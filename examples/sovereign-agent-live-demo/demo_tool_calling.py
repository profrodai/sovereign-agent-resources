"""LIVE demo: a chosen real model does real tool-calling on a
tool BUILT WITH ZEOCORE, and the Sovereign Agent governs the result.

Nothing here is scripted. The model decides to call the tool, the tool reads the
real governed SQLite ledger, and the Sovereign Agent RE-VALIDATES the model's
proposal against reality before it would ever be committed.

Run:  python demo_tool_calling.py --provider ollama|openai|anthropic
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

from pydantic import BaseModel

# --- Sovereign Agent (the governance framework, installed as a package) -------
from sovereign_agent.database import Database
from reference_organizations.store import (
    CatalogEntry,
    Product,
    RestockProposal,
    record_sale,
    seed_catalog,
    validate_restock,
)
from sovereign_agent.errors import Refusal

# --- ZeoCore (the framework the TOOL is built with) ---------------------------
from zeo_core.tools import ToolContext, bound_capability_of, capability
from zeo_core.tools.invoke import invoke_sync
from zeo_core.contracts import CapabilityResult
from zeo_core.contracts.common.enums import EffectKind
from zeo_core.contracts.capabilities.metadata import CapabilityExample

from model_provider import ProviderConfig, chat, parse_provider_argument


# =============================================================================
# THE TOOL — a real ZeoCore capability. Typed request/response, declared READ
# effect, an example. qwen will be handed its JSON schema and may call it.
# =============================================================================
class InspectInventoryRequest(BaseModel):
    sku: str


class InspectInventoryResponse(BaseModel):
    sku: str
    on_hand: int
    reorder_point: int


@capability(
    id="store.inspect_inventory@1.0.0",
    description="Read the CURRENT on_hand and reorder_point for an ice cream SKU from the governed ledger. Call this before proposing any restock; never guess stock levels.",
    effects={EffectKind.READ},
    examples=(
        CapabilityExample(
            request={"sku": "SKU-VANILLA"},
            response={"sku": "SKU-VANILLA", "on_hand": 2, "reorder_point": 3},
        ),
    ),
)
def inspect_inventory(
    request: InspectInventoryRequest, ctx: ToolContext
) -> CapabilityResult[InspectInventoryResponse]:
    db_path = ctx.metadata["db_path"]
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT on_hand, reorder_point FROM inventory WHERE sku = ?", (request.sku,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return CapabilityResult.fail(msg=f"unknown sku {request.sku}", code="NO_SKU")
    return CapabilityResult.ok(
        data=InspectInventoryResponse(
            sku=request.sku, on_hand=int(row["on_hand"]), reorder_point=int(row["reorder_point"])
        )
    )


CAP = bound_capability_of(inspect_inventory)


def run_actor(db_path: Path, config: ProviderConfig) -> tuple[int, list[str]]:
    """The chosen model decides a restock quantity via tool calling."""
    ctx = ToolContext(
        run_id="live-demo",
        tool_name="inspect_inventory",
        tool_version="1.0.0",
        logger=logging.getLogger("live-demo"),
        fs=None,
        work_dir=str(db_path.parent),
        output_dir=str(db_path.parent),
        metadata={"db_path": str(db_path)},
    )
    tool_schema = {
        "type": "function",
        "function": {
            "name": "inspect_inventory",
            "description": CAP.definition.description,
            "parameters": CAP.request_model.model_json_schema(),
        },
    }
    messages = [
        {
            "role": "system",
            "content": (
                "You are a Sovereign Agent ice cream shop operator actor. You do NOT get to "
                "commit anything; you PROPOSE. You MUST call inspect_inventory to learn "
                "real stock before proposing. Goal: keep the SKU at or ABOVE its reorder "
                "point. When ready, reply with exactly one line: RESTOCK_UNITS: <integer>."
            ),
        },
        {"role": "user", "content": "Keep SKU-VANILLA stocked at or above its reorder point. How many units should we order?"},
    ]
    transcript: list[str] = []
    for _turn in range(6):
        msg = chat(config, messages, [tool_schema])
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if calls:
            for call in calls:
                fn = call["function"]
                args = fn["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)
                result = invoke_sync(CAP, InspectInventoryRequest(**args), ctx)
                # CapabilityResult.ok is a CONSTRUCTOR, not a bool — key on data.
                # (And CapabilityResult has no .msg attribute, so don't touch it.)
                payload = (
                    result.data.model_dump()
                    if result.data is not None
                    else {"error": f"unknown sku {args.get('sku')!r}; the only valid sku is SKU-VANILLA"}
                )
                transcript.append(
                    f"{config.model} CALLED zeocore tool inspect_inventory({args}) -> {payload}"
                )
                messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(payload),
                        "tool_name": fn["name"],
                        "tool_call_id": call.get("id") or fn["name"],
                    }
                )
            continue
        content = msg.get("content") or ""
        transcript.append(f"{config.model} SAID: {content.strip()[:300]}")
        m = re.search(r"RESTOCK_UNITS:\s*(\d+)", content)
        if m:
            return int(m.group(1)), transcript
        m2 = re.search(r"\b(\d{1,3})\b", content)
        if m2:
            return int(m2.group(1)), transcript
        messages.append({"role": "user", "content": "Reply with exactly: RESTOCK_UNITS: <integer>."})
    raise RuntimeError(f"{config.model} never produced a RESTOCK_UNITS proposal")


def main() -> int:
    config = parse_provider_argument(__doc__ or "Live governed tool-calling demo")
    root = Path(tempfile.mkdtemp(prefix="sovereign-live-"))
    db = Database(root / ".sovereign" / "organization.db")
    db_path = root / ".sovereign" / "organization.db"

    print("=" * 74)
    print(f"SOVEREIGN AGENT — LIVE tool-calling via {config.name} ({config.model})")
    print("=" * 74)
    # Lucy's ice cream shop. seed_catalog needs >= 2 SKUs, each independent.
    seed_catalog(db, (
        CatalogEntry(product=Product(sku="SKU-VANILLA", name="Vanilla ice cream",
                                     unit_cost_cents=250, price_cents=500),
                     on_hand=4, reorder_point=3),
        CatalogEntry(product=Product(sku="SKU-CHOCOLATE", name="Chocolate ice cream",
                                     unit_cost_cents=260, price_cents=520),
                     on_hand=10, reorder_point=6),
    ))
    sig = record_sale(db, "SKU-VANILLA", 2, 500)  # a real sale drops on_hand to 2 (below 3)
    before = db.connection.execute(
        "SELECT on_hand, reorder_point FROM inventory WHERE sku='SKU-VANILLA'"
    ).fetchone()
    print(f"\n1) A customer bought 2 tubs of vanilla ice cream. Ledger now: on_hand={before['on_hand']}, "
          f"reorder_point={before['reorder_point']} (below reorder). signal={sig.id}")

    print(f"\n2) Handing the assignment to a REAL actor: {config.model} via {config.name}.")
    print(f"   Inference runs at {config.location}; the model still receives no authority.")
    print("   It is given ONE tool, built with ZeoCore: inspect_inventory. Watch it call it.\n")
    units, transcript = run_actor(db_path, config)
    for line in transcript:
        print("   " + line)
    print(f"\n3) The actor PROPOSED: restock {units} units of SKU-VANILLA.")

    print("\n4) The Sovereign Agent does NOT trust the model. It re-validates the proposal")
    print("   against the ledger and reads the TRUE unit cost from the product record:")
    proposal = RestockProposal(sku="SKU-VANILLA", quantity=units)
    try:
        unit_cost, total = validate_restock(db, proposal)
        print(f"   VALID: {units} units x {unit_cost}c (cost read from the ledger, not from the model) "
              f"= {total}c. This proposal is governable.")
    except Refusal as exc:
        print(f"   REFUSED by governance: {exc}")
        return 1

    print("\n5) Governance proof — the model's number is not authority. Try an absurd proposal:")
    try:
        validate_restock(db, RestockProposal(sku="SKU-VANILLA", quantity=9999))
        print("   (unexpected) 9999 units was allowed")
    except Refusal as exc:
        print(f"   REFUSED: {str(exc).splitlines()[0]}")
    print("\nDONE — a real LLM did real tool-calling on a ZeoCore-built tool, and the")
    print("Sovereign Agent governed the result. Not scripted. Live.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

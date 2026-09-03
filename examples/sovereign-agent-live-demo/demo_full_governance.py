"""FULL end-to-end LIVE governed run with Ollama, OpenAI, or Anthropic.

The resource-local adapter changes only the intelligence transport. A real model
PROPOSES a restock, and
the Sovereign Agent validates, COMMITS atomically, verifies, and accepts -- the
whole governed loop. Not scripted.

Run:  python demo_full_governance.py --provider ollama|openai|anthropic
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from sovereign_agent.models import Role
from sovereign_agent.organization import Organization
from sovereign_agent.providers import PROVIDERS
from sovereign_agent.providers.base import (
    InvocationRequest,
    InvocationSpec,
    ProviderCapabilities,
    parse_json_line,
)
from reference_organizations.store import (
    CatalogEntry,
    Product,
    RestockProposal,
    apply_restock,
    below_reorder,
    record_sale,
    seed_catalog,
)
from model_provider import ProviderConfig, parse_provider_argument

SKU = "SKU-VANILLA"

# Lucy's ice cream shop. seed_catalog needs >= 2 SKUs, each with its own
# independent stock level and reorder point (one shared till).
ICE_CREAM = (
    CatalogEntry(
        product=Product(sku="SKU-VANILLA", name="Vanilla ice cream",
                        unit_cost_cents=250, price_cents=500),
        on_hand=4, reorder_point=3,
    ),
    CatalogEntry(
        product=Product(sku="SKU-CHOCOLATE", name="Chocolate ice cream",
                        unit_cost_cents=260, price_cents=520),
        on_hand=10, reorder_point=6,
    ),
)


class DemoModelProvider:
    """Bind Sovereign Agent to this resource's provider-neutral worker."""

    name = "demo-model"
    executable = "python"
    requires_terminal_event = False

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.name = f"demo-{config.name}"

    def probe(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            available=True,
            version=f"{self.config.name}:{self.config.model}",
            print_mode=True,
            streaming=True,
            structured_result=True,
            workspace_write=True,
        )

    def build_invocation(self, request: InvocationRequest) -> InvocationSpec:
        environment = {
            "SOVEREIGN_DEMO_PROVIDER": self.config.name,
            f"{self.config.name.upper()}_MODEL": self.config.model,
            f"{self.config.name.upper()}_URL": self.config.url,
        }
        if self.config.api_key:
            environment[f"{self.config.name.upper()}_API_KEY"] = self.config.api_key
        return InvocationSpec(
            argv=[
                "python",
                str(Path(__file__).with_name("demo_provider_worker.py").resolve()),
                str(request.output),
                request.prompt,
            ],
            cwd=request.workspace,
            env=environment,
        )

    def parse_event(self, line: str):
        return parse_json_line(line)


def main() -> int:
    config = parse_provider_argument(__doc__ or "Full governed model demo")
    provider = DemoModelProvider(config)
    PROVIDERS[provider.name] = provider

    root = Path(tempfile.mkdtemp(prefix="sovereign-full-"))
    print("=" * 74)
    print(f"SOVEREIGN AGENT — FULL governed run via {config.name}, model = {config.model}")
    print("=" * 74)

    org = Organization.init(root)
    seed_catalog(org.db, ICE_CREAM)
    outcome = org.create_outcome(
        title="Keep the vanilla tub stocked",
        desired_state="On-hand vanilla is at or above the reorder point, the purchase is reconciled, and the replenishment is on the ledger.",
        checks=["inventory_at_or_above_reorder_point", "cash_reconciles", "replenishment_event_exists"],
        owner="principal-human",
        subject=SKU,
    )
    org.activate(outcome.id, "master-course")
    signal = record_sale(org.db, SKU, 2, 500)
    assert below_reorder(org.db), "sale should cross the reorder point"
    before = org.db.connection.execute(
        "SELECT on_hand, reorder_point FROM inventory WHERE sku=?", (SKU,)
    ).fetchone()
    on_hand, reorder = before["on_hand"], before["reorder_point"]
    print(f"\n1) Sale committed. Ledger: on_hand={on_hand}, reorder_point={reorder} (below). signal={signal.id}")

    # The built-in provider is generic: it proposes from the assignment's scope,
    # so the SOW states the real numbers the model needs to decide.
    scope = (
        f"Replenish {SKU}. Current on_hand is {on_hand}; reorder_point is {reorder}. "
        f"Propose the integer number of units to restock so on_hand reaches at least the reorder point."
    )
    sow = org.create_sow(outcome.id, scope=scope, role=Role.OPERATOR,
                         actor_id="master-course", required_effect_kind="replenishment")
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")

    # Bind the actor to the resource's provider-neutral adapter, then run the
    # unchanged governed path.
    org.rebind_actor("operator-course", provider.name, "principal-human")
    print(f"\n2) Actor operator-course bound to {config.name}. Running the assignment —")
    print(f"   {config.model} reads the scope and proposes a governed ActorReport...\n")
    assignment = org.run_assignment(assignment.id)

    report_path = root / ".sovereign" / "runs" / assignment.workspace_id / ".sovereign-out" / "report.json"
    report = json.loads(report_path.read_text())
    proposed = report["proposed_restock_units"]
    print(f"3) The model's governed ActorReport: status={report['status']}, proposed={proposed} units.")
    if not proposed:
        print("   (The model did not propose a positive quantity this run — re-run, or use the")
        print("    retry, or choose another model in .env.)")
        return 1

    proposal = RestockProposal(sku=SKU, quantity=proposed)
    apply_restock(org.db, proposal, assignment.id, signal.id)  # validate + commit atomically
    org.verify_outcome(outcome.id, "verifier-course")
    org.review(sow.id, "sparring-course")
    org.accept(outcome.id, "principal-human")

    after = org.db.connection.execute(
        "SELECT on_hand, reorder_point FROM inventory WHERE sku=?", (SKU,)
    ).fetchone()
    cash = org.db.connection.execute(
        "SELECT id, amount_cents FROM cash_entries ORDER BY rowid"
    ).fetchall()
    print("\n4) COMMITTED + VERIFIED + ACCEPTED.")
    print(f"   inventory now: on_hand={after['on_hand']} (>= reorder {after['reorder_point']}) — tub genuinely full")
    print(f"   cash ledger: {[(c['id'].split('_')[0], c['amount_cents']) for c in cash]}")
    print(f"\n   status: {org.status_text(outcome.id).splitlines()[0]}")
    print(f"\nDONE — a real model, via {config.name},")
    print("proposed work that flowed through the FULL governance loop to an accepted outcome.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

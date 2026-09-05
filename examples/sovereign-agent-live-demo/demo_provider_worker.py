"""Resource-local Sovereign Agent provider worker for the three model choices."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from sovereign_agent.models import ActorReport

from model_provider import ProviderRequestError, chat, resolve_config

SYSTEM_PROMPT = (
    "You are a Sovereign Agent operator actor. You only PROPOSE work; you never commit or "
    "accept it. Reply with ONLY one JSON object, no prose or code fences, containing: "
    '{"status":"completed"|"blocked"|"failed","proposed_restock_units":integer|null,'
    '"proposed_checks":[string],"notes":"short string"}.'
)


def _json_object(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("model reply contained no JSON object")
    value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("model reply was not an object")
    return value


def run(output: Path, envelope_text: str) -> ActorReport:
    output.mkdir(parents=True, exist_ok=True)
    # The parent passes only the selected provider's allowlisted variables.
    # Do not reopen the resource's .env from inside the actor subprocess.
    config = resolve_config(load_file=False)
    try:
        envelope = json.loads(envelope_text)
        scope = str(envelope["statement_of_work"]["scope"])
        message = chat(
            config,
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Assignment scope:\n{scope}\n\nJSON object only."},
            ],
        )
        parsed = _json_object(str(message.get("content") or ""))
        raw_units = parsed.get("proposed_restock_units")
        units = int(raw_units) if not isinstance(raw_units, bool) and raw_units is not None else None
        checks = parsed.get("proposed_checks")
        report = ActorReport(
            status=parsed.get("status") if parsed.get("status") in {"completed", "blocked", "failed"} else "completed",
            proposed_restock_units=units,
            changed_artifacts=["inventory.md"],
            proposed_checks=[str(item) for item in checks] if isinstance(checks, list) else [],
            questions=[],
            notes=str(parsed.get("notes") or f"proposed by {config.model}")[:500],
        )
    except (ProviderRequestError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        report = ActorReport(
            status="failed",
            proposed_restock_units=None,
            notes=f"{config.name} provider failed safely: {error}"[:500],
        )
    (output / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    (output / "artifacts.json").write_text(
        '{"inventory.md":"replenishment proposed"}', encoding="utf-8"
    )
    return report


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: demo_provider_worker.py OUTPUT ASSIGNMENT_JSON")
    run(Path(sys.argv[1]), sys.argv[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

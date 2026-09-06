"""Run the successful handoff and both required refusal controls."""

from pathlib import Path
from tempfile import TemporaryDirectory

from handoff import HandoffRefusal, execute_handoff


def _run_refusal(name: str, **kwargs: object) -> None:
    with TemporaryDirectory(prefix=f"zeocreator-{name}-") as temporary:
        try:
            execute_handoff(Path(temporary), **kwargs)
        except HandoffRefusal as refusal:
            print(f"{name}: REFUSED ({refusal.category})")
            return
    raise RuntimeError(f"{name} did not refuse")


def main() -> None:
    with TemporaryDirectory(prefix="zeocreator-happy-") as temporary:
        summary = execute_handoff(Path(temporary))
    sovereign = summary["sovereign_agent"]
    creator = summary["zeo_creator"]
    print("=== governed handoff ===")
    print(f"outcome: {sovereign['outcome_state']}")
    print(f"sow: {sovereign['sow_state']}")
    print(f"assignment: {sovereign['assignment_state']}")
    print(f"origin: {sovereign['origin']}")
    print(f"assignment binding: {creator['assignment_binding']}")
    print(f"delivery ready: {creator['delivery_ready']}")
    print(f"proposed operations: {creator['proposed_operations']}")
    print(f"executed operations: {creator['executed_operations']}")
    print(f"sovereign acceptance recorded: {sovereign['acceptance_recorded']}")
    print("=== refusal controls ===")
    _run_refusal("identity mismatch", creator_assignment_override="assignment_wrong")
    _run_refusal("byte tamper", tamper_after_manifest=True)


if __name__ == "__main__":
    main()

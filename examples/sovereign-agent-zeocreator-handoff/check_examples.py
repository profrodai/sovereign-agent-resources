"""Behavioral smoke test for the successful bridge and its dual controls."""

from pathlib import Path
from tempfile import TemporaryDirectory

from src.handoff import HandoffRefusal, execute_handoff


def _expect_refusal(category: str, **kwargs: object) -> None:
    with TemporaryDirectory(prefix=f"zeocreator-check-{category}-") as temporary:
        try:
            execute_handoff(Path(temporary), **kwargs)
        except HandoffRefusal as refusal:
            assert refusal.category == category, refusal
            print(f"PASS refusal: {category}")
            return
    raise AssertionError(f"expected refusal: {category}")


def main() -> None:
    with TemporaryDirectory(prefix="zeocreator-check-happy-") as temporary:
        summary = execute_handoff(Path(temporary))
    sovereign = summary["sovereign_agent"]
    creator = summary["zeo_creator"]
    assert sovereign["outcome_state"] == "ACTIVE"
    assert sovereign["sow_state"] == "ASSIGNED"
    assert sovereign["assignment_state"] == "CREATED"
    assert sovereign["origin"] == "manual"
    assert sovereign["acceptance_recorded"] is False
    assert creator["assignment_binding"] == "MATCH"
    assert creator["assignment_id"] == sovereign["assignment_id"]
    assert creator["delivery_ready"] is True
    assert creator["proposed_operations"] == 1
    assert creator["executed_operations"] == 0
    assert str(summary["handoff_digest"]).startswith("sha256:")
    print("PASS governed handoff: assignment-bound brief and one write-free proposal")

    _expect_refusal(
        "assignment_identity_mismatch",
        creator_assignment_override="assignment_wrong",
    )
    _expect_refusal("artifact_bytes_changed", tamper_after_manifest=True)


if __name__ == "__main__":
    main()

"""Persist condition state without inventing a run, then fire one due slot."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from sovereign_agent.automation import WatchDecision, create_automation, run_due
from sovereign_agent.organization import Organization


def main() -> None:
    now = datetime(2026, 9, 5, tzinfo=UTC)
    with TemporaryDirectory() as scratch:
        org = Organization.init(Path(scratch))
        create_automation(
            org.db,
            "low-stock",
            interval_seconds=60,
            payload="order vanilla",
            first_run_at=now,
        )
        first = run_due(
            org.db,
            "low-stock",
            lambda state: WatchDecision(
                False, "healthy", {"checks": state.get("checks", 0) + 1}
            ),
            lambda _run_id, _message: None,
            now=now,
        )
        run_count = org.db.connection.execute(
            "SELECT COUNT(*) FROM automation_runs"
        ).fetchone()[0]
        state = org.db.connection.execute(
            "SELECT condition_state FROM automations WHERE id = 'low-stock'"
        ).fetchone()[0]
        assert first.status == "NO_FIRE" and run_count == 0 and state == '{"checks":1}'
        print(f"first check: {first.status}, runs={run_count}, state={state}")

        payload_calls: list[str] = []
        second = run_due(
            org.db,
            "low-stock",
            lambda _state: WatchDecision(True, "order vanilla", {"ordered": True}),
            lambda _run_id, message: payload_calls.append(message),
            now=now + timedelta(seconds=60),
        )
        run_count = org.db.connection.execute(
            "SELECT COUNT(*) FROM automation_runs"
        ).fetchone()[0]
        assert second.status == "SUCCEEDED" and run_count == 1
        assert payload_calls == ["order vanilla"]
        print(
            f"second check: {second.status}, runs={run_count}, payload={payload_calls[0]}"
        )
        org.db.close()


if __name__ == "__main__":
    main()

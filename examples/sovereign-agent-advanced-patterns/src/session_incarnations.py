"""Let a new host take over an expired session and fence the stale worker."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from sovereign_agent.coordination import (
    claim_session,
    finish_session,
    record_delivery_failure,
    register_host,
)
from sovereign_agent.errors import Refusal
from sovereign_agent.organization import Organization


def main() -> None:
    now = datetime(2026, 9, 5, tzinfo=UTC)
    takeover_at = now + timedelta(seconds=20)
    with TemporaryDirectory() as scratch:
        org = Organization.init(Path(scratch))
        register_host(org.db, "host-a", now=now, ttl_seconds=10)
        first = claim_session(org.db, "shop-session", "host-a", now=now, ttl_seconds=10)
        register_host(org.db, "host-b", now=takeover_at, ttl_seconds=60)
        second = claim_session(
            org.db, "shop-session", "host-b", now=takeover_at, ttl_seconds=60
        )
        assert (first.incarnation, second.incarnation) == (1, 2)
        print(f"incarnation: {first.incarnation} -> {second.incarnation}")
        stale_refused = False
        try:
            finish_session(org.db, first, "stale result", now=takeover_at)
        except Refusal:
            stale_refused = True
            print("stale completion: REFUSED")
        assert stale_refused
        finish_session(org.db, second, "current result", now=takeover_at)
        completions = org.db.connection.execute(
            "SELECT COUNT(*) FROM session_completions"
        ).fetchone()[0]
        attempts = record_delivery_failure(org.db, "delivery-1", "offline", takeover_at)
        attempts = record_delivery_failure(
            org.db, "delivery-1", "still offline", takeover_at
        )
        assert completions == 1 and attempts == 2
        print(f"durable completions: {completions}")
        print(f"delivery attempts: {attempts}")
        org.db.close()


if __name__ == "__main__":
    main()

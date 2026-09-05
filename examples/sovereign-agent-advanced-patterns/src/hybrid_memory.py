"""Filter memory access before ranking and expose score provenance."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from sovereign_agent.memory import recall, remember
from sovereign_agent.organization import Organization


def main() -> None:
    now = datetime(2026, 9, 5, tzinfo=UTC)
    with TemporaryDirectory() as scratch:
        org = Organization.init(Path(scratch))
        remember(
            org.db,
            "public-rule",
            "Vanilla reorder point is six",
            importance=0.8,
            embedding=(1.0, 0.0),
            created_at=now - timedelta(days=1),
        )
        remember(
            org.db,
            "public-supplier",
            "Vanilla supplier lead time is two days",
            importance=0.6,
            embedding=(0.8, 0.2),
            created_at=now - timedelta(days=2),
        )
        remember(
            org.db,
            "private-other",
            "Vanilla emergency override",
            visibility="actor:other",
            importance=1.0,
            embedding=(1.0, 0.0),
            created_at=now,
        )
        hits = recall(
            org.db,
            "vanilla reorder",
            actor_id="lucy",
            query_embedding=(1.0, 0.0),
            limit=2,
            now=now,
        )
        assert [hit.id for hit in hits] == ["public-rule", "public-supplier"]
        assert all(hit.id != "private-other" for hit in hits)
        print(f"visible ids: {','.join(hit.id for hit in hits)}")
        print(
            f"private-other visible: {any(hit.id == 'private-other' for hit in hits)}"
        )
        first = hits[0]
        assert first.semantic_status == "used"
        assert first.semantic > 0 and first.lexical > 0
        print(
            "top score provenance: "
            f"lexical={first.lexical:.3f}, semantic={first.semantic:.3f}, "
            f"recency={first.recency:.3f}, importance={first.importance:.3f}"
        )
        print(f"semantic status: {first.semantic_status}")
        org.db.close()


if __name__ == "__main__":
    main()

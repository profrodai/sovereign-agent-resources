"""Compact a rendered view while preserving every source transcript row."""

from pathlib import Path
from tempfile import TemporaryDirectory

from sovereign_agent.context import append_message, compact_one, render_context
from sovereign_agent.organization import Organization


def main() -> None:
    with TemporaryDirectory() as scratch:
        org = Organization.init(Path(scratch))
        messages = (
            ("system", "Keep the shop governed."),
            ("user", "Check vanilla stock."),
            ("assistant", "I inspected the catalog."),
            ("tool", "Vanilla has eight tubs."),
            ("user", "Keep this correction verbatim."),
            ("assistant", "The recent answer stays visible."),
            ("tool", "Recent tool result."),
        )
        for role, content in messages:
            append_message(org.db, "lesson", role, content)
        before = org.db.connection.execute(
            "SELECT COUNT(*) FROM transcript_messages"
        ).fetchone()[0]
        changed = compact_one(
            org.db,
            "lesson",
            lambda _prior, exchange: f"Summarized {len(exchange)} derived messages.",
        )
        after = org.db.connection.execute(
            "SELECT COUNT(*) FROM transcript_messages"
        ).fetchone()[0]
        rendered = render_context(org.db, "lesson")
        users = sum(item.role == "user" for item in rendered)
        summaries = sum(item.derived for item in rendered)
        assert changed and before == after == 7
        assert len(rendered) == 6 and summaries == 1 and users == 2
        print(f"compaction appended: {changed}")
        print(f"source rows: {before} -> {after}")
        print(
            f"rendered: {len(rendered)}, summaries={summaries}, user messages={users}"
        )
        org.db.close()


if __name__ == "__main__":
    main()

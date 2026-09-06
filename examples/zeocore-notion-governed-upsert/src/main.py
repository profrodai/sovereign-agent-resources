"""Prove the governed Notion upsert request contract without dispatching it."""

from __future__ import annotations

import hashlib

from pydantic import ValidationError
from zeo_core.integrations.notion import (
    CitedText,
    NotionPageUpsertRequest,
    notion_page_upsert_revision,
)

SOURCE = b"Weekly review: the cohort completed the local-first lab."
DESTINATION = "87654321-4321-4321-8321-cba987654321"
ALTERNATE_DESTINATION = "12345678-1234-4234-9234-123456789abc"


def build_request() -> NotionPageUpsertRequest:
    """Build the exact admitted request from cited, content-addressed input."""
    source_digest = hashlib.sha256(SOURCE).hexdigest()
    return NotionPageUpsertRequest(
        meeting_id="meeting-weekly-review",
        meeting_artifact_sha256=source_digest,
        interpretation_id="interpretation-weekly-review",
        interpretation_sha256="b" * 64,
        destination_parent_id=DESTINATION,
        title="Weekly course review",
        summary=CitedText(
            text="The cohort completed the local-first lab.",
            source_citations=("transcript:12-18",),
        ),
        decisions=(
            CitedText(
                text="Keep the next lab local-first.",
                source_citations=("transcript:31-34",),
            ),
        ),
        idempotency_marker=NotionPageUpsertRequest.marker_for(
            meeting_artifact_sha256=source_digest,
            destination_parent_id=DESTINATION,
        ),
    )


def main() -> int:
    """Assert and print only contract facts established in this process."""
    request = build_request()
    revision = notion_page_upsert_revision()
    expected_marker = NotionPageUpsertRequest.marker_for(
        meeting_artifact_sha256=request.meeting_artifact_sha256,
        destination_parent_id=DESTINATION,
    )
    alternate_marker = NotionPageUpsertRequest.marker_for(
        meeting_artifact_sha256=request.meeting_artifact_sha256,
        destination_parent_id=ALTERNATE_DESTINATION,
    )

    try:
        NotionPageUpsertRequest.model_validate(
            {**request.model_dump(), "unexpected": "not admitted"}
        )
    except ValidationError:
        extra_field_rejected = True
    else:
        extra_field_rejected = False

    facts = {
        "operation": str(revision.operations[0].operation_id),
        "revision": str(revision.revision_id),
        "marker_bound": request.idempotency_marker == expected_marker,
        "summary_cited": "transcript:12-18" in request.canonical_markdown(),
        "decision_cited": "transcript:31-34" in request.canonical_markdown(),
        "destination_changes_marker": alternate_marker != expected_marker,
        "extra_field_rejected": extra_field_rejected,
        "provider_calls": 0,
    }

    assert facts == {
        "operation": "notion.page.upsert",
        "revision": "notion.page-upsert@1",
        "marker_bound": True,
        "summary_cited": True,
        "decision_cited": True,
        "destination_changes_marker": True,
        "extra_field_rejected": True,
        "provider_calls": 0,
    }

    for name, value in facts.items():
        print(f"{name}={value}")
    print("mode=SIMULATED_CONTRACT_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

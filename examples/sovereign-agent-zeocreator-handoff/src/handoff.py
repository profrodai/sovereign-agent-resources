"""Application-owned bridge from Sovereign Agent work to ZEO Creator contracts.

This module deliberately stops before publication and before Sovereign Agent
acceptance. Sovereign Agent 1.4 has no public generic external-capability receipt
import; pretending otherwise would turn a useful handoff example into a hollow
end-to-end claim.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sovereign_agent import Organization
from sovereign_agent.models import Role
from zeo_core.tools import invoke_sync
from zeo_creator.capabilities.create_content_brief import (
    CreateContentBriefRequest,
    CreateContentBriefResponse,
)
from zeo_creator.capabilities.prepare_distribution import (
    PrepareDistributionRequest,
    PrepareDistributionResponse,
)
from zeo_creator.capabilities.validate_delivery import (
    ValidateDeliveryRequest,
    ValidateDeliveryResponse,
)
from zeo_creator.contracts.delivery import (
    ArtifactAttestation,
    ArtifactDescriptor,
    ArtifactDigestProof,
    ArtifactManifest,
)
from zeo_creator.contracts.distribution import (
    ChannelDestination,
    ChannelPlan,
    DistributionVariant,
)
from zeo_creator.contracts.editorial import EditorialAssignment
from zeo_creator.contracts.evidence import EvidenceClaim, ResearchSynthesis, ResearchWindow
from zeo_creator.contracts.production import (
    AttestationPolicy,
    AttestationRequirement,
    ContentDocument,
)
from zeo_creator.contracts.publications import PublicationProfile
from zeo_creator.registry import capability_registry
from zeo_creator.runtime import make_context

NOW = datetime(2026, 9, 6, 9, tzinfo=UTC)
WINDOW = ResearchWindow(starts_at=NOW - timedelta(days=1), ends_at=NOW)
ORGANIZATION_ID = "org_sovereign_agent_example"
PUBLICATION_ID = "publication.learning.example"
ARTIFACT_REF = "artifact_governed_handoff"
ARTIFACT_STORAGE_REF = "artifact://local/governed-handoff.html"
REQUIREMENTS = (
    AttestationRequirement(
        check_id="artifact.readable",
        check_version="1.0.0",
        policy=AttestationPolicy.REQUIRED,
    ),
    AttestationRequirement(
        check_id="content.claims-traceable",
        check_version="1.0.0",
        policy=AttestationPolicy.REQUIRED,
    ),
)


class HandoffRefusal(RuntimeError):
    """A named application-boundary refusal."""

    def __init__(self, category: str, message: str) -> None:
        self.category = category
        super().__init__(f"{category}: {message}")


def _sha256(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _publication() -> PublicationProfile:
    return PublicationProfile(
        profile_id="profile_learning_publication",
        created_at=NOW,
        organization_id=ORGANIZATION_ID,
        publication_id=PUBLICATION_ID,
        display_name="Learning Publication",
        audience_definition="Builders learning governed creator operations",
        editorial_pillars=("evidence", "governance"),
        voice_rules=("Be concrete", "State proof boundaries"),
        style_ref="style_learning@1",
        participant_refs=("principal.example",),
        default_channels=("website",),
        prohibited_topics=("unverified rumours",),
        prohibited_claims=("publication was executed",),
        cta_policy="Invite the reader to reproduce the refusal controls.",
        approval_policy_ref="approval_operator@1",
    )


def _synthesis() -> ResearchSynthesis:
    claim = EvidenceClaim(
        claim_id="claim_assignment_identity",
        text="A creator handoff must preserve its governed assignment identity.",
        evidence_refs=("evidence_sovereign_assignment",),
    )
    return ResearchSynthesis(
        synthesis_id="synthesis_governed_handoff",
        created_at=NOW,
        organization_id=ORGANIZATION_ID,
        publication_id=PUBLICATION_ID,
        research_window=WINDOW,
        themes=("governed handoffs",),
        opportunities=("make the assignment boundary executable",),
        candidate_claims=(claim,),
        evidence_refs=claim.evidence_refs,
    )


def _governed_assignment(root: Path) -> tuple[Organization, Any, Any, Any]:
    organization = Organization.init(root / "sovereign-organization")
    outcome = organization.create_outcome(
        title="Explain the Sovereign Agent to ZEO Creator handoff",
        desired_state="One evidence-bound brief is ready for a human approval decision.",
        checks=[],
        owner="principal-human",
        subject="governed-creator-handoff",
    )
    outcome = organization.activate(outcome.id, "master-course")
    sow = organization.create_sow(
        outcome.id,
        (
            "Create one evidence-grounded article brief whose creator assignment "
            "is bound to this exact Sovereign Agent assignment. Prepare publication "
            "proposals but execute none."
        ),
        Role.OPERATOR,
        "master-course",
    )
    organization.ready_sow(sow.id)
    assignment = organization.assign(sow.id, "operator-course", "master-course")
    return organization, outcome, sow, assignment


def _creator_assignment(
    *, sovereign_assignment_id: str, scope: str, publication: PublicationProfile
) -> EditorialAssignment:
    return EditorialAssignment(
        assignment_id=sovereign_assignment_id,
        created_at=NOW,
        organization_id=publication.organization_id,
        publication_id=publication.publication_id,
        content_kind="article",
        objective=scope,
        audience=publication.audience_definition,
        desired_audience_action="Run the example and inspect both refusal paths.",
        topic="Sovereign Agent and ZEO Creator",
        thesis="A safe integration preserves assignment identity and artifact bytes.",
        hook="The handoff is a contract, not an import statement",
        evidence_refs=("evidence_sovereign_assignment",),
        novelty_rationale="The bridge makes the missing generic receipt seam explicit.",
        relationship_to_other_assignments="A standalone integration lesson.",
        target_channels=publication.default_channels,
        brand_profile_ref=publication.reference,
        due_at=NOW + timedelta(hours=8),
    )


def _require_assignment_binding(
    *, sovereign_assignment_id: str, creator_assignment: EditorialAssignment
) -> None:
    if creator_assignment.assignment_id != sovereign_assignment_id:
        raise HandoffRefusal(
            "assignment_identity_mismatch",
            "the ZEO Creator assignment does not name the governed Sovereign Agent assignment",
        )


def _invoke_content_brief(
    *, assignment: EditorialAssignment, publication: PublicationProfile, scope: str
) -> tuple[Any, ResearchSynthesis]:
    synthesis = _synthesis()
    capability = capability_registry().get("creator.create_content_brief@1.0.0")
    result = invoke_sync(
        capability,
        CreateContentBriefRequest(
            assignment=assignment,
            publication=publication,
            synthesis=synthesis,
            creative_direction=(
                "Turn the bounded SOW into a concise tutorial. Preserve the evidence claim, "
                "name the approval boundary, and never imply that a proposal was published. "
                f"Governing scope: {scope}"
            ),
            delivery_requirements=REQUIREMENTS,
            created_at=NOW,
        ),
        make_context(capability_name="create_content_brief"),
    )
    if not isinstance(result.data, CreateContentBriefResponse):
        raise HandoffRefusal("brief_creation_failed", result.human_message)
    return result.data.brief, synthesis


def _produce_manifest(root: Path, brief: Any) -> tuple[Path, ArtifactManifest]:
    artifact = root / "producer-output" / "governed-handoff.html"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        "<article><h1>The handoff is a contract</h1>"
        "<p>A creator handoff must preserve its governed assignment identity.</p>"
        "<p>This is a proposal candidate, not a publication receipt.</p></article>"
    ).encode()
    artifact.write_bytes(payload)
    digest = _sha256(payload)
    descriptor = ArtifactDescriptor(
        artifact_ref=ARTIFACT_REF,
        role="primary",
        media_type="text/html",
        byte_length=len(payload),
        digest=digest,
        storage_ref=ARTIFACT_STORAGE_REF,
    )
    proof = ArtifactDigestProof(
        artifact_ref=ARTIFACT_REF,
        algorithm="sha256",
        digest=digest,
        byte_length=len(payload),
        storage_ref=ARTIFACT_STORAGE_REF,
        retrieved_at=NOW,
        evidence_ref="evidence://local-byte-read",
        tool_identity="sovereign-agent-zeocreator-handoff",
        tool_version="1.0.0",
    )
    attestations = tuple(
        ArtifactAttestation(
            check_id=requirement.check_id,
            check_version=requirement.check_version or "1.0.0",
            result=True,
            artifact_refs=(ARTIFACT_REF,),
            evidence_ref=f"evidence://{requirement.check_id}",
            tool_identity="sovereign-agent-zeocreator-handoff",
            observed_value="verified against deterministic local bytes",
            expected_constraint="declared by the creator brief",
        )
        for requirement in REQUIREMENTS
    )
    manifest = ArtifactManifest(
        manifest_id="manifest_governed_handoff",
        created_at=NOW,
        organization_id=brief.organization_id,
        publication_id=brief.publication_id,
        input_refs=(brief.brief_id, brief.content_digest),
        brief_id=brief.brief_id,
        content_revision=brief.content_revision,
        brief_content_digest=brief.content_digest,
        producer_ref="example.local-deterministic-producer",
        producer_version="1.0.0",
        brand_profile_ref=brief.brand_profile_ref,
        artifacts=(descriptor,),
        digest_proofs=(proof,),
        attestations=attestations,
        produced_claim_ids=tuple(claim.claim_id for claim in brief.evidence_claims),
        extracted_text=payload.decode(),
    )
    return artifact, manifest


def _require_current_bytes(artifact: Path, manifest: ArtifactManifest) -> None:
    payload = artifact.read_bytes()
    descriptor = manifest.artifacts[0]
    if len(payload) != descriptor.byte_length or _sha256(payload) != descriptor.digest:
        raise HandoffRefusal(
            "artifact_bytes_changed",
            "the producer bytes no longer match the manifest presented for review",
        )


def _channel_plan(brief: Any) -> ChannelPlan:
    return ChannelPlan(
        channel_plan_id="channels_governed_handoff",
        created_at=NOW,
        organization_id=brief.organization_id,
        publication_id=brief.publication_id,
        input_refs=(brief.brief_id,),
        variants=(
            DistributionVariant(
                destination=ChannelDestination(
                    channel="website",
                    provider_kind="website",
                    connection_ref="connection_example_website",
                    destination_account_ref="destination_learning_publication",
                ),
                selected_artifact_refs=(ARTIFACT_REF,),
                content=ContentDocument(
                    media_type="text/html",
                    content="<p>Review the governed handoff example.</p>",
                ),
                accessibility_text="A tutorial about a digest-bound creator handoff.",
            ),
        ),
    )


def execute_handoff(
    root: Path,
    *,
    creator_assignment_override: str | None = None,
    tamper_after_manifest: bool = False,
) -> dict[str, Any]:
    """Run the bounded bridge and return an observable summary."""

    organization, outcome, sow, assignment = _governed_assignment(root)
    current_sow = organization.sows_for(outcome.id)[0]
    origin = organization.pulse_origin_for_sow(sow.id)
    publication = _publication()
    creator_assignment = _creator_assignment(
        sovereign_assignment_id=creator_assignment_override or assignment.id,
        scope=sow.scope,
        publication=publication,
    )
    _require_assignment_binding(
        sovereign_assignment_id=assignment.id,
        creator_assignment=creator_assignment,
    )
    brief, synthesis = _invoke_content_brief(
        assignment=creator_assignment,
        publication=publication,
        scope=sow.scope,
    )
    artifact, manifest = _produce_manifest(root, brief)
    if tamper_after_manifest:
        artifact.write_text("tampered after manifest", encoding="utf-8")
    _require_current_bytes(artifact, manifest)
    channel_plan = _channel_plan(brief)

    registry = capability_registry()
    validation = invoke_sync(
        registry.get("creator.validate_delivery@1.0.0"),
        ValidateDeliveryRequest(
            brief=brief,
            manifest=manifest,
            publication=publication,
            synthesis=synthesis,
            channel_plan=channel_plan,
            created_at=NOW,
        ),
        make_context(capability_name="validate_delivery"),
    )
    if not isinstance(validation.data, ValidateDeliveryResponse):
        raise HandoffRefusal("delivery_validation_failed", validation.human_message)
    review = validation.data.review
    if not review.ready_for_approval:
        raise HandoffRefusal("delivery_blocked", "ZEO Creator reported blocking findings")

    prepared = invoke_sync(
        registry.get("creator.prepare_distribution@1.0.0"),
        PrepareDistributionRequest(
            brief=brief,
            manifest=manifest,
            review=review,
            channel_plan=channel_plan,
            created_at=NOW,
        ),
        make_context(capability_name="prepare_distribution"),
    )
    if not isinstance(prepared.data, PrepareDistributionResponse):
        raise HandoffRefusal("distribution_preparation_failed", prepared.human_message)

    handoff = {
        "sovereign_agent": {
            "outcome_id": outcome.id,
            "outcome_state": outcome.state.value,
            "sow_id": sow.id,
            "sow_state": current_sow.state.value,
            "assignment_id": assignment.id,
            "assignment_state": assignment.state.value,
            "origin": origin.origin_kind if origin else "missing",
            "acceptance_recorded": False,
        },
        "zeo_creator": {
            "assignment_id": brief.assignment_id,
            "assignment_binding": "MATCH",
            "brief_id": brief.brief_id,
            "brief_digest": brief.content_digest,
            "manifest_digest": manifest.content_digest,
            "delivery_ready": review.ready_for_approval,
            "approval_digest": review.approval_digest,
            "proposed_operations": len(prepared.data.operations),
            "executed_operations": 0,
        },
    }
    encoded = json.dumps(handoff, indent=2, sort_keys=True) + "\n"
    (root / "handoff.json").write_text(encoded, encoding="utf-8")
    handoff["handoff_digest"] = _sha256(encoded.encode())
    return handoff

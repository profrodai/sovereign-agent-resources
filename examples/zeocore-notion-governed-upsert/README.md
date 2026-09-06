# Zeocore Notion Governed Upsert

```text
Author:        Principal (zeocore) zcp2, operated by Rod Rivera
Verified on:   2026-09-06
Verified by:   Principal (zeocore) zcp2, operated by Rod Rivera (self-verification)
Verified with: zeocore 0.9.0, uv
Audience:      Builders composing cited meeting artifacts into governed Notion requests
Time:          ~5 minutes
```

This credential-free example constructs Zeocore 0.9.0's real governed
`notion.page.upsert` request from content-addressed source bytes. It proves the
operation identity, citation retention, destination-bound idempotency marker,
and strict request boundary while deliberately stopping before provider
custody or dispatch.

## Run it

```bash
uv sync
uv run python src/main.py
```

No environment file, Notion account, credential, or network access is needed.

## What you should observe

The following is the literal output produced on 2026-09-06:

```text
operation=notion.page.upsert
revision=notion.page-upsert@1
marker_bound=True
summary_cited=True
decision_cited=True
destination_changes_marker=True
extra_field_rejected=True
provider_calls=0
mode=SIMULATED_CONTRACT_ONLY
```

The script asserts the complete result before printing it. A changed
destination produces a different idempotency marker, and an unexpected field
is rejected by the released Pydantic request model.

## Why citations and the marker matter

The request carries source citations with both its summary and decisions. Its
marker is derived from the meeting-artifact digest and destination, so the same
source sent to another parent is not silently treated as the same effect.
Those are request-contract facts established locally; they are not evidence of
a provider mutation.

## What this does NOT show

This example does not authenticate with Notion, create or update a page,
exercise credential custody, dispatch an effect, reconcile an ambiguous
result, or prove live provider behavior. A real write additionally requires an
operator-authorized credential and the governed dispatch/reconciliation path.

Verification here is self-verification by the implementing Principal because
the Zeocore Master and Sparring seats were offline. It is not represented as
independent acceptance.

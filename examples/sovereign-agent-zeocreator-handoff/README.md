# Sovereign Agent to ZEO Creator: a governed handoff

```text
Author:        Principal (sovereign-agent), operated by Rod Rivera
Verified on:   2026-09-06
Verified by:   Principal (sovereign-agent), operated by Rod Rivera
Verified with: sovereign-agent 1.4.0 / zeo-creator 0.2.0.dev0 at 4d807f68c330a075e27c7b4714ca0ebf2e88f948 / zeocore 0.9.0, uv
Audience:      Builders connecting governed work to creator-domain capabilities
Time:          15–20 minutes
```

Watch one real Sovereign Agent outcome become a ready SOW and exact assignment,
then follow that assignment identity through a ZEO Creator editorial assignment,
typed content brief, locally produced artifact, delivery review, and write-free
publication proposal. Two attacks prove the bridge refuses a substituted
assignment identity and bytes changed after the producer declared its manifest.

This is an application-owned handoff, not framework magic. The bridge code is
small enough to inspect and names the exact place where Sovereign Agent 1.4 and
ZEO Creator do—and do not—connect.

## Run it

From this directory:

```bash
uv sync --frozen
uv run python src/run_demo.py
uv run python check_examples.py
```

No key, account, model, provider, browser, or network connection is used after
dependencies are installed. Every run uses a fresh temporary Sovereign Agent
organization and temporary producer output.

## What you should observe

This is the real output from `uv run python src/run_demo.py`:

```text
=== governed handoff ===
outcome: ACTIVE
sow: ASSIGNED
assignment: CREATED
origin: manual
assignment binding: MATCH
delivery ready: True
proposed operations: 1
executed operations: 0
sovereign acceptance recorded: False
=== refusal controls ===
identity mismatch: REFUSED (assignment_identity_mismatch)
byte tamper: REFUSED (artifact_bytes_changed)
```

The smoke checker independently executes all three paths:

```text
PASS governed handoff: assignment-bound brief and one write-free proposal
PASS refusal: assignment_identity_mismatch
PASS refusal: artifact_bytes_changed
```

Generated identifiers and digests are intentionally not pasted as fixed output.
Sovereign Agent mints fresh outcome, SOW, and assignment identifiers on each run.
The checker proves their relationship instead of blessing one captured value.

## The connection, stage by stage

```text
Sovereign Agent
  outcome ACTIVE
    -> SOW ASSIGNED
      -> assignment CREATED
        -> exact assignment id
             |
             | application adapter validates identity
             v
ZEO Creator
  EditorialAssignment
    -> ContentBrief with the same assignment id
      -> deterministic local producer bytes
        -> byte-derived ArtifactManifest
          -> DeliveryReviewBundle ready for approval
            -> ProposedPublicationOperation
              -> zero execution
```

### 1. Sovereign Agent governs the work envelope

`Organization` creates an outcome, activates it, creates and readies a SOW, and
assigns it to the bounded course operator. The SOW explicitly asks for one
evidence-grounded article brief and forbids executing publication. Its
`PulseOrigin` is `manual`, so origin is read from durable state rather than
inferred from a missing event.

The example deliberately does not call `run_assignment`. Sovereign Agent 1.4's
provider registry accepts its five intelligence-provider adapters; it does not
expose a public adapter for arbitrary Python capabilities.

### 2. The application maps one exact identity

The bridge creates a ZEO Creator `EditorialAssignment` whose `assignment_id` is
byte-for-byte equal to the Sovereign Agent assignment ID. It checks that equality
before invoking a creator capability. Substituting another ID produces the named
`assignment_identity_mismatch` refusal.

The remaining creator inputs are publication-scoped contracts: a
`PublicationProfile`, a `ResearchSynthesis`, one evidence claim, and required
delivery attestations. No credential or provider object enters those contracts.

### 3. ZEO Creator creates and validates creator-domain artifacts

`creator.create_content_brief@1.0.0` turns the typed editorial assignment into
a producer-neutral `ContentBrief`. A deterministic local producer writes one
HTML file and calculates its descriptor and digest proof from the bytes it
actually wrote.

The application re-reads those bytes immediately before ZEO Creator validation.
Changing the file after manifest construction produces the named
`artifact_bytes_changed` refusal. This check belongs to the producer adapter:
ZEO Creator validates the manifest and its proof contracts but does not fetch an
`artifact://` reference by itself.

`creator.validate_delivery@1.0.0` then checks assignment/brief/manifest scope,
required attestations, evidence traceability, brand constraints, selected
artifacts, and manifest integrity. Only a ready review reaches
`creator.prepare_distribution@1.0.0`.

### 4. The boundary stays visible

The final object is a digest-bound proposal. It requires later write and
external-communication authority, but this example never grants either and
never calls a connector. `executed_operations: 0` is an asserted invariant, not
decorative output.

The application also writes `handoff.json` inside the temporary root and hashes
it. That file links Sovereign Agent IDs and states to ZEO Creator IDs and
digests. It is application evidence, not a Sovereign Agent `Receipt`.

## Why ZEO Creator is pinned to a Git commit

ZEO Creator is currently `0.2.0.dev0` and is not published on PyPI. Its own
installation contract uses Git. This resource therefore makes the pre-release
exception visible and immutable in both `pyproject.toml` and `uv.lock`:

```text
zeo-creator @ git+https://github.com/profrodai/zeocreator.git@4d807f68c330a075e27c7b4714ca0ebf2e88f948
```

That commit requires Zeocore 0.9.0, which resolves transitively. The repository's
shared `ZEOCORE_VERSION` remains 0.6.0 because this resource does not claim to be
a Zeocore catalog example and does not directly pin Zeocore. When ZEO Creator is
released, moving this resource to a registry version is a separate reviewed
migration—not a lockfile refresh to perform casually.

## Break-it experiments

Make one change, predict which assertion fails, then rerun
`uv run python check_examples.py`:

1. Remove `_require_assignment_binding`. The identity attack should stop
   refusing, proving an import alone does not preserve governed identity.
2. Remove `_require_current_bytes`. The tamper attack should reach contract
   validation, showing why a self-consistent manifest is not proof of current
   bytes.
3. Change `executed_operations` to `1`. The happy-path smoke assertion should
   fail; proposal construction is not execution.
4. Change the channel plan from `website` to an unapproved channel. ZEO Creator
   should return a blocking destination finding instead of a ready review.

## What this does not show

- No Sovereign Agent assignment is executed and no external result is imported
  as a Sovereign Agent receipt. Version 1.4 has no public generic bridge for
  that; `sovereign acceptance recorded: False` keeps the gap visible.
- No human or Principal approves the delivery. `ready_for_approval` means the
  typed preconditions passed, not that approval happened.
- No publication, connector write, scheduling, OAuth, provider SDK, credential,
  model call, retry loop, or reconciliation occurs.
- The deterministic HTML producer teaches the contract boundary. It is not a
  renderer, editorial model, or production content engine.
- A Git commit pin is reproducible source identity, not a released package or a
  long-term catalog compatibility promise.
- This resource proves local composition of these exact versions. It does not
  claim production readiness or compatibility with a future ZeoCreator commit.

## Files

| File | Purpose |
|---|---|
| `src/handoff.py` | Governed setup, contract mapping, producer adapter, validation, proposals, and named refusals |
| `src/run_demo.py` | Human-readable happy path and both attacks |
| `check_examples.py` | Behavioral smoke assertions for all three paths |
| `pyproject.toml` | Exact Sovereign Agent and immutable ZeoCreator dependencies |
| `uv.lock` | Complete reproducible resolution, including transitive Zeocore 0.9.0 |

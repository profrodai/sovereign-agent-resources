# Zeocore Supabase Bounded Data

```text
Author:        Principal (zeocore) zcp2, operated by Rod Rivera
Verified on:   2026-09-06
Verified by:   Principal (zeocore) zcp2, operated by Rod Rivera (self-verification)
Verified with: zeocore 0.9.0, uv
Audience:      Builders learning Zeocore's bounded Supabase database boundary
Time:          ~10 minutes
```

This credential-free example sends select, insert, and upsert operations
through Zeocore 0.9.0's real `SupabaseClient` and `SupabaseIntegration`. The
provider boundary is an injected, stateful SDK-shaped fake, so query
construction, validation, typed response normalization, and refusal behavior
run for real while provider and network behavior remain explicitly unclaimed.

## Run it

```bash
uv sync
uv run python src/main.py
```

No environment file, Supabase project, credential, database, or network access
is needed.

## What you should observe

The following is the literal output produced on 2026-09-06:

```text
selected_rows=1
inserted_rows=1
upserted_status=ready
typed_filter_applied=True
invalid_table_refused=True
over_limit_refused=True
refusals_executed_queries=0
sdk_executions=3
network_calls=0
canary_absent=True
canary_control_detected=True
mode=IN_MEMORY_PROVIDER_BOUNDARY
```

The fake begins with one `ready` and one `pending` row. Zeocore applies a typed
equality filter, inserts a third row, then idempotently upserts that row by
`id`. An invalid table identifier and a request above the configured two-row
limit both become unsuccessful `IntegrationResult` values without executing a
query.

The same substring instrument is calibrated against a deliberately contaminated
in-memory rendering and reports `canary_control_detected=True`; the clean result
is therefore not accepted from an instrument never shown to detect its target.

## The boundary being demonstrated

The fake implements only the narrow SDK methods the public Zeocore database
client calls. This keeps the example deterministic while ensuring it cannot
pass by replacing Zeocore with a hand-written data layer. A clearly synthetic
canary enters only the client constructor; the script proves it is absent from
the client representation and every returned or refused result.

## What this does NOT show

This example does not prove a live Supabase connection, network transport,
Postgres behavior, RLS, tenancy, Auth, Storage, Functions, Realtime, deployment,
or credential custody. It never uses a privileged key, `service_role`, Vault,
or raw SQL. ZEOconnect's private Supabase project is outside this resource.

Verification here is self-verification by the implementing Principal because
the Zeocore Master and Sparring seats were offline. It is not represented as
independent acceptance.

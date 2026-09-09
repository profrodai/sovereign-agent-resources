# Examples

Complete, clone-and-run projects. Each is pinned to the catalog versions in the
repository root and migrated with `make migrate`.

| Example | What it shows | Requirements |
|---|---|---|
| [`zeocore-0100`](zeocore-0100/) | Offline HubSpot/Kit capabilities, managed account tracks, native fake services, Gemini request construction and notebook authoring receipts | uv + Git |
| [`sovereign-agent-advanced-patterns`](sovereign-agent-advanced-patterns/) | Six offline labs for isolation, durable automation, recoverable context, session incarnations, bounded tool discovery, and hybrid memory | uv |
| [`sovereign-agent-live-demo`](sovereign-agent-live-demo/) | A real local LLM tool-calls a ZeoCore capability; the Sovereign Agent governs the result — replay, refusal, and a full accepted loop | uv + Ollama (offline warmup needs neither model nor keys) |
| [`sovereign-agent-zeocreator-handoff`](sovereign-agent-zeocreator-handoff/) | One governed assignment becomes a digest-bound ZEO Creator brief, validated artifact, and write-free proposal, with identity and byte-tamper refusals | uv |
| [`zeocore-examples`](zeocore-examples/) | Three real applications rebuilt on zeocore: CSV cleaning, doc→Bluesky, metrics — typed tools doing actual work | uv |
| [`zeocore-notion-governed-upsert`](zeocore-notion-governed-upsert/) | Build a cited, destination-bound `notion.page.upsert` request and prove its strict boundary without credentials or dispatch | uv |
| [`zeocore-supabase-bounded-data`](zeocore-supabase-bounded-data/) | Exercise bounded select, insert, upsert, typed filters, and refusal edges through Zeocore's real Supabase client with an in-memory provider boundary | uv |

To add an example, follow [docs/RESOURCE_TEMPLATE.md](../docs/RESOURCE_TEMPLATE.md).

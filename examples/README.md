# Examples

Complete, clone-and-run projects. Each is pinned to the catalog versions in the
repository root and migrated with `make migrate`.

| Example | What it shows | Requirements |
|---|---|---|
| [`sovereign-agent-advanced-patterns`](sovereign-agent-advanced-patterns/) | Six offline labs for isolation, durable automation, recoverable context, session incarnations, bounded tool discovery, and hybrid memory | uv |
| [`sovereign-agent-live-demo`](sovereign-agent-live-demo/) | A real local LLM tool-calls a ZeoCore capability; the Sovereign Agent governs the result — replay, refusal, and a full accepted loop | uv + Ollama (offline warmup needs neither model nor keys) |
| [`sovereign-agent-zeocreator-handoff`](sovereign-agent-zeocreator-handoff/) | One governed assignment becomes a digest-bound ZEO Creator brief, validated artifact, and write-free proposal, with identity and byte-tamper refusals | uv |
| [`zeocore-examples`](zeocore-examples/) | Two real applications rebuilt on zeocore: CSV cleaning, doc→Bluesky, metrics — typed tools doing actual work | uv |

To add an example, follow [docs/RESOURCE_TEMPLATE.md](../docs/RESOURCE_TEMPLATE.md).

# A Real Agent, Governed — with your choice of model provider

```text
Author:        Rod Rivera
Verified on:   2026-09-05
Verified by:   Principal (sovereign-agent), operated by Rod Rivera
Verified with: sovereign-agent 1.3.0 / zeocore 0.6.0, uv
Audience:      Practitioners learning to separate model intelligence from authority
Time:          ~20 minutes after provider setup
```

A model helps run Lucy's ice-cream shop. It calls a typed ZeoCore capability,
proposes a restock, and Sovereign Agent checks the proposal against the real
ledger before anything changes.

Choose the intelligence that fits your machine and account:

| Provider | Where inference runs | What you need | Default model |
|---|---|---|---|
| Ollama | your computer | Ollama and enough RAM | `qwen3:latest` |
| OpenAI | OpenAI's API | `OPENAI_API_KEY` | `gpt-5-mini` |
| Anthropic | Anthropic's API | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` |

The provider changes; the tool contract, ledger validation, bounds, commit,
verification, and acceptance do not. An actor is not a model: the model
proposes and governed code decides.

Teaching this? Start with
[`CLASS-RUNBOOK-2026-09-05-Rev-3.md`](CLASS-RUNBOOK-2026-09-05-Rev-3.md);
it binds the timeout and ZeoCore credential-loading corrections and points to
the full Rev 2 narration.

## 1. Install and choose one provider

```bash
git clone https://github.com/profrodai/sovereign-agent-resources.git
cd sovereign-agent-resources/examples/sovereign-agent-live-demo
```

### Option A — Ollama, local and keyless

Install [Ollama](https://ollama.com/download), then run `bash setup.sh ollama`.
Setup installs the pinned PyPI packages, pulls `qwen3:latest` only if absent,
and warms it. Set `OLLAMA_MODEL=another-model` in `.env` to override it.

### Option B — OpenAI API

Create a secret project API key on the
[OpenAI API key page](https://platform.openai.com/api-keys), then:

```bash
cp .env.example .env
chmod 600 .env
```

Set these lines in `.env`:

```dotenv
SOVEREIGN_DEMO_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-5-mini
```

Run `bash setup.sh openai`. Setup validates configuration but makes no billed
API call.

### Option C — Anthropic API

Create an API key in the
[Anthropic Console](https://console.anthropic.com/settings/keys), then create
and protect `.env` as above. Set:

```dotenv
SOVEREIGN_DEMO_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-6
```

Run `bash setup.sh anthropic`. Setup validates configuration but makes no API
call.

`.env` is ignored. The loader treats it as `KEY=value` data, never executes it,
and existing process environment variables take precedence. Never commit,
paste, print, or screenshot the real file. Cloud providers receive the demo's
prompts and tool results; use Ollama when data must remain local.

## 2. Run the same three-stage lesson

Replace `PROVIDER` with `ollama`, `openai`, or `anthropic` in both live steps.
The explicit choice overrides `SOVEREIGN_DEMO_PROVIDER` in `.env`.

```bash
# Deterministic fallback: no model, network, account, or key
uv run sovereign-agent demo store --mode simulated

# A real model calls a typed ZeoCore read capability; governance refuses 9999
uv run python demo_tool_calling.py --provider PROVIDER

# The model drives propose -> commit -> verify -> accept
uv run python demo_full_governance.py --provider PROVIDER
```

### Stage 1 — deterministic governance

The packaged tea-store actor is scripted so the governance loop can always be
shown offline. The point is not intelligence; it is that an outcome becomes
`ACCEPTED` only after evidence and verification agree with the claim.

### Stage 2 — real tool calling, bounded authority

`demo_tool_calling.py`:

1. writes a sale to a disposable SQLite ledger, taking vanilla stock from 4 to 2;
2. exposes `inspect_inventory`, a ZeoCore `@capability` with typed request and
   response models and a declared `READ` effect;
3. sends that capability's JSON schema to the selected model;
4. executes the model's tool request through ZeoCore's `invoke_sync`;
5. gives the read-only result back to the model and receives a restock proposal;
6. asks Sovereign Agent's shop rules to re-read cost and stock from the ledger;
7. proves the bound by passing an absurd `9999` proposal and showing refusal.

`model_provider.py` normalizes Ollama, OpenAI function calls, and Anthropic
`tool_use` blocks into one internal message shape. It does not normalize
authority: the model has none to begin with.

### Stage 3 — the full governed loop

`demo_full_governance.py` initializes a disposable organization, creates an
outcome and SOW, assigns the operator actor, and binds that actor to the chosen
provider through a provider-specific `DemoModelProvider` registry name. The resource-local worker asks the model
for a strict `ActorReport`. That report remains advisory. Deterministic Python
then validates and atomically applies the proposal, another actor verifies the
ledger, Sparring reviews the SOW, and the Principal accepts the outcome.

## Provider boundary and secrets

```text
.env (ignored) -> ProviderConfig -> HTTP request -> normalized proposal
                                      |
                                      v
ZeoCore typed capability -> Sovereign Agent validation -> commit/verify/accept
```

- `OPENAI_API_KEY` is sent only as an HTTP bearer credential to OpenAI.
- `ANTHROPIC_API_KEY` is sent only in Anthropic's `x-api-key` header.
- Ollama sends no API key and defaults to `localhost`.
- Only variables for the selected provider cross into the disposable actor
  subprocess.
- Keys are never copied into assignment JSON, reports, receipts, transcripts,
  or the SQLite ledger.

## Troubleshooting

| Symptom | Action |
|---|---|
| Missing API key | Copy `.env.example` to `.env`, fill only the chosen key, and rerun setup. |
| HTTP 401/403 | Stop; check key and account access. Do not blind-retry authentication failures. |
| Ollama connection refused | Start the Ollama app or run `ollama serve`. |
| Ollama first call is slow | Run `printf '' \| ollama run qwen3:latest` before class. |
| Provider times out | Inspect the disposable workspace/provider logs; choose a smaller/faster model or correct reachability before retrying. |
| Cloud data is not acceptable | Select `--provider ollama`; cloud choices send prompts to their vendors. |

## Offline verification

Credential-free contract tests simulate both cloud wire formats and prove
`.env` precedence, missing-key refusal, OpenAI function calls, and Anthropic
tool-use/tool-result translation:

```bash
uv run python test_model_provider.py
```

This does not claim live cloud execution without operator-supplied credentials.

## Files

| File | Purpose |
|---|---|
| `.env.example` | safe variable-name template; contains no secret |
| `model_provider.py` | `.env`, selection, HTTP calls, and message normalization |
| `demo_provider_worker.py` | turns a selected model response into an advisory `ActorReport` |
| `demo_tool_calling.py` | Stage 2: ZeoCore tool call and refusal proof |
| `demo_full_governance.py` | Stage 3: full governed organization loop |
| `test_model_provider.py` | offline unit and six-path end-to-end provider checks |
| `setup.sh` | idempotent provider-aware setup |

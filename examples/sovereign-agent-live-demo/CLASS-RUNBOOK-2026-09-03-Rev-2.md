# Class runbook Rev 2 — choose Ollama, OpenAI, or Anthropic

**Created:** 2026-09-03 · **Last-updated:** 2026-09-03 · **Status:** ACTIVE

This revision supersedes `CLASS-RUNBOOK-2026-09-03.md` for the live-model
steps. The original measured Ollama run remains the evidence for the local
path. The OpenAI and Anthropic transports are contract-tested against their
wire formats; live cloud execution awaits operator-supplied credentials.

## What the class demonstrates

The intelligence provider is a choice, not part of the governance contract.
All three providers feed the same two demos:

```text
Ollama --------┐
OpenAI --------+--> model proposal --> deterministic governance --> effect
Anthropic -----┘                              |                 --> refusal
                                              +--> verification --> acceptance
```

The useful contrast is explicit: local versus cloud changes where inference
happens and how it is authenticated. It does not give the model more authority.

## Before class: choose and prepare one provider

```bash
git clone https://github.com/profrodai/sovereign-agent-resources.git
cd sovereign-agent-resources/examples/sovereign-agent-live-demo
```

### Local Ollama

```bash
bash setup.sh ollama
ollama list
printf '' | ollama run qwen3:latest
```

### OpenAI

Create a project API key at <https://platform.openai.com/api-keys>. Then:

```bash
cp .env.example .env
chmod 600 .env
```

Edit `.env` without displaying it on the projector:

```dotenv
SOVEREIGN_DEMO_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-5-mini
```

Validate without spending tokens:

```bash
bash setup.sh openai
```

### Anthropic

Create an API key at <https://console.anthropic.com/settings/keys>, create and
protect `.env` as above, then set:

```dotenv
SOVEREIGN_DEMO_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-6
```

Validate without making an API call:

```bash
bash setup.sh anthropic
```

Never show `.env`, keys, request headers, or shell history in class. The file is
ignored and only the selected provider's variables cross into the model worker.

## The guaranteed class path

Choose `PROVIDER=ollama`, `PROVIDER=openai`, or `PROVIDER=anthropic` in your
shell. This variable is only a convenience for these commands; the Python
scripts still receive an explicit choice.

```bash
PROVIDER=ollama

# 1. Guaranteed offline governance
uv run sovereign-agent demo store --mode simulated

# 2. Real model -> real ZeoCore capability -> governed proposal/refusal
uv run python demo_tool_calling.py --provider "$PROVIDER"

# 3. Real model -> complete propose/commit/verify/accept loop
uv run python demo_full_governance.py --provider "$PROVIDER"
```

If the provider or network fails, Step 1 remains the honest fallback. Do not
describe a failed live call as a successful demo.

## Narration: what runs behind each command

### Step 1 — prove governance without model variability

`sovereign-agent demo store --mode simulated` loads Sovereign Agent's packaged
store organization. A deterministic actor reports proposed work, the framework
records evidence, verification compares claimed and observed state, and only
then the outcome reaches `ACCEPTED`. No ZeoCore capability or network provider
is involved in this warmup.

Say: “The guardrails do not depend on a model behaving well.”

### Step 2 — show the intelligence/tool boundary

Open `demo_tool_calling.py` and follow this chain:

1. `seed_catalog` creates the disposable store ledger.
2. `record_sale` changes vanilla `on_hand` from 4 to 2 and emits a signal.
3. `@capability` has already turned `inspect_inventory` into a typed ZeoCore
   capability with a declared read effect.
4. `CAP.request_model.model_json_schema()` builds the tool schema handed to the
   selected model.
5. `model_provider.chat` translates that schema and messages for Ollama,
   OpenAI, or Anthropic.
6. The model—not a hard-coded branch—returns a tool call.
7. `invoke_sync` validates the arguments and runs the ZeoCore capability.
8. The read-only SQLite result returns to the model as a tool result.
9. The model proposes `RESTOCK_UNITS: N`.
10. `validate_restock` distrusts that number, re-reads the ledger and true unit
    cost, and enforces the maximum quantity.
11. The explicit `9999` proposal proves the refusal branch is live.

Say: “The model can ask the tool and propose a number. It cannot change stock.”

Provider-specific bytes are confined to `model_provider.py`:

- Ollama uses `/api/chat` and its `message.tool_calls` shape.
- OpenAI uses `/v1/chat/completions`, bearer authentication, and function calls.
- Anthropic uses `/v1/messages`, `x-api-key`, `tool_use`, and `tool_result`.

All three are normalized before ZeoCore sees the request.

### Step 3 — show the full organization, not just validation

Open `demo_full_governance.py` and follow:

1. `Organization.init` creates a disposable organization and ledger.
2. `create_outcome`, `activate`, `create_sow`, `ready_sow`, and `assign` create
   an addressable governed assignment.
3. `DemoModelProvider` binds the actor to the selected transport without
   changing the installed Sovereign Agent package.
4. `org.run_assignment` invokes `demo_provider_worker.py` in the disposable
   workspace.
5. The worker asks the model for strict JSON and writes an advisory
   `ActorReport`; it does not apply the proposal.
6. `apply_restock` validates and commits inventory and cash atomically.
7. `verify_outcome` checks the effect independently.
8. `review` records the separate review layer.
9. `accept` moves the outcome to its terminal accepted state.

Say: “We swapped intelligence, not the constitution of the company.”

## Safety and proof boundary

- Step 1 requires no model or key.
- Setup does not call a cloud model; the first live script is the first billed
  request.
- Cloud prompts and tool results leave the laptop. Use Ollama for local data.
- A 401 or 403 is an authentication checkpoint, not a retry opportunity.
- `uv run python test_model_provider.py` is an offline contract proof. It does
  not prove that an operator's cloud account, quota, or chosen model is live.
- The original runbook's Google and Bluesky credential section is unrelated to
  these model-provider keys and remains the reference for those integrations.
  Its old note that demos do not load `.env` is superseded here: these two
  model demos do load it; Google and Bluesky continue to use their documented
  ZeoCore credential locations and environment variables.

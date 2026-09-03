# Class runbook — Sovereign Agent + Ollama + ZeoCore

Verified on 2026-09-03 from `profrodai/sovereign-agent-resources@9032750` on
macOS with Ollama 0.32.5, `qwen3:latest`, Sovereign Agent 1.1.1, ZeoCore 0.6.0,
and uv. The commands in the green path below were executed, not inferred.

## The guaranteed class path

Clone the catalog and enter the live-demo resource:

```bash
git clone https://github.com/profrodai/sovereign-agent-resources.git
cd sovereign-agent-resources/examples/sovereign-agent-live-demo
bash setup.sh
```

If the model is already installed, `setup.sh` is safe to rerun. Before class,
confirm Ollama is running and the model is present:

```bash
ollama list
printf '' | ollama run qwen3:latest
```

Run these in order:

```bash
# 1. Deterministic fallback: Sovereign Agent, no model or credentials
uv run sovereign-agent demo store --mode simulated

# 2. A real Ollama model calls a typed ZeoCore capability; governance rejects 9999
uv run python demo_tool_calling.py

# 3. The real model drives the full propose -> commit -> verify -> accept loop
uv run python demo_full_governance.py
```

Measured on the instructor machine:

| Step | Exit | Observed result |
|---|---:|---|
| Scripted store | 0 | Outcome `ACCEPTED` |
| Ollama tool calling | 0 | Model called `inspect_inventory`; proposal 1 was valid; 9999 was refused |
| Full Ollama governance | 0 | Inventory and cash committed, independently verified, then accepted |

The current catalog demo uses Ollama. It does not claim an API-model path that
has not been implemented or exercised. If the network or model fails during
class, Step 1 is the honest guaranteed fallback.

## The idea to explain before running anything

The three commands separate three concerns that are easy to blur together:

1. **Sovereign Agent governs the work.** It records the desired outcome, scope,
   actor assignment, execution, evidence, review, and final acceptance.
2. **Ollama supplies intelligence, not authority.** `qwen3:latest` may inspect
   information and propose a quantity. It cannot write inventory, choose the
   price, approve itself, or declare the outcome accepted.
3. **ZeoCore defines the typed tool boundary in Step 2.** It turns a Python
   function into a capability with request and response models, a declared
   `READ` effect, metadata, and validated invocation.

The sequence demonstrates these layers progressively:

```text
Step 1  Sovereign Agent governance + deterministic scripted provider
Step 2  Ollama reasoning + a typed ZeoCore read capability + governance refusal
Step 3  Ollama reasoning + the full Sovereign Agent effect and acceptance loop
```

The sequence as a whole demonstrates Sovereign Agent, Ollama, and ZeoCore.
Step 3 does not secretly call the ZeoCore tool from Step 2: the assignment scope
contains the current stock figures, and the built-in Ollama provider returns an
`ActorReport`. That separation is intentional and should be stated in class.

## Before the demo: what setup is doing

`bash setup.sh` performs four visible operations:

1. It checks that `uv` is installed.
2. It runs `uv sync`, which creates or updates the resource's isolated `.venv`
   from `pyproject.toml` and `uv.lock`. The lock selects Sovereign Agent 1.1.1
   and ZeoCore 0.6.0 from PyPI; the demo does not import a neighboring source
   checkout by accident.
3. It checks for Ollama and pulls `qwen3:latest` only when the model is absent.
4. It sends an empty prompt once so Ollama loads the model before students are
   waiting on the first real inference.

`ollama list` then proves that the model is installed on this machine. The warmup
command starts or loads the model, but it creates no Sovereign Agent outcome and
changes no shop ledger:

```bash
ollama list
printf '' | ollama run qwen3:latest
```

No cloud model or API key is involved. The two live scripts talk to the local
Ollama server over HTTP.

## Step 1 — prove the governance loop without depending on a model

```bash
uv run sovereign-agent demo store --mode simulated
```

This invokes the installed Sovereign Agent CLI. Its `_demo` command dispatches
to `reference_organizations.store.demo.run_simulated`. The provider is scripted,
so the result is deterministic and remains available if Ollama fails during the
class.

Behind the scenes, the call path is:

```text
sovereign-agent CLI
  -> run_simulated(current directory)
  -> Organization.init(...)
  -> seed the tea product, inventory, and opening cash
  -> create_outcome(...) and activate(...)
  -> record_sale(...)
  -> create_sow(...) -> ready_sow(...) -> assign(...)
  -> run_assignment(...) using the scripted provider
  -> read .sovereign-out/report.json
  -> convert the report into a RestockProposal
  -> apply_restock(...) in one database transaction
  -> verify_outcome(...) -> review(...) -> accept(...)
  -> status_text(...)
```

What each part means:

- `Organization.init` creates or opens the `.sovereign` SQLite ledger beneath
  the current demo directory.
- The outcome declares a desired state—tea at or above its reorder point—and
  three executable checks: inventory level, cash reconciliation, and a durable
  replenishment event.
- `record_sale` reduces inventory, credits the cash ledger, and writes the
  durable `sig_...` inventory signal in the same transaction.
- The `sow_...` record is the bounded unit of work. It requires a
  `replenishment` effect, so an unrelated successful action cannot satisfy it.
- The scripted provider writes a proposal to the assignment workspace. The
  framework parses that report fail-closed: absent JSON, malformed JSON, or a
  non-integer quantity is refused rather than guessed.
- `apply_restock` does not trust the proposal as permission. Under one immediate
  database transaction it verifies the assignment, actor authority, outcome
  subject, quantity bound, real product cost, and available cash; then it
  updates inventory, debits cash, records the effect, resolves the signal, and
  appends the event.
- Verification runs before review. Acceptance then re-executes the declared
  checks against current state, requires the stored evidence still to match
  that state, and prevents the performer from accepting its own work.

Read the output accordingly:

```text
out_... ACCEPTED Keep the tea jar stocked
  sow_... ACCEPTED Manually dispatched replenishment after signal sig_...
outcome ACCEPTED
```

`sig_` identifies the observed condition, `sow_` the governed work, and `out_`
the desired outcome. `ACCEPTED` is not the provider saying “done”; it is the
terminal governance state reached after effect, verification, review, and
acceptance. This step proves that lifecycle, but it proves neither live model
reasoning nor ZeoCore tool calling.

## Step 2 — let the model call a real, typed ZeoCore capability

```bash
uv run python demo_tool_calling.py
```

Open [`demo_tool_calling.py`](demo_tool_calling.py) while explaining this step.
It creates a temporary SQLite organization database and seeds two independent
products. Vanilla starts at 4 units with a reorder point of 3. A sale of 2
leaves 2 units and creates the printed `sig_...` record. Chocolate is present
as a second product so the example is genuinely SKU-specific rather than a
single hard-coded stock slot.

### The ZeoCore portion

The `InspectInventoryRequest` and `InspectInventoryResponse` Pydantic models
define the only accepted input and the typed output. The `@capability`
decorator adds:

- the stable id `store.inspect_inventory@1.0.0`;
- a description telling the actor to inspect rather than guess;
- a declared `{EffectKind.READ}` effect; and
- an example request and response.

`bound_capability_of(inspect_inventory)` produces a bound definition containing
that metadata and the request model. `run_actor` turns the request model into
JSON Schema with `model_json_schema()` and sends that schema to Ollama as its
one available function.

The tool itself opens the SQLite database using `mode=ro`, performs a
parameterized lookup for the requested SKU, and returns either
`CapabilityResult.ok(InspectInventoryResponse(...))` or a typed `NO_SKU`
failure. The tool has no write path.

### The model/tool conversation

`run_actor` sends Ollama a system message saying that the actor may only
**propose**, must inspect current inventory, and should return
`RESTOCK_UNITS: <integer>`. Then this loop occurs:

```text
Python sends prompt + ZeoCore-derived function schema to Ollama /api/chat
  -> qwen chooses inspect_inventory({"sku": "SKU-VANILLA"})
  -> Pydantic validates the model-generated arguments
  -> invoke_sync executes the bound ZeoCore capability
  -> the read-only ledger result is returned to qwen as a tool message
  -> qwen proposes RESTOCK_UNITS: 1
```

That is why these two output lines are different kinds of evidence:

```text
qwen CALLED zeocore tool inspect_inventory(...) -> {...}
qwen SAID: RESTOCK_UNITS: 1
```

The first proves a real tool invocation reached the database. The second is
only the model's proposal.

### The governance portion

The script converts the number to `RestockProposal(sku="SKU-VANILLA",
quantity=units)` and passes it to Sovereign Agent's `validate_restock`. That
trusted Python boundary independently rereads the product and inventory rows.
It enforces a positive quantity, a maximum of 50, a known product, an existing
inventory row, and sufficient cash. It obtains the 250-cent unit cost from the
product record; the model never gets to supply the cost or cash amount.

The second validation with quantity `9999` is an adversarial control. It proves
that a syntactically valid model proposal is not authority and that the bound is
behavioral, not merely documentation:

```text
9999 > MAX_RESTOCK_UNITS (50) -> Refusal -> no restock
```

Important boundary: this script calls `validate_restock`, not `apply_restock`.
It deliberately demonstrates inspection, proposal, and refusal without
committing the proposed replenishment. The only mutation is the fixture sale
that creates the condition the actor must reason about.

## Step 3 — run the proposal through commit, proof, review, and acceptance

```bash
uv run python demo_full_governance.py
```

Open [`demo_full_governance.py`](demo_full_governance.py) for this narration.
It uses another temporary organization and the same two-product ice-cream
fixture. The full flow is:

```text
Organization.init + seed_catalog
  -> create and activate outcome with three acceptance checks
  -> atomically record sale + cash credit + durable signal
  -> create, ready, and assign a replenishment SOW
  -> bind operator-course to Sovereign Agent's built-in ollama provider
  -> run_assignment -> qwen writes a governed ActorReport
  -> parse proposed_restock_units
  -> apply_restock under an immediate database transaction
  -> verify outcome checks
  -> independent SOW review
  -> Principal acceptance, with checks re-run against current state
```

The provider configuration is real but small. The script copies
`SOVEREIGN_DEMO_MODEL`—default `qwen3:latest`—to
`SOVEREIGN_AGENT_LLM_MODEL`. Sovereign Agent's shipped `ollama` provider talks
to Ollama's OpenAI-compatible endpoint at `http://localhost:11434/v1` unless
`SOVEREIGN_AGENT_LLM_BASE_URL` overrides it.

Unlike Step 2, the model receives the current `on_hand` and `reorder_point` in
the SOW scope. It does not receive the `inspect_inventory` tool. Its output is
written as `.sovereign-out/report.json` in the assignment workspace and parsed
as an `ActorReport`. A completed report is still not an applied effect.

`apply_restock` is the effect boundary. It first proves that the assignment is
real, completed, authorized for a replenishment effect, and attached to the
same outcome subject. Inside the same database lock it revalidates quantity,
catalog membership, cost, and cash. It then performs all of these together:

- inventory `2 + 1 -> 3`;
- cash purchase entry `-250` cents;
- durable replenishment effect tied to the assignment and outcome;
- resolution of the originating sale signal; and
- append-only `replenishment.committed` event.

The effect table has a uniqueness constraint over assignment, kind, and
subject, so replaying the same authorized effect returns the recorded result
instead of purchasing twice.

The final cash output is a compact audit trail:

```text
('cash-opening', 10000)  opening balance
('cash', 1000)           sale: 2 tubs x 500 cents
('cash', -250)           replenishment: 1 tub x trusted 250-cent cost
```

Finally, `verify_outcome` runs the declared checks and stores evidence,
`review` changes the SOW only after that evidence exists, and `accept` checks
the outcome again at acceptance time. Therefore the printed result:

```text
COMMITTED + VERIFIED + ACCEPTED
```

names three different facts. “Committed” means the ledger changed atomically;
“verified” means the checks observed the required state; “accepted” means the
governance chain admitted that evidence and independently confirmed the state
still held. The model performs none of those authority-bearing transitions.

## The one-sentence class takeaway

The model can inspect and propose; typed tools constrain what it can ask and
what data it receives; the governed runtime independently decides whether an
effect is authorized, records it atomically, proves the resulting state, and
only then accepts the outcome.

## Other catalog demos verified today

From the repository root:

```bash
cd examples/zeocore-examples/apps/data_cleaning
uv run python run_demo.py

cd ../metrics_tracker
uv run python run_demo.py

cd ../doc_to_bluesky
env -u GOOGLE_CLIENT_SECRETS_FILE \
    -u GOOGLE_CREDENTIALS_FILE \
    -u BLUESKY_IDENTIFIER \
    -u BLUESKY_APP_PASSWORD \
    -u BLUESKY_SERVICE_URL \
    uv run python run_demo.py

cd ../../../../tutorials/capability-authoring
uv run python src/main.py
```

All four commands exited 0 on 2026-09-03. The Doc-to-Bluesky command is the
safe zero-credential demonstration: it shows the real integrations refusing or
skipping honestly. It does not publish a post.

The repository-wide gates also passed:

```bash
make validate
make check-all KEEP_GOING=1
```

## Google OAuth: exactly what to create

Use one testing-only Google Cloud project and one **Desktop app OAuth client**.
Do not create an API key, service-account key, or Web application client for
these demos.

1. Open [Google Cloud Console](https://console.cloud.google.com/), select the
   project menu, choose **New Project**, and create a project such as
   `zeocore-class-demo`.
2. With that project selected, open **APIs & Services → Library**. Enable
   **Google Docs API** for the Doc-to-Bluesky example. Enable **Google Drive
   API** as well if you will run `data_cleaning/run_demo_drive.py`.
3. Open **Google Auth Platform → Branding**. If prompted, choose **Get
   Started**. Set an app name, support email, and contact email.
4. Open **Google Auth Platform → Audience**:
   - Use **Internal** only when the project belongs to a Google Workspace
     organization and the account used in class is inside that organization.
   - Otherwise use **External**, leave the app in **Testing**, and add the
     Google account used in class under **Test users**. Publication and Google
     verification are not required for a private classroom test.
5. In **Data Access**, the runtime will request its actual scopes. The Docs
   path requests `https://www.googleapis.com/auth/documents`; the Drive path
   requests Drive scopes. Do not add unrelated scopes.
6. Open **Google Auth Platform → Clients**, click **Create Client**, choose
   **Desktop app**, name it `zeocore-class-desktop`, and click **Create**.
7. Download the client JSON. That downloaded JSON—not a copied client ID—is the
   file ZeoCore needs.

Google's current official instructions are:

- [Enable Google Workspace APIs](https://developers.google.com/workspace/guides/enable-apis)
- [Configure the OAuth consent screen](https://developers.google.com/workspace/guides/configure-oauth-consent)
- [Create OAuth credentials](https://developers.google.com/workspace/guides/create-credentials)

### Store Google files on this Mac

Keep all credential material outside the repository. On macOS, ZeoCore's
per-user configuration directory is:

```text
~/Library/Application Support/zeocore/
```

Create it with owner-only permissions, then copy the exact downloaded file:

```bash
ZEOCORE_CREDENTIAL_DIR="$HOME/Library/Application Support/zeocore"
install -d -m 700 "$ZEOCORE_CREDENTIAL_DIR"
install -m 600 "/exact/path/from/Downloads/client_secret_FILE.json" \
  "$ZEOCORE_CREDENTIAL_DIR/google_client_secret.json"
```

Use separate generated token files for Docs and Drive because they request
different scopes:

```text
~/Library/Application Support/zeocore/google_docs_credentials.json
~/Library/Application Support/zeocore/google_drive_credentials.json
```

Do not create either token JSON yourself. ZeoCore creates it after the first
browser consent flow and writes it with mode `600`.

For the existing real Drive demo:

```bash
export ZEOCORE_DRIVE_CLIENT_SECRETS="$HOME/Library/Application Support/zeocore/google_client_secret.json"
export ZEOCORE_DRIVE_CREDENTIALS="$HOME/Library/Application Support/zeocore/google_drive_credentials.json"
export ZEOCORE_DRIVE_FILE_ID="YOUR_REAL_DRIVE_FILE_ID"

cd examples/zeocore-examples/apps/data_cleaning
uv run python run_demo_drive.py
```

The first run opens Google's browser consent flow. Authenticate as the test
user configured above.

### ZeoCore 0.6.0 Google Docs configuration caveat

`GoogleDocsService(client_secrets_file=..., credentials_file=...)` currently
fails its base configuration lookup before those constructor arguments are
consumed. The resource documents this upstream defect. For 0.6.0, the working
shape is a local YAML configuration file passed through `config_path=`. The
YAML contains paths, not credential values:

```yaml
google_docs:
  client_secrets_file: "<fully expanded path>/google_client_secret.json"
  credentials_file: "<fully expanded path>/google_docs_credentials.json"
```

Print the fully expanded directory with:

```bash
python3 -c 'from pathlib import Path; print(Path.home() / "Library/Application Support/zeocore")'
```

Paste that output in place of `<fully expanded path>`. ZeoCore 0.6.0 does not
expand `~` inside these YAML values. Keep the YAML untracked. Do not put the
client secret JSON or generated token inside the repository.

## Bluesky: generate and store an app password

Never use the Bluesky account password.

1. Sign in at [bsky.app](https://bsky.app/).
2. Open **Settings → Privacy and security → App passwords**. Some clients show
   this as **Settings → Advanced → App passwords**.
3. Choose **Add app password**, name it `zeocore-class-demo`, and create it.
4. Copy it once. Treat it as a live credential.

Bluesky's official guidance directs third-party clients to app passwords:
[Bluesky User FAQ](https://bsky.social/about/blog/5-19-2023-user-faq).

ZeoCore 0.6.0 reads the first credential from these environment variables:

```bash
export BLUESKY_IDENTIFIER="YOUR_HANDLE.bsky.social"
export BLUESKY_APP_PASSWORD="YOUR_APP_PASSWORD"
export BLUESKY_SERVICE_URL="https://bsky.social"
```

After successful authentication, ZeoCore stores the identifier and app
password atomically with file mode `600` at:

```text
~/Library/Application Support/zeocore/bluesky/bluesky_credentials.json
```

Do not put the app password in this repository, a committed YAML file, shell
history, slides, screenshots, or pasted logs. The checked-in `.env.example`
documents variable names only; the current demos do not automatically load a
`.env` file.

## Live-service safety boundary

- Acquiring credentials is safe preparation; publishing is a separate operator
  act.
- `run_demo.py` never posts. A real Bluesky `post()` creates a public record and
  must only be invoked deliberately.
- Do not print, log, `repr`, or serialize authentication-result objects. ZeoCore
  0.6.0 has a known disclosure defect in those representation channels; the
  class-critical Sovereign Agent/Ollama/ZeoCore demos do not enter that path.
- After class, revoke the Bluesky app password if it was only for the demo. In
  Google Cloud, delete the cached token locally and revoke the app's access from
  the Google account if the authorization is no longer needed.

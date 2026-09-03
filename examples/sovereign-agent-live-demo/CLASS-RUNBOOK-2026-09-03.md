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

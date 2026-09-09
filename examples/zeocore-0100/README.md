# Zeocore 0.10.0 release labs

```text
Author:        Zeocore Principal, operated by Rod Rivera
Verified on:   2026-09-09
Verified by:   Zeocore Principal, operated by Rod Rivera
Verified with: zeocore 0.10.0 from PyPI, Python 3.14, uv
Audience:      Capability authors and hosts adopting marketing and authoring operations
Time:          15 minutes offline; live account setup is separate
```

Run six local labs using the public package APIs: HubSpot marketing, Kit
marketing, explicit test/production state, native service profiles, a Gemini
request and an authoring build. The smoke checks exact output against independent
expectations and refuses a second build into an existing destination.

Publication status: Zeocore 0.10.0 is available on PyPI. The catalog pin and
committed lock were updated through `make migrate` after checking the production
release. The production wheel and source archive match the qualified release
digests, and the wheel imports successfully in a fresh Python 3.14 environment.

## Run it

From this directory, using Python 3.14 or newer:

```bash
uv sync --frozen
uv run --frozen python src/main.py
```

No account, API key, Ollama, Google SDK or Pandoc binary is needed for that
command. The lock installs Jupytext and the local notebook runtime. Git must be
on PATH for the author's temporary workspace. Notebook cells are trusted
repository fixtures and run in a fresh local Python kernel.

Expected summary:

```text
PASS hubspot_usage.py
PASS kit_usage.py
PASS environment_usage.py
PASS zeoconnect_usage.py
PASS gemini_request.py
PASS authoring conversion, execution and independent fixture checks
PASS existing authoring output refused and unchanged
OFFLINE: no live delivery, provider generation or publication
```

Each of the five named scripts is also independently runnable with
`uv run python src/<name>.py`. They retain the output and public API call shapes
of the upstream release examples. Their synthetic credentials stay within
injected in-memory HTTP transports; they are not real provider credentials.

## Inspect an authoring build

To retain artifacts instead of deleting the smoke's temporary workspace:

```bash
uv run python src/authoring_reference/run.py --state-root .lab-state --mode test --run-id first
```

Read `.lab-state/test/work/first/release.json`, the clean and executed notebooks,
and `roundtrip.md`. The fixture expects `total=10` from `[2, 3, 5]`, verifies a
relative text asset and Unicode prose, and ensures an illustrative `.noeval`
block is not executed. A second run with the same ID fails `OUTPUT_EXISTS`.
Choose a new run ID for a new attempt. Delete only your chosen `.lab-state` run
when finished. No notebook content or artifact is uploaded.

For an optional DOCX review artifact, install the Pandoc binary and append
`--docx` with a fresh run ID. Read the `optional_docx` receipt independently:
optional export failure is visible but does not convert the required notebook
build into a failure. Open the DOCX for human review; structural validation is
not visual approval.

## Test and production accounts

Read [integration account tracks](../../docs/INTEGRATIONS.md) before adapting
these examples for live use. The offline scripts have no live flag: adding an
API key does not switch their transports. A production host must explicitly
construct its real client and provide the relevant authorization.

- HubSpot and Kit: use designated test accounts and opted-in test recipients;
  production uses a distinct account, approved sender, audience and reviewed send.
- Gemini: use a separate Google Cloud project/key for each track and separate
  host Keychain, broker and artifact namespaces. This lab builds a request only.
- Native profiles: a fake fixture is not a paired session. Configure account
  selection and custody explicitly before choosing hosted or governed placement.
- Notebook authoring: no provider key exists; separate roots and approved input
  notebooks form the local test and production tracks.

The authoring CLI accepts `--mode production` with a separate state namespace.
Using that label is not approval to run untrusted cells. The installed inventory
identity and declared lock are recorded; a lock hash alone is not proof that
installed dependencies match it.

## What this does not demonstrate

No live newsletter delivery, subscriber consent audit, paid Gemini generation,
Google pairing, sovereign authority issuance or publication occurs. The marketing
labs exercise real registries and client serialization at a simulated provider
boundary. Notebook execution is for trusted code and is not an OS/network
sandbox. Receipts establish observed local conversion and execution; they do not
establish learning outcomes, complete descendant isolation or human render approval.

## Provenance

The provider examples and authoring reference are adapted from Zeocore's 0.10.0
release examples under its MIT license. They depend on the installed framework;
no framework implementation is vendored. The catalog smoke adds independent
expected stdout and repeat-build refusal checks around those public consumers.

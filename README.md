# Sovereign Agent Resources

**Tutorials, example projects, and reference code for practitioners building governed AI organizations with [Sovereign Agent](https://github.com/profrodai/sovereign-agent) and [ZeoCore](https://pypi.org/project/zeocore/).**

Every resource is a directory you can run in full, study, or copy piece by piece into your own project. Each one is pinned to versions it was verified against, and the pins are kept honest by machinery, not by promises.

---

## Start here

**New to Sovereign Agent.** No account, no API key, no license — the whole loop runs offline:

```bash
uvx sovereign-agent@latest doctor
uvx sovereign-agent@latest demo store --mode simulated --root /tmp/first-shift
```

Then go deeper, in order:

1. [The book](https://github.com/profrodai/sovereign-agent/tree/main/book) — thirteen chapters that build a Zero-Employee Organization from an empty directory, break it on purpose, and repair it. Every code block executes; every output is byte-verified.
2. [`examples/sovereign-agent-live-demo`](examples/sovereign-agent-live-demo) — a **real local LLM** tool-calls a ZeoCore capability and the Sovereign Agent governs the result. `bash setup.sh`, then three `uv run` commands.
3. [`examples/zeocore-examples`](examples/zeocore-examples) — two real applications rebuilt on zeocore: typed tools doing actual work.

**Building something specific.** Open the category catalog that matches your goal: [examples](examples/README.md), [tutorials](tutorials/README.md), [patterns](patterns/README.md).

## What this is

- **Example projects** — complete, clone-and-run demonstrations, not fragments
- **Tutorials** — end-to-end walkthroughs, each self-contained and runnable
- **Reference code** — patterns for recurring problems: governed tools, verification, refusal as a first-class result
- **Workshop material** — slides, exercises, and solutions from live sessions

## What this is not

- **Not the framework.** `sovereign-agent` and `zeocore` live on PyPI and in their own repositories; the executable textbook lives in [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent). This repository is the material *around* them.
- **Not a support channel.** Product issues belong on the product repositories; questions about material here belong in [Discussions](../../discussions/).

---

## Featured resources

| Resource | What you watch happen | Path |
|---|---|---|
| Live governance demo | A real local model proposes a restock; deterministic Python re-validates it against the ledger and **refuses 9999 units** | [`examples/sovereign-agent-live-demo`](examples/sovereign-agent-live-demo) |
| Data cleaning on zeocore | B2B contact/company CSV cleaning as typed tools | [`examples/zeocore-examples/apps/data_cleaning`](examples/zeocore-examples/apps/data_cleaning) |
| Doc → Bluesky pipeline | A document becomes governed social posts | [`examples/zeocore-examples/apps/doc_to_bluesky`](examples/zeocore-examples/apps/doc_to_bluesky) |
| Metrics tracker | Governed metric collection on zeocore | [`examples/zeocore-examples/apps/metrics_tracker`](examples/zeocore-examples/apps/metrics_tracker) |

---

## Repository map

The repository holds two kinds of material under two different promises.

**Maintained catalog** — one shared pin per governed package
(`SOVEREIGN_AGENT_VERSION`, `ZEOCORE_VERSION`), migrated together, expected to
stay green for as long as it is checked in.

| Path | What it holds |
|---|---|
| [`examples/`](examples/README.md) | Complete clone-and-run projects |
| [`tutorials/`](tutorials/README.md) | Step-by-step walkthroughs — accepting contributions |
| [`patterns/`](patterns/README.md) | Small reference implementations of recurring problems — accepting contributions |
| [`snippets/`](snippets/README.md) | Short pieces too small to be a pattern — accepting contributions |
| [`workshops/`](workshops/README.md) | Slides, exercises, and solutions from sessions — accepting contributions |

**Frozen snapshots** — author-pinned, never migrated forward, still required to
be reproducible (a committed `uv.lock`, a name, a date). See [docs/SNAPSHOTS.md](docs/SNAPSHOTS.md).

| Path | What it holds |
|---|---|
| [`community/`](community/README.md) | Resources written by practitioners, credited to their authors — accepting contributions |

---

## Staying current

The pins are governed by tooling, never by hand ([docs/MIGRATING.md](docs/MIGRATING.md)):

```bash
make outdated    # ask PyPI what is new — read-only
make update      # bump both pins to newest, rewrite every project, re-lock
make ci          # install every project for real and prove the pins resolved
```

`make migrate VERSION=x` refuses a version that does not exist on PyPI —
before writing anything. `make status` fails if any project drifts from the
root pins. CI runs the offline gate on every push and asks PyPI weekly whether
the catalog has gone stale.

## Requirements

- [`uv`](https://docs.astral.sh/uv/) — supplies Python and every environment; nothing else to install
- [Ollama](https://ollama.com/download) — only for the live-model demos; everything else runs offline with the deterministic `scripted` provider
- **No API keys, no accounts, no licenses** for the core material

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md); AI agents get the same
contract as a deterministic procedure in [AGENTS.md](AGENTS.md). The short
version: `make new-resource CATEGORY=patterns NAME=my-resource` scaffolds a
directory with a pinned `pyproject.toml` and the required metadata block —
fill it with something a stranger can run, `uv lock`, and pass
`make validate`.

## License

[MIT](LICENSE), unless a resource's own directory states otherwise.

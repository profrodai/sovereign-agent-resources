# Contributing

Thank you for helping grow this catalog. This repository is teaching material
for practitioners building governed AI organizations with
[Sovereign Agent](https://github.com/profrodai/sovereign-agent) and
[ZeoCore](https://pypi.org/project/zeocore/). Contributions are credited by
name on the resources they touch and stay credited.

**Contributing as an AI agent?** Everything below applies to you too, and
[`AGENTS.md`](AGENTS.md) restates it as a deterministic procedure with exact
commands. Human or agent, the bar is identical: material a stranger can run,
whose claims are machine-checked.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Where contributed work goes

Almost everything here is **maintained**: it pins the shared versions in
[`SOVEREIGN_AGENT_VERSION`](SOVEREIGN_AGENT_VERSION) and
[`ZEOCORE_VERSION`](ZEOCORE_VERSION), moves forward with `make migrate`, and is
expected to keep running. A resource pinned to a release the catalog has left
behind is one nobody clones — being current is most of what makes it useful.

You are not signing up for that maintenance by contributing. Migration is the
maintainers' job, and whoever bumps your resource re-verifies it and puts
**their** name on `Verified by:` — never yours on a version you did not test.
`Author:` is yours permanently.

The frozen exception is [`community/`](community/): a dated record credited to
its author, pinned to the versions the author verified, never migrated forward.
Full contract: [`docs/SNAPSHOTS.md`](docs/SNAPSHOTS.md).

## What belongs where

| Folder | Put it here when… |
|---|---|
| [`examples/`](examples/) | You have a **complete, clone-and-run** project others can adapt |
| [`tutorials/`](tutorials/) | You have a **step-by-step walkthrough** with runnable code |
| [`patterns/`](patterns/) | You have a **small, focused** reference for one recurring problem (governed tools, verification, refusal, idempotent replay) |
| [`workshops/`](workshops/) | You have **slides, exercises, and solutions** from a session |
| [`snippets/`](snippets/) | You have something useful that is **too small** to be a pattern |
| [`community/`](community/) | Any of the above, credited to you and frozen at your verified pins — see [community/README.md](community/README.md) |

If you are unsure, open an issue before a large PR. Out-of-scope work is
declined with a pointer to a better home when we can offer one.

---

## The three rules that matter most

1. **One resource per pull request.** A tutorial, an example, a pattern, a
   workshop pack, or a snippet — not a mix.
2. **It has to run.** `uv sync && uv run <entry point>` on a clean machine,
   no keys and no accounts for the core path. State what you verified and
   when in the resource README. A contribution that works only on your
   machine is a maintenance liability.
3. **Say what it does NOT show.** This catalog's whole discipline is honest
   claims. A resource that demonstrates the happy path states plainly which
   failure modes it skips; a demo that fakes something says so.

---

## Step by step

1. **Scaffold.** `make new-resource CATEGORY=patterns NAME=my-resource`
   creates the directory with a pinned `pyproject.toml` and a README skeleton
   carrying the metadata block. (Or copy
   [docs/RESOURCE_TEMPLATE.md](docs/RESOURCE_TEMPLATE.md) by hand.)
2. **Build the material.** Real code, real outputs, honestly labeled.
3. **Pin exactly.** Governed packages use `==` against the root pins
   (`sovereign-agent==<SOVEREIGN_AGENT_VERSION>`, `zeocore==<ZEOCORE_VERSION>`)
   — never `>=`. The scaffolder does this for you.
4. **Lock.** `uv lock` in your resource directory and **commit `uv.lock`**.
   Without it, `uv sync` resolves to something you never ran and your README's
   claim stops being checkable.
5. **Declare a smoke test** (optional but valued): a command CI runs to prove
   your resource behaves, not just installs:
   ```toml
   [tool.sovereign-catalog]
   smoke = "python check_me.py"
   ```
6. **Catalog it.** Add one row to your category's README table.
7. **No secrets.** `.env.example` only; never commit keys. Core paths must
   not require any secret — a resource that demands one for its basic demo
   is treated as a bug (see [SECURITY.md](SECURITY.md)).

### Metadata block (required)

Every resource README opens with:

```text
Author:        Your Name (or: Your Agent Name, operated by Your Name)
Verified on:   YYYY-MM-DD
Verified by:   Name who last verified it runs
Verified with: sovereign-agent X.Y.Z / zeocore X.Y.Z, uv
Audience:      Who this is for (one line)
Time:          Honest estimate to complete or explore
```

Multiple authors are listed on one line, comma-separated. Substantive later
edits add a co-author rather than replacing the original name. AI agents are
credited like anyone else — name the agent and its operator.

`community/` resources add one field, because the folder is not typed by its
path: `Kind: pattern | example | tutorial | workshop | snippet`.

---

## Validating your change

Run this before opening a pull request. It is offline, stdlib-only, and takes
seconds:

```bash
make validate
```

It runs the tooling unit tests, lints the catalog (README + metadata presence,
pin drift, committed locks, path leaks), and fails on drift. CI runs the same
target, so a green `make validate` locally means a green offline gate on the PR.

If you changed a runnable resource, also install and check it for real:

```bash
make check-all KEEP_GOING=1   # installs every project, asserts the pins resolved
```

See [docs/VALIDATION.md](docs/VALIDATION.md) for what each layer enforces.

## Pull request checklist

- [ ] One resource only
- [ ] `make validate` passes
- [ ] README opens with the metadata block
- [ ] Verified on a clean environment; `Verified on` / `Verified with` are current
- [ ] `uv.lock` committed and resolving to the versions the README claims
- [ ] Category README table updated with a new row
- [ ] No secrets, keys, or personal data in the tree
- [ ] What the resource does NOT show is stated where relevant
- [ ] You agree to the [Code of Conduct](CODE_OF_CONDUCT.md)

---

## Review

A maintainer (listed in [MAINTAINERS.md](MAINTAINERS.md)) runs your resource
before merging — the catalog's promise is that everything in it runs, and that
promise is kept by execution, not by trust. Expect concrete feedback tied to
the checklist above, not style opinions.

## Security

Do not report vulnerabilities in public issues. Follow [SECURITY.md](SECURITY.md).

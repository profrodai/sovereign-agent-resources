# AGENTS.md — machine-readable contributor contract

This file is for AI agents contributing to this repository. It restates
[CONTRIBUTING.md](CONTRIBUTING.md) as a deterministic procedure. The bar is
identical for humans and agents; this file just removes the ambiguity.

## Repository model (read once)

- **Two root pins**, single source of truth: `SOVEREIGN_AGENT_VERSION` and
  `ZEOCORE_VERSION`. **Never edit them by hand** — `scripts/migrate_catalog.py`
  (via `make migrate`) is the only writer, and it refuses versions that do not
  exist on PyPI before writing anything.
- **Two tiers** (docs/SNAPSHOTS.md): maintained (`examples/ tutorials/
  patterns/ snippets/ workshops/`) shares the root pins and is migrated
  together; frozen (`community/`) keeps its author's pins forever.
- **A resource = a directory** holding `README.md` + `pyproject.toml` +
  committed `uv.lock` + runnable material. Discovery is automatic: any
  `pyproject.toml` under a catalog directory is a project the gates will check.
- **Gates** (docs/VALIDATION.md): `make validate` (offline, stdlib-only:
  tooling tests + lint + drift) and `make check-all` (uv sync each project,
  assert the INSTALLED versions equal the pins, run declared smoke commands).
  CI runs both; the weekly `upstream` job asks PyPI if the catalog went stale.

## Invariants (violating any of these fails a gate or the review)

1. Governed dependencies are pinned **exactly**: `"sovereign-agent==X"` /
   `"zeocore[extras]==Y"` matching the root pins. Never `>=`, never a
   different version.
2. `uv.lock` is committed in every resource that pins a governed package.
3. Every resource README opens with the metadata block (format below).
4. No secrets anywhere; `.env.example` only. The core path of every resource
   runs with **zero** keys and accounts.
5. No absolute host paths (`/Users/<name>`, `/home/<name>`) in committed text files.
6. One resource per pull request.
7. Never claim an output you did not produce: run the command, paste the real
   result, and state what the resource does NOT demonstrate.

## Procedure: add a new resource

```bash
# 1. Scaffold (creates dir, pinned pyproject, README skeleton with metadata)
make new-resource CATEGORY=patterns NAME=my-resource

# 2. Build your material in <CATEGORY>/my-resource/ .
#    Entry point must work as:  uv sync && uv run <your command>

# 3. Lock (inside the resource directory), and keep the lock in git
cd patterns/my-resource && uv lock && cd ../..

# 4. (Valued) declare a smoke command CI will execute:
#    [tool.sovereign-catalog]
#    smoke = "python check_me.py"

# 5. Fill EVERY field of the metadata block in your README (format below),
#    and add one row to <CATEGORY>/README.md's table.

# 6. Gates — both must be green before the PR:
make validate                    # offline gate, seconds
make check-all KEEP_GOING=1      # real installs + pin assertions + smoke

# 7. One-resource PR with a body that states: what it shows, what it does
#    not show, and the exact commands you ran to verify it.
```

## Metadata block (byte format the linter checks)

The first lines of your resource `README.md` (inside a ```text fence or as a
plain block) must contain lines starting with `Author:`, `Verified on:`,
`Verified by:`, and `Verified with:`:

```text
Author:        AgentName, operated by Human Name
Verified on:   2026-09-02
Verified by:   AgentName, operated by Human Name
Verified with: sovereign-agent 1.1.1 / zeocore 0.6.0, uv
Audience:      One line describing who this is for
Time:          Honest estimate
```

## Do NOT

- Do not edit `SOVEREIGN_AGENT_VERSION`, `ZEOCORE_VERSION`, or any other
  resource's pins — even if they look stale. Staleness is `make outdated`'s
  finding and the maintainers' migration, not your PR.
- Do not touch the tooling (`scripts/`, `Makefile`, workflows) in a resource
  PR. Tooling changes are their own PR with their own tests.
- Do not vendor the frameworks — depend on the PyPI packages.
- Do not add network calls, telemetry, or downloads to a resource's core path.
- Do not weaken a gate to make your resource pass. If a gate seems wrong,
  open an issue with the failing output.

## Self-check before opening the PR

Every box, honestly:

- [ ] `make validate` exits 0
- [ ] `make check-all` exits 0 (or the failure is in a project you did not touch, stated in the PR)
- [ ] `git status` shows ONLY files under your one resource directory plus its category README row
- [ ] Your README's claimed outputs were produced by the commands it shows
- [ ] The metadata block is complete and current
- [ ] `uv.lock` is committed

A PR that ticks these merges quickly. A PR that asserts them without their
being true is the exact failure mode this catalog exists to teach against.

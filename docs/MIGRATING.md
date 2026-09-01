# Migrating the catalog to a new release

This repository pins **one version per governed package** for every maintained
resource. The pins live at the repository root:

- [`SOVEREIGN_AGENT_VERSION`](../SOVEREIGN_AGENT_VERSION) — the `sovereign-agent` pin
- [`ZEOCORE_VERSION`](../ZEOCORE_VERSION) — the `zeocore` pin

Each project still has its own `pyproject.toml` + `uv.lock`; the root tooling
keeps those files and the README metadata in sync.

**Never hand-edit the pin files.** `scripts/migrate_catalog.py` is the only
writer, and it fails closed: a target version is verified to exist on PyPI
*before* anything is written, so a typo cannot break every project at sync time.

## The routine bump

```bash
make outdated    # 1. read-only: current vs newest on PyPI, per package
make update      # 2. bump both pins, rewrite every pyproject + README, uv lock everywhere
make ci          # 3. install every project for real; assert the pins actually resolved
```

## Targeted bumps

```bash
make migrate-dry PACKAGE=sovereign-agent VERSION=1.2.0   # preview, writes nothing
make migrate     PACKAGE=sovereign-agent VERSION=1.2.0   # rewrite + re-lock
make migrate     PACKAGE=zeocore         VERSION=0.7.0
```

## What the guards catch

| Guard | When it fires |
|---|---|
| `make migrate VERSION=x` | Refuses **before writing anything** if `x` is not a release on PyPI. |
| `make status` | Fails if any maintained project's pin drifted from the root pins. |
| `make check-all` | Installs each project and asserts the **installed** version equals the pin — a lockfile's presence is not proof of behavior. |
| CI `upstream` job (weekly) | Asks PyPI whether the catalog has gone stale even though nobody touched the repo. |

## Release lines

There is currently no release-line restriction: the newest stable release of
both packages is the right target, so `make latest` tracks PyPI directly. If a
future release ever splits the catalog (an import rename, an engine that only
ships on a pre-release line), add a `*_VERSION_LINE` file and teach
`migrate_catalog.py` to respect it — rasa-community-resources'
`RASA_PRO_VERSION_LINE` is the worked precedent for exactly that situation.

## Frozen snapshots are never migrated

`community/` resources keep their authors' pins forever. They are validated
against **their own** pins, not the catalog's. See [SNAPSHOTS.md](SNAPSHOTS.md).

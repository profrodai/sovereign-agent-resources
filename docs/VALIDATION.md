# Validation

Cheapest gate first; each layer catches what the previous one cannot.

| Layer | Command | Needs | Catches |
|---|---|---|---|
| Offline gate | `make validate` | stdlib only | tooling regressions, lint findings, pin drift |
| Install gate | `make check-all` | uv, network | locks that don't resolve; pins that install as a DIFFERENT version than claimed |
| Full | `make ci` | uv, network | both of the above, in CI order |

The install gate's version assertion is the anti-hollow check: a project can
carry a plausible-looking lockfile and still resolve to the wrong version —
`check_project.py` reads the version out of the actual installed environment.

The repository has no GitHub Actions workflows: CI does not run on GitHub
(operator direction of 2026-09-25, under R-36). Run `make ci` (or `make verify`)
locally; `make outdated` asks PyPI whether the catalog has gone stale.

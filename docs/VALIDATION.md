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

CI (`.github/workflows/validate.yml`) runs the offline gate on every push and
PR, the install gate on every push, and asks PyPI weekly (`upstream` job)
whether the catalog has silently gone stale.

The fleet `zeo` workflow additionally runs `make verify` in its certify lane
on main; `verify-fast` aliases the offline gate for the fast PR lane.

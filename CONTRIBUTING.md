# Contributing

Two ways in:

**Maintained catalog** (`examples/`, `tutorials/`, `patterns/`, `snippets/`,
`workshops/`) — your resource joins the shared pins and gets migrated forward
with the catalog. You build it once; the tooling keeps it current.

**Community snapshots** (`community/`) — credited to you, frozen at the
versions you verified, never migrated. Right for material tied to a moment.

## The mechanics

1. Follow [docs/RESOURCE_TEMPLATE.md](docs/RESOURCE_TEMPLATE.md).
2. Pin governed packages exactly (`sovereign-agent==<root pin>`); commit `uv.lock`.
3. Run the gates before opening a PR:
   ```bash
   make validate          # offline: lint + drift + tooling tests
   make check-all         # installs everything, asserts the pins resolved
   ```
4. Open a PR. CI runs the same gates; a reviewer runs your resource.

## What gets merged

Material a stranger can run, that states what it does and does not show, and
whose claimed outputs are real. The catalog's whole value is that its promises
are machine-checked — a resource that needs hand-waving does not fit.

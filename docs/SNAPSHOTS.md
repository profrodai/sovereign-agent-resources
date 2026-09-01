# Maintained catalog vs frozen snapshots

Two tiers, two promises:

**Maintained** (`examples/`, `tutorials/`, `patterns/`, `snippets/`,
`workshops/`) — one shared pin per governed package, migrated together by
`make migrate`, expected to stay green for as long as it is checked in.
Contributed work lives here too: an example pinned to a release the catalog
has moved off is one nobody clones.

**Frozen snapshots** (`community/`) — dated records credited to their authors,
pinned to the versions the author verified, never migrated forward. Still
required to be reproducible: a real committed `uv.lock`, an author name, and a
verification date in the resource README.

The tooling enforces the difference: `make migrate` only touches maintained
directories; `make status` only checks maintained projects for drift.

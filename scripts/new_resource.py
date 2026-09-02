#!/usr/bin/env python3
"""Scaffold a new catalog resource with pinned pyproject and README skeleton.

    python scripts/new_resource.py --category patterns --name my-resource
    make new-resource CATEGORY=patterns NAME=my-resource

Creates <category>/<name>/ with:
- pyproject.toml pinned to the CURRENT root pins (exact ==, never >=);
- README.md opening with the required metadata block, every field marked TODO;
- a src/ placeholder.

Refuses: unknown categories, names that are not kebab-case, and existing
directories (never overwrites). Stdlib-only.
"""

from __future__ import annotations

import argparse
import re
import sys

import catalog

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
CATEGORIES = catalog.MAINTAINED_DIRS + catalog.SNAPSHOT_DIRS

PYPROJECT = """\
[project]
name = "{name}"
version = "0.1.0"
description = "TODO: one line — what the reader watches happen"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
    "sovereign-agent=={sa_pin}",
]

# Uncomment if this resource also uses zeocore (keep the exact pin):
# "zeocore=={zc_pin}",

# A command CI runs to prove the resource behaves, not just installs:
# [tool.sovereign-catalog]
# smoke = "python check_me.py"
"""

README = """\
# {title}

```text
Author:        TODO Your Name (or: AgentName, operated by Your Name)
Verified on:   TODO YYYY-MM-DD
Verified by:   TODO Name who last verified it runs
Verified with: sovereign-agent {sa_pin} / zeocore {zc_pin}, uv
Audience:      TODO one line
Time:          TODO honest estimate
```

TODO: One paragraph — what the reader watches happen.

## Run it

```bash
uv sync
uv run python src/main.py   # TODO: your real entry point
```

## What you should observe

TODO: real output, produced by the commands above, pasted honestly.

## What this does NOT show

TODO: name the failure modes and scope this resource deliberately skips.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", choices=sorted(CATEGORIES), required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    if not NAME_RE.match(args.name):
        raise SystemExit(f"REFUSED: name {args.name!r} must be kebab-case (a-z, 0-9, hyphens)")
    target = catalog.ROOT / args.category / args.name
    if target.exists():
        raise SystemExit(f"REFUSED: {target.relative_to(catalog.ROOT)} already exists; never overwriting")

    sa_pin = catalog.read_pin("sovereign-agent")
    zc_pin = catalog.read_pin("zeocore")
    title = args.name.replace("-", " ").title()

    (target / "src").mkdir(parents=True)
    (target / "pyproject.toml").write_text(
        PYPROJECT.format(name=args.name, sa_pin=sa_pin, zc_pin=zc_pin), encoding="utf-8"
    )
    (target / "README.md").write_text(
        README.format(title=title, sa_pin=sa_pin, zc_pin=zc_pin), encoding="utf-8"
    )
    (target / "src" / "main.py").write_text(
        'print("TODO: replace with your resource\'s real entry point")\n', encoding="utf-8"
    )

    rel = target.relative_to(catalog.ROOT)
    print(f"scaffolded {rel}/")
    print("next:")
    print(f"  1. build your material in {rel}/")
    print(f"  2. cd {rel} && uv lock   (commit the lock)")
    print(f"  3. fill every TODO in {rel}/README.md")
    print(f"  4. add a row to {args.category}/README.md")
    print("  5. make validate && make check-all")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Static checks for the resources catalog. Stdlib-only, offline, fast.

    python scripts/lint_repo.py            # human output, exit 1 on findings
    python scripts/lint_repo.py --json     # machine-readable findings
    python scripts/lint_repo.py --strict   # warnings count as findings

Checks:
- every project has README.md alongside pyproject.toml, opening with the
  CONTRIBUTING.md metadata block (Author / Verified on / Verified with);
- every MAINTAINED project's governed pins match the root pin files;
- every maintained project with a governed pin has a committed uv.lock
  (reproducibility is the catalog's promise) — warning until first lock;
- category READMEs (examples/, tutorials/, ...) exist;
- no absolute /Users or /home paths leak into committed files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

import catalog

LEAK_RE = re.compile(r"(/Users/[A-Za-z0-9_.-]+|/home/[A-Za-z0-9_.-]+)")
TEXT_SUFFIXES = {".md", ".py", ".toml", ".yml", ".yaml", ".sh", ".txt", ".json"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    projects = catalog.discover()
    METADATA_LINES = ("Author:", "Verified on:", "Verified with:")
    for p in projects:
        readme = p.path / "README.md"
        if not readme.is_file():
            errors.append(f"{p.rel}: missing README.md")
        else:
            head = readme.read_text(encoding="utf-8")[:1500]
            for field in METADATA_LINES:
                if field not in head:
                    errors.append(
                        f"{p.rel}: README missing metadata line {field!r} "
                        "(see CONTRIBUTING.md metadata block)"
                    )
        if p.tier == "maintained":
            for pkg, (have, want) in p.drift().items():
                errors.append(f"{p.rel}: {pkg}=={have} drifted from root pin {want}")
            if p.pinned_versions() and not (p.path / "uv.lock").is_file():
                warnings.append(f"{p.rel}: no committed uv.lock (run `make lock-all`)")

    for d in catalog.MAINTAINED_DIRS + catalog.SNAPSHOT_DIRS:
        if not (catalog.ROOT / d / "README.md").is_file():
            errors.append(f"{d}/: missing category README.md")

    for path in catalog.ROOT.rglob("*"):
        if (
            path.is_file()
            and path.suffix in TEXT_SUFFIXES
            and ".git" not in path.parts
            and ".venv" not in path.parts
        ):
            if path.name == "lint_repo.py":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            match = LEAK_RE.search(text)
            if match:
                errors.append(
                    f"{path.relative_to(catalog.ROOT)}: absolute path leaks: {match.group(0)}"
                )

    findings = errors + (warnings if args.strict else [])
    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings}, indent=2))
    else:
        for e in errors:
            print(f"ERROR   {e}")
        for w in warnings:
            print(f"WARNING {w}")
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s), {len(projects)} project(s) scanned")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

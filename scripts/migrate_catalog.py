#!/usr/bin/env python3
"""Migrate the maintained catalog to a new governed-package version.

    python scripts/migrate_catalog.py --package sovereign-agent --latest
    python scripts/migrate_catalog.py --package sovereign-agent --version 1.1.1
    python scripts/migrate_catalog.py --package zeocore --version 0.6.0 --dry

Discipline (mirrors rasa-community-resources):
- NEVER hand-edit the root pin files; this script is the only writer.
- A target version is verified to EXIST on PyPI before anything is written —
  a typo'd version fails closed instead of breaking every project at sync time.
- --dry previews every rewrite and writes nothing.
- Lockfile re-resolution is `make lock-all`'s job (needs uv); this script is
  stdlib-only so the offline gate can always reason about pins.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

import catalog


def pypi_versions(package: str) -> list[str]:
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.URLError as error:
        raise SystemExit(f"cannot reach PyPI for {package}: {error}")
    return list(data["releases"].keys()), data["info"]["version"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", choices=sorted(catalog.PIN_FILES), required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--latest", action="store_true", help="target the newest release on PyPI")
    group.add_argument("--version", help="target this exact version (must exist on PyPI)")
    group.add_argument("--outdated", action="store_true", help="report only; write nothing")
    parser.add_argument("--dry", action="store_true", help="preview rewrites, write nothing")
    args = parser.parse_args()

    package = args.package
    current = catalog.read_pin(package)
    releases, newest = pypi_versions(package)

    if args.outdated:
        print(f"{package}: pinned {current}, newest on PyPI {newest}")
        if current == newest:
            print("up to date — nothing to do")
            return 0
        print(f"run: make migrate PACKAGE={package} VERSION={newest}   (or make update)")
        return 0

    target = newest if args.latest else args.version
    if target not in releases:
        raise SystemExit(
            f"REFUSED: {package}=={target} does not exist on PyPI "
            f"(newest is {newest}); nothing was written"
        )

    pattern = catalog.dep_pattern(package)
    changes: list[str] = []
    for project in catalog.maintained():
        text = project.pyproject.read_text(encoding="utf-8")
        new_text, n = pattern.subn(lambda m: f'{m.group(1)}=={target}"', text)
        if n:
            changes.append(f"{project.rel}/pyproject.toml ({n} pin(s))")
            if not args.dry:
                project.pyproject.write_text(new_text, encoding="utf-8")
        # "Verified against" lines in project READMEs move with the pin.
        readme = project.path / "README.md"
        if readme.is_file():
            rtext = readme.read_text(encoding="utf-8")
            new_rtext = rtext.replace(f"{package}=={current}", f"{package}=={target}")
            if new_rtext != rtext:
                changes.append(f"{project.rel}/README.md")
                if not args.dry:
                    readme.write_text(new_rtext, encoding="utf-8")

    pin_file = catalog.PIN_FILES[package]
    changes.append(f"{pin_file.name}: {current} -> {target}")
    if not args.dry:
        pin_file.write_text(target + "\n", encoding="utf-8")

    mode = "DRY RUN — nothing written" if args.dry else "written"
    print(f"migrate {package}: {current} -> {target} ({mode})")
    for c in changes:
        print(f"  - {c}")
    if not args.dry:
        print("\nnext: make lock-all   (re-resolve every uv.lock)")
        print("then: make ci         (install + validate every project)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

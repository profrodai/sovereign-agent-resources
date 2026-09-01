#!/usr/bin/env python3
"""List catalog projects and their pins versus the root pins.

    python scripts/list_projects.py                # table
    python scripts/list_projects.py --paths-only   # for Makefile loops
    python scripts/list_projects.py --scope snapshots --paths-only
    python scripts/list_projects.py --status       # exit 1 on any drift
"""

from __future__ import annotations

import argparse
import sys

import catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths-only", action="store_true")
    parser.add_argument("--scope", choices=["maintained", "snapshots", "all"], default="maintained")
    parser.add_argument("--status", action="store_true", help="exit 1 if any maintained project drifted")
    args = parser.parse_args()

    projects = catalog.discover()
    if args.scope == "maintained":
        projects = [p for p in projects if p.tier == "maintained"]
    elif args.scope == "snapshots":
        projects = [p for p in projects if p.tier == "snapshot"]

    if args.paths_only:
        for p in projects:
            print(p.rel)
        return 0

    pins = {pkg: catalog.read_pin(pkg) for pkg in catalog.PIN_FILES}
    print("Root pins: " + "  ".join(f"{k}=={v}" for k, v in pins.items()))
    print()
    drifted = False
    for p in projects:
        versions = p.pinned_versions()
        drift = p.drift() if p.tier == "maintained" else {}
        flag = "DRIFT" if drift else "ok"
        if drift:
            drifted = True
        pinned = "  ".join(f"{k}=={v}" for k, v in versions.items()) or "(no governed pins)"
        print(f"  [{p.tier:10}] {flag:5} {p.rel:55} {pinned}")
    if args.status and drifted:
        print("\ndrift detected: run `make migrate` to re-align the catalog", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

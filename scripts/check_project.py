#!/usr/bin/env python3
"""Install one project for real and prove the pin is what actually resolved.

    python scripts/check_project.py examples/sovereign-agent-live-demo

Steps (needs uv):
1. `uv sync` in the project directory (creates/uses its .venv);
2. for every governed package the project pins, assert the INSTALLED version
   equals the pin — presence of a lockfile is not proof of behavior;
3. if the project declares a smoke command in
   [tool.sovereign-catalog] smoke = "...", run it and require exit 0.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import catalog


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    project_dir = (catalog.ROOT / sys.argv[1]).resolve()
    pyproject = project_dir / "pyproject.toml"
    if not pyproject.is_file():
        print(f"not a project: {sys.argv[1]}")
        return 2

    sync = run(["uv", "sync"], project_dir)
    if sync.returncode != 0:
        print(sync.stdout + sync.stderr)
        print(f"FAIL {sys.argv[1]}: uv sync failed")
        return 1

    text = pyproject.read_text(encoding="utf-8")
    for package in catalog.PIN_FILES:
        match = catalog.dep_pattern(package).search(text)
        if not match:
            continue
        want = match.group(3)
        shown = run(["uv", "pip", "show", package], project_dir)
        installed = ""
        for line in shown.stdout.splitlines():
            if line.startswith("Version:"):
                installed = line.split(":", 1)[1].strip()
        if installed != want:
            print(f"FAIL {sys.argv[1]}: {package} installed {installed!r} != pinned {want!r}")
            return 1
        print(f"  ok {package}=={installed}")

    smoke_match = re.search(
        r"\[tool\.sovereign-catalog\][^\[]*?smoke\s*=\s*\"([^\"]+)\"", text, re.S
    )
    if smoke_match:
        smoke = smoke_match.group(1)
        result = run(["uv", "run", *smoke.split()], project_dir)
        if result.returncode != 0:
            print(result.stdout[-2000:] + result.stderr[-2000:])
            print(f"FAIL {sys.argv[1]}: smoke command failed: {smoke}")
            return 1
        print(f"  ok smoke: {smoke}")

    print(f"PASS {sys.argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

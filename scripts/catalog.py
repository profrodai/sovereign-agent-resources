"""Shared catalog model for sovereign-agent-resources tooling.

Stdlib-only by design: the offline gate must run on a bare runner with no
dependencies installed. Mirrors the discipline of rasa-community-resources:
one root pin per governed package, discovered projects, exact-pin drift checks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Maintained catalog: one shared pin per package, migrated together.
MAINTAINED_DIRS = ("examples", "tutorials", "patterns", "snippets", "workshops")
# Frozen snapshots: author-pinned, never migrated (see docs/SNAPSHOTS.md).
SNAPSHOT_DIRS = ("community",)

# The governed packages and where each root pin lives.
PIN_FILES = {
    "sovereign-agent": ROOT / "SOVEREIGN_AGENT_VERSION",
    "zeocore": ROOT / "ZEOCORE_VERSION",
}

# Matches `sovereign-agent==1.1.1` or `zeocore[drive]==0.6.0` inside a
# dependency string. Group 1: package, group 2: extras, group 3: version.
_DEP_RE_TEMPLATE = r'("{pkg}(\[[^\]]*\])?)==([0-9][0-9A-Za-z.\-]*)"'


def read_pin(package: str) -> str:
    path = PIN_FILES[package]
    return path.read_text(encoding="utf-8").strip()


def dep_pattern(package: str) -> re.Pattern[str]:
    return re.compile(_DEP_RE_TEMPLATE.format(pkg=re.escape(package)))


@dataclass
class Project:
    path: Path  # directory containing pyproject.toml
    tier: str  # "maintained" | "snapshot"
    root: Path = ROOT

    @property
    def rel(self) -> str:
        return str(self.path.relative_to(self.root))

    @property
    def pyproject(self) -> Path:
        return self.path / "pyproject.toml"

    def pinned_versions(self) -> dict[str, str]:
        """Package -> exact pinned version found in this project's pyproject."""
        text = self.pyproject.read_text(encoding="utf-8")
        found: dict[str, str] = {}
        for package in PIN_FILES:
            match = dep_pattern(package).search(text)
            if match:
                found[package] = match.group(3)
        return found

    def drift(self) -> dict[str, tuple[str, str]]:
        """Package -> (project pin, root pin) for every mismatch."""
        out: dict[str, tuple[str, str]] = {}
        for package, version in self.pinned_versions().items():
            root_pin = read_pin(package)
            if version != root_pin:
                out[package] = (version, root_pin)
        return out


def discover(root: Path = ROOT) -> list[Project]:
    """Every directory holding a pyproject.toml under the catalog dirs.

    A project is the SHALLOWEST pyproject-bearing directory on its branch;
    nested pyprojects (test fixtures etc.) belong to their project.
    """
    projects: list[Project] = []
    for tier, dirs in (("maintained", MAINTAINED_DIRS), ("snapshot", SNAPSHOT_DIRS)):
        for d in dirs:
            base = root / d
            if not base.is_dir():
                continue
            claimed: list[Path] = []
            for pyproject in sorted(base.rglob("pyproject.toml"), key=lambda q: (len(q.parts), str(q))):
                parent = pyproject.parent
                if any(str(parent).startswith(str(c) + "/") for c in claimed):
                    continue
                claimed.append(parent)
                projects.append(Project(path=parent, tier=tier, root=root))
    return projects


def maintained(root: Path = ROOT) -> list[Project]:
    return [p for p in discover(root) if p.tier == "maintained"]

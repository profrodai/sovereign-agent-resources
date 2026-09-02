#!/usr/bin/env python3
"""Unit tests for the catalog tooling. Stdlib unittest; run via `make test-scripts`.

Mutation-shaped: each test is a failure class that must stay closed —
a typo'd version writing anyway, drift passing silently, discovery
claiming nested fixtures as projects.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalog  # noqa: E402


def make_project(base: Path, rel: str, deps: str) -> Path:
    d = base / rel
    d.mkdir(parents=True)
    (d / "pyproject.toml").write_text(
        f'[project]\nname = "x"\nversion = "0"\ndependencies = [\n{deps}\n]\n'
    )
    (d / "README.md").write_text("# x\n")
    return d


class DiscoveryTests(unittest.TestCase):
    def test_discovers_maintained_and_snapshot_tiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root, "examples/a", '    "sovereign-agent==1.1.1",')
            make_project(root, "community/b", '    "sovereign-agent==1.0.0",')
            found = catalog.discover(root)
            tiers = {p.rel: p.tier for p in found}
            self.assertEqual(tiers, {"examples/a": "maintained", "community/b": "snapshot"})

    def test_nested_pyproject_belongs_to_its_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outer = make_project(root, "examples/app", '    "zeocore==0.6.0",')
            inner = outer / "fixtures"
            inner.mkdir()
            (inner / "pyproject.toml").write_text('[project]\nname="fixture"\nversion="0"\n')
            found = catalog.discover(root)
            self.assertEqual([p.rel for p in found], ["examples/app"])


class PinTests(unittest.TestCase):
    def test_extras_pins_are_recognized(self):
        pattern = catalog.dep_pattern("zeocore")
        match = pattern.search('"zeocore[drive]==0.6.0"')
        self.assertIsNotNone(match)
        self.assertEqual(match.group(3), "0.6.0")

    def test_range_dependencies_are_not_pins(self):
        pattern = catalog.dep_pattern("zeocore")
        self.assertIsNone(pattern.search('"zeocore[drive]>=0.1.0"'))

    def test_rewrite_preserves_extras(self):
        pattern = catalog.dep_pattern("zeocore")
        text = 'deps = ["zeocore[drive]==0.5.0", "polars>=1.0.0"]'
        out = pattern.sub(lambda m: f'{m.group(1)}==0.6.0"', text)
        self.assertIn('"zeocore[drive]==0.6.0"', out)
        self.assertIn('"polars>=1.0.0"', out)

    def test_similar_package_names_do_not_match(self):
        # sovereign-agent's pattern must not rewrite sovereign-agent-extras.
        pattern = catalog.dep_pattern("sovereign-agent")
        self.assertIsNone(pattern.search('"sovereign-agent-extras==9.9.9"'))


class ScaffoldTests(unittest.TestCase):
    def test_scaffold_refuses_bad_names_and_existing_dirs(self):
        import subprocess
        script = str(Path(__file__).resolve().parent / "new_resource.py")
        bad = subprocess.run(
            [sys.executable, script, "--category", "patterns", "--name", "Bad_Name"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("kebab-case", bad.stderr)
        exists = subprocess.run(
            [sys.executable, script, "--category", "examples", "--name", "zeocore-examples"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(exists.returncode, 0)
        self.assertIn("never overwriting", exists.stderr)

    def test_scaffold_output_carries_current_pins_and_metadata(self):
        # Render the templates directly against the real pins; no writes.
        import new_resource
        sa = catalog.read_pin("sovereign-agent")
        zc = catalog.read_pin("zeocore")
        pyproject = new_resource.PYPROJECT.format(name="x", sa_pin=sa, zc_pin=zc)
        self.assertIn(f'"sovereign-agent=={sa}"', pyproject)
        readme = new_resource.README.format(title="X", sa_pin=sa, zc_pin=zc)
        for field in ("Author:", "Verified on:", "Verified with:"):
            self.assertIn(field, readme)


class MetadataLintTests(unittest.TestCase):
    def test_every_real_project_readme_carries_the_metadata_block(self):
        for p in catalog.discover():
            head = (p.path / "README.md").read_text(encoding="utf-8")[:1500]
            for field in ("Author:", "Verified on:", "Verified with:"):
                self.assertIn(field, head, f"{p.rel} missing {field}")


class RealCatalogTests(unittest.TestCase):
    def test_real_catalog_has_no_drift(self):
        for p in catalog.maintained():
            self.assertEqual(p.drift(), {}, f"{p.rel} drifted")

    def test_real_pin_files_hold_versions(self):
        for pkg in catalog.PIN_FILES:
            pin = catalog.read_pin(pkg)
            self.assertRegex(pin, r"^[0-9][0-9A-Za-z.\-]*$", pkg)


if __name__ == "__main__":
    unittest.main(verbosity=2)

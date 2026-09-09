"""Run the release labs with synthetic data and independent output expectations."""

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
CASES = {
    "drive_profiles_v1.py": (
        "PASS fake: unchanged business function total=10\n"
        "PASS local: unchanged business function total=10\n"
        "PASS hosted: unchanged business function total=10\n"
        "PASS empty catalog, multiple connections and missing resource refuse without dispatch\n"
        "OFFLINE: local service and hosted transport injected; no account or network\n"
    ),
    "hubspot_usage.py": (
        "Draft created through registered capability: 123\n"
        "HTTP operations: POST, GET, PATCH, GET, POST\n"
        "SIMULATED: no network, no live send, provider delivery unverified\n"
    ),
    "kit_usage.py": (
        "Draft created through registered capability: 57\n"
        "Track the new send object: 58\n"
        "HTTP operations: POST, GET, GET, POST\n"
        "SIMULATED: no network, no live send, provider delivery unverified\n"
    ),
    "environment_usage.py": (
        "test: private state prepared; ambient key excluded\n"
        "production: private state prepared; ambient key excluded\n"
        "LOCAL: no provider request; temporary state removed on exit\n"
    ),
    "zeoconnect_usage.py": "FAKE: selected Drive bytes verified; no credential or network\n",
    "gemini_request.py": (
        "Operation: gemini.generate_reference_image\n"
        "Reference bytes verified: True\n"
        "REQUEST ONLY: no authorization minted; no provider called\n"
    ),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    with TemporaryDirectory(prefix="zeocore-release-labs-") as temporary:
        workspace = Path(temporary)
        environment = {
            "HOME": str(workspace),
            "PATH": os.environ.get("PATH", ""),
            "PYTHONIOENCODING": "utf-8",
            "XDG_CONFIG_HOME": str(workspace / "config"),
        }
        for name, expected in CASES.items():
            result = subprocess.run(
                [sys.executable, str(ROOT / name)], cwd=workspace, env=environment,
                capture_output=True, text=True, timeout=30, check=False,
            )
            require(result.returncode == 0, f"{name}: process failed")
            require(result.stdout == expected and result.stderr == "", f"{name}: unexpected output")
            print(f"PASS {name}")
        command = [
            sys.executable, str(ROOT / "authoring_reference/run.py"),
            "--state-root", str(workspace / "authoring"), "--mode", "test", "--run-id", "lesson",
        ]
        built = subprocess.run(command, cwd=workspace, env=environment,
                               capture_output=True, text=True, timeout=180, check=False)
        require(built.returncode == 0, "authoring build failed")
        releases = list((workspace / "authoring").rglob("release.json"))
        require(len(releases) == 1, "expected one authoring receipt")
        receipt = json.loads(releases[0].read_text())
        require(receipt["status"] == "SUCCEEDED", "authoring receipt failed")
        require(receipt["publication_status"] == "NOT_PUBLISHED", "unexpected publication")
        require(receipt["receipts"]["independent_fixture_checks"] == "PASSED", "fixture failed")
        repeated = subprocess.run(command, cwd=workspace, env=environment,
                                  capture_output=True, text=True, timeout=30, check=False)
        require(repeated.returncode == 1, "existing destination was not refused")
        require('"error": "OUTPUT_EXISTS"' in repeated.stderr, "wrong refusal")
        require(json.loads(releases[0].read_text()) == receipt, "refusal changed receipt")
        print("PASS authoring conversion, execution and independent fixture checks")
        print("PASS existing authoring output refused and unchanged")
        print("OFFLINE: no live delivery, provider generation or publication")


if __name__ == "__main__":
    main()

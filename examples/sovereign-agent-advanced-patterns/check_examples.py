"""Behavioral smoke test: every lesson must produce its named invariant."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "isolation_policy.py": ("outside path: REFUSED", "deny wins: REFUSED"),
    "durable_automation.py": (
        "first check: NO_FIRE, runs=0",
        "second check: SUCCEEDED, runs=1",
    ),
    "recoverable_context.py": ("source rows: 7 -> 7", "summaries=1, user messages=2"),
    "session_incarnations.py": ("incarnation: 1 -> 2", "stale completion: REFUSED"),
    "tool_discovery.py": (
        "dangerous discovery: delete_inventory",
        "dangerous authorization: REFUSED",
    ),
    "hybrid_memory.py": ("private-other visible: False", "semantic status: used"),
}


def main() -> None:
    for lesson, invariants in EXPECTED.items():
        result = subprocess.run(
            [sys.executable, str(ROOT / "src" / lesson)],
            capture_output=True,
            text=True,
            check=True,
        )
        missing = [
            invariant for invariant in invariants if invariant not in result.stdout
        ]
        if missing:
            raise AssertionError(
                f"{lesson} missed {missing!r}; output was {result.stdout!r}"
            )
        print(f"PASS {lesson}: {len(invariants)} invariants")


if __name__ == "__main__":
    main()

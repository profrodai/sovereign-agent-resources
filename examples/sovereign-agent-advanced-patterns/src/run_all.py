"""Run each lesson in a separate process so no example shares hidden state."""

from pathlib import Path
import subprocess
import sys

LESSONS = (
    "isolation_policy.py",
    "durable_automation.py",
    "recoverable_context.py",
    "session_incarnations.py",
    "tool_discovery.py",
    "hybrid_memory.py",
)


def main() -> None:
    root = Path(__file__).resolve().parent
    for lesson in LESSONS:
        result = subprocess.run(
            [sys.executable, str(root / lesson)],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"=== {lesson.removesuffix('.py')} ===")
        print(result.stdout.rstrip())


if __name__ == "__main__":
    main()

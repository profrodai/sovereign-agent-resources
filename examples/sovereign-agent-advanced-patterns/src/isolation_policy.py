"""Authorize each isolation plane independently; deny always wins."""

from pathlib import Path
from tempfile import TemporaryDirectory

from sovereign_agent.errors import Refusal
from sovereign_agent.isolation import IsolationPolicy


def main() -> None:
    with TemporaryDirectory() as scratch:
        root = Path(scratch)
        workspace = root / "workspace"
        workspace.mkdir()
        policy = IsolationPolicy(
            filesystem_roots=(workspace,),
            network_hosts=frozenset({"inventory.example"}),
            credential_names=frozenset({"INVENTORY_TOKEN"}),
            allowed_tools=frozenset({"read_inventory", "delete_inventory"}),
            denied_tools=frozenset({"delete_inventory"}),
        )

        allowed = policy.authorize_path(workspace / "report.txt")
        assert allowed.parent == workspace.resolve()
        print(f"inside path allowed: {allowed.parent == workspace.resolve()}")
        process = next(item for item in policy.explain() if item.plane == "process")
        assert process.verdict == "UNAVAILABLE"
        print(f"process isolation: {process.verdict}")

        outside_refused = False
        try:
            policy.authorize_path(root / "outside.txt")
        except Refusal:
            outside_refused = True
            print("outside path: REFUSED")
        assert outside_refused
        delete_refused = False
        try:
            policy.authorize_tool("delete_inventory")
        except Refusal:
            delete_refused = True
            print("deny wins: REFUSED")
        assert delete_refused


if __name__ == "__main__":
    main()

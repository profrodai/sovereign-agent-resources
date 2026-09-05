"""Discover a relevant tool, then make authorization decide independently."""

from sovereign_agent.errors import Refusal
from sovereign_agent.isolation import IsolationPolicy
from sovereign_agent.tools import Tool, ToolCatalog


def main() -> None:
    catalog = ToolCatalog(
        [
            Tool("read_inventory", "read stock levels", ("stock",)),
            Tool("delete_inventory", "delete stock rows", ("stock",)),
            Tool("send_email", "notify a supplier", ("message",)),
        ]
    )
    policy = IsolationPolicy(
        allowed_tools=frozenset({"read_inventory", "delete_inventory"}),
        denied_tools=frozenset({"delete_inventory"}),
    )
    safe = catalog.discover("read stock", limit=1)
    authorized = catalog.authorize(safe.tools[0], policy)
    assert (
        authorized.name == "read_inventory"
        and safe.total_matches == 2
        and safe.truncated
    )
    print(
        f"safe discovery: {authorized.name}, matches={safe.total_matches}, "
        f"truncated={safe.truncated}"
    )
    dangerous = catalog.discover("delete stock", limit=1).tools[0]
    assert dangerous.name == "delete_inventory"
    print(f"dangerous discovery: {dangerous.name}")
    refused = False
    try:
        catalog.authorize(dangerous, policy)
    except Refusal:
        refused = True
        print("dangerous authorization: REFUSED")
    assert refused


if __name__ == "__main__":
    main()

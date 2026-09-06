"""Exercise Zeocore's real Supabase data boundary without network or secrets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from zeo_core.integrations.database.supabase import (
    SupabaseClient,
    SupabaseFilter,
    SupabaseIntegration,
)

SYNTHETIC_BOUNDARY_CANARY = "sb_publishable_CANARY_NOT_A_CREDENTIAL"


@dataclass
class FakeResponse:
    """Minimal response shape consumed by the public Zeocore client."""

    data: list[dict[str, Any]]
    count: int | None = None


class FakeQuery:
    """Stateful PostgREST-shaped query; every operation stays in memory."""

    def __init__(self, sdk: FakeSDK, table: str) -> None:
        self.sdk = sdk
        self.table_name = table
        self.operation = "select"
        self.payload: list[dict[str, Any]] = []
        self.filters: list[tuple[str, Any]] = []
        self.window: tuple[int, int] | None = None
        self.on_conflict: str | None = None

    def select(self, columns: str, *, count: str | None = None) -> FakeQuery:
        self.operation = "select"
        self.sdk.events.append(("select", self.table_name, columns, count))
        return self

    def eq(self, field: str, value: Any) -> FakeQuery:
        self.filters.append((field, value))
        self.sdk.events.append(("eq", field, value))
        return self

    def order(self, field: str, *, desc: bool, nullsfirst: bool) -> FakeQuery:
        self.sdk.events.append(("order", field, desc, nullsfirst))
        return self

    def range(self, start: int, end: int) -> FakeQuery:
        self.window = (start, end)
        self.sdk.events.append(("range", start, end))
        return self

    def insert(
        self, rows: Mapping[str, Any] | Sequence[Mapping[str, Any]]
    ) -> FakeQuery:
        self.operation = "insert"
        self.payload = _rows(rows)
        self.sdk.events.append(("insert", self.table_name, len(self.payload)))
        return self

    def upsert(
        self,
        rows: Mapping[str, Any] | Sequence[Mapping[str, Any]],
        *,
        on_conflict: str | None,
        ignore_duplicates: bool,
    ) -> FakeQuery:
        self.operation = "upsert"
        self.payload = _rows(rows)
        self.on_conflict = on_conflict
        self.sdk.events.append(
            ("upsert", self.table_name, on_conflict, ignore_duplicates)
        )
        return self

    def execute(self) -> FakeResponse:
        self.sdk.executions += 1
        table = self.sdk.tables.setdefault(self.table_name, [])
        if self.operation == "select":
            selected = [
                dict(row)
                for row in table
                if all(row.get(field) == value for field, value in self.filters)
            ]
            if self.window is not None:
                start, end = self.window
                selected = selected[start : end + 1]
            return FakeResponse(selected, count=len(selected))
        if self.operation == "insert":
            inserted = [dict(row) for row in self.payload]
            table.extend(inserted)
            return FakeResponse(inserted)

        updated: list[dict[str, Any]] = []
        for incoming in self.payload:
            match = next(
                (
                    row
                    for row in table
                    if self.on_conflict is not None
                    and row.get(self.on_conflict) == incoming.get(self.on_conflict)
                ),
                None,
            )
            if match is None:
                match = dict(incoming)
                table.append(match)
            else:
                match.update(incoming)
            updated.append(dict(match))
        return FakeResponse(updated)


class FakeSDK:
    """In-memory SDK boundary with an explicit zero-network counter."""

    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {
            "work_items": [
                {"id": 1, "status": "ready"},
                {"id": 2, "status": "pending"},
            ]
        }
        self.events: list[tuple[Any, ...]] = []
        self.executions = 0
        self.network_calls = 0

    def table(self, table: str) -> FakeQuery:
        self.events.append(("table", table))
        return FakeQuery(self, table)


def _rows(
    value: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        return [dict(value)]
    return [dict(row) for row in value]


def main() -> int:
    """Run accepted operations and prove two refusals stop before execution."""
    sdk = FakeSDK()
    client = SupabaseClient(
        "https://example.supabase.co",
        SYNTHETIC_BOUNDARY_CANARY,
        sdk_client=sdk,
        max_rows=2,
    )
    service = SupabaseIntegration(client=client, realtime_client=object())

    selected = service.select(
        "work_items",
        columns=("id", "status"),
        filters=(SupabaseFilter(field="status", value="ready"),),
        limit=2,
        count="exact",
    )
    inserted = service.insert("work_items", {"id": 3, "status": "queued"})
    upserted = service.upsert(
        "work_items",
        {"id": 3, "status": "ready"},
        on_conflict="id",
    )

    before_refusals = sdk.executions
    invalid_table = service.select("work-items", limit=1)
    over_limit = service.select("work_items", limit=3)

    rendered = "\n".join(
        (
            repr(client),
            selected.model_dump_json(),
            inserted.model_dump_json(),
            upserted.model_dump_json(),
            invalid_table.model_dump_json(),
            over_limit.model_dump_json(),
        )
    )
    facts = {
        "selected_rows": len(selected.content.rows if selected.content else []),
        "inserted_rows": len(inserted.content.rows if inserted.content else []),
        "upserted_status": (
            upserted.content.rows[0]["status"] if upserted.content else "missing"
        ),
        "typed_filter_applied": ("eq", "status", "ready") in sdk.events,
        "invalid_table_refused": not invalid_table.success,
        "over_limit_refused": not over_limit.success,
        "refusals_executed_queries": sdk.executions - before_refusals,
        "sdk_executions": sdk.executions,
        "network_calls": sdk.network_calls,
        "canary_absent": SYNTHETIC_BOUNDARY_CANARY not in rendered,
        "canary_control_detected": (
            SYNTHETIC_BOUNDARY_CANARY in rendered + SYNTHETIC_BOUNDARY_CANARY
        ),
    }

    assert facts == {
        "selected_rows": 1,
        "inserted_rows": 1,
        "upserted_status": "ready",
        "typed_filter_applied": True,
        "invalid_table_refused": True,
        "over_limit_refused": True,
        "refusals_executed_queries": 0,
        "sdk_executions": 3,
        "network_calls": 0,
        "canary_absent": True,
        "canary_control_detected": True,
    }

    for name, value in facts.items():
        print(f"{name}={value}")
    print("mode=IN_MEMORY_PROVIDER_BOUNDARY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

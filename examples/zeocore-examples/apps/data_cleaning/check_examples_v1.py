"""Check independently counted CSV fixtures through the real cleaning tools."""

import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from run_demo import APP_DIR, build_ctx
from data_cleaning.pipeline_tools import (
    CleanAccountsRequest, CleanAccountsTool, CleanContactsRequest, CleanContactsTool,
)


def main() -> None:
    with TemporaryDirectory(prefix="cleaning-check-") as temporary:
        root = Path(temporary)
        for name, tool, request_type, counts in (
            ("contacts", CleanContactsTool(), CleanContactsRequest, (15, 2, 2, 11)),
            ("accounts", CleanAccountsTool(), CleanAccountsRequest, (14, 1, 2, 11)),
        ):
            output = root / f"{name}.csv"
            result = tool.run(request_type(
                input_path=str(APP_DIR / "data" / f"{name}_messy.csv"),
                output_path=str(output),
            ), build_ctx(name, root))
            if result.data is None:
                raise RuntimeError(f"{name}: no successful result")
            stats = result.data
            observed = (stats.original_count, stats.invalid_filtered,
                        stats.duplicates_removed, stats.final_count)
            if observed != counts:
                raise RuntimeError(f"{name}: fixture counts differ")
            with output.open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            if len(rows) != 11:
                raise RuntimeError(f"{name}: actual CSV row count differs")
            if name == "contacts":
                emails = [row["email"] for row in rows]
                if len(set(emails)) != 11 or any(email != email.lower() for email in emails):
                    raise RuntimeError("contact normalization or deduplication failed")
                if "test@example.com" in emails:
                    raise RuntimeError("junk contact survived")
            print(f"PASS {name}: {counts[0]} inputs, 11 actual output rows")
    print("OFFLINE: synthetic CSVs checked; temporary outputs removed")


if __name__ == "__main__":
    main()

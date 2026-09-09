"""Check metric arithmetic, persisted rows and refusal before writes."""

import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import ValidationError
from zeo_core.tools import ToolContext
from metrics_tracker.submit_tool import SubmitWeeklyMetricsTool, WeeklyMetricsRequest
from metrics_tracker.storage import fetch_all_weeks


def main() -> None:
    with TemporaryDirectory(prefix="metrics-check-") as temporary:
        database = str(Path(temporary) / "metrics.db")
        tool = SubmitWeeklyMetricsTool(db_path=database)
        ctx = ToolContext(run_id="check", tool_name=tool.name, tool_version="1.0.0",
                          logger=logging.getLogger("check"), fs=None,
                          work_dir=temporary, output_dir=temporary)
        common = dict(active_clients=4, revenue_ratio_to_baseline=1.0,
                      recurring_revenue_percentage=20.0,
                      what_i_automated_this_week="Synthetic check",
                      biggest_bottleneck_now="Synthetic check")
        for week, hours, expected in (
            (1, 40.0, (30.0, 25.0, 0.0, 1.0, 1.0)),
            (2, 20.0, (10.0, 50.0, 20.0, 2.0, 2.0)),
        ):
            result = tool.run(WeeklyMetricsRequest(
                week_number=week, total_hours_worked=hours, automated_hours=10.0,
                **common,
            ), ctx)
            if result.data is None:
                raise RuntimeError("metrics submission failed")
            data = result.data
            observed = (data.manual_hours, data.automation_index,
                        data.time_saved_vs_baseline, data.revenue_efficiency_multiple,
                        data.client_capacity_score)
            if observed != expected:
                raise RuntimeError("independent metric expectation failed")
        before = fetch_all_weeks(database)
        if [row["week_number"] for row in before] != [1, 2]:
            raise RuntimeError("actual stored weeks differ")
        for hours, automated in ((0.0, 0.0), (10.0, 50.0)):
            try:
                WeeklyMetricsRequest(week_number=3, total_hours_worked=hours,
                                     automated_hours=automated, **common)
            except ValidationError:
                pass
            else:
                raise RuntimeError("invalid metrics were accepted")
        if fetch_all_weeks(database) != before:
            raise RuntimeError("refused requests changed persisted rows")
        print("PASS metrics: two computed and persisted weeks")
        print("PASS refusals: zero hours and excess automation; database unchanged")
    print("OFFLINE: temporary database removed")


if __name__ == "__main__":
    main()

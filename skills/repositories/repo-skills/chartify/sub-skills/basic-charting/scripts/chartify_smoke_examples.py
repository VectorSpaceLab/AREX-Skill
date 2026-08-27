#!/usr/bin/env python3
"""Safe tiny Chartify smoke examples for the basic-charting sub-skill.

The script constructs small charts from pandas DataFrames, never calls
``show()``, performs no network access, and optionally saves HTML files to a
user-supplied directory. It is intended to validate basic Chartify usage and
provide copyable minimal patterns.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, Tuple


pd = None
chartify = None


def ensure_dependencies():
    """Import runtime dependencies only when a chart case is executed."""
    global pd, chartify
    if pd is not None and chartify is not None:
        return pd, chartify
    try:
        import pandas as _pd  # type: ignore
        import chartify as _chartify  # type: ignore
    except ImportError as exc:  # pragma: no cover - exercised by missing envs
        print(
            "ERROR: Could not import chartify and pandas. Install Chartify in "
            "the active Python environment (for example, `pip install chartify`) "
            "and retry. Original import error: {}".format(exc),
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    pd, chartify = _pd, _chartify
    return pd, chartify


ChartCase = Callable[[], Tuple[object, str]]


def _source_count(chart: object) -> int:
    data = getattr(chart, "data")
    return len(data)


def _safe_filename(case_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", case_id).strip("._") or "chart"


def case_numeric_line() -> Tuple[object, str]:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-01-01", "2024-02-01", "2024-03-01"] * 2
            ),
            "segment": ["A", "A", "A", "B", "B", "B"],
            "value": [10, 13, 15, 7, 9, 12],
        }
    ).sort_values("date")

    ch = chartify.Chart(blank_labels=True, x_axis_type="datetime", y_axis_type="linear")
    ch.plot.line(df, x_column="date", y_column="value", color_column="segment")
    ch.set_title("Numeric/datetime line")
    ch.set_subtitle("Grouped by segment")
    ch.set_legend_location("outside_bottom")
    return ch, "datetime line with color grouping"


def case_categorical_bar() -> Tuple[object, str]:
    pivoted = pd.DataFrame(
        {
            "fruit": ["Apple", "Banana"],
            "US": [12, 9],
            "CA": [7, 4],
        }
    )
    tidy = pd.melt(pivoted, id_vars="fruit", var_name="country", value_name="quantity")

    ch = chartify.Chart(blank_labels=True, x_axis_type="categorical")
    ch.plot.bar(
        tidy,
        categorical_columns=["fruit", "country"],
        numeric_column="quantity",
        color_column="country",
        categorical_order_by="labels",
        categorical_order_ascending=True,
    )
    ch.set_title("Grouped categorical bar")
    ch.set_legend_location("outside_bottom")
    return ch, "pivoted sales table melted to grouped categorical bar"


def case_heatmap() -> Tuple[object, str]:
    df = pd.DataFrame(
        {
            "fruit": ["Apple", "Apple", "Banana", "Banana"],
            "country": ["US", "CA", "US", "CA"],
            "avg_price": [1.2, 1.0, 0.6, 0.7],
        }
    )

    ch = chartify.Chart(blank_labels=True, x_axis_type="categorical", y_axis_type="categorical")
    ch.plot.heatmap(
        df,
        x_column="fruit",
        y_column="country",
        color_column="avg_price",
        text_column="avg_price",
        text_color="white",
    )
    ch.set_title("Categorical heatmap")
    return ch, "categorical/categorical heatmap with numeric color values"


def case_density_histogram() -> Tuple[object, str]:
    df = pd.DataFrame(
        {
            "score": [1.1, 1.2, 1.5, 1.9, 2.2, 2.4, 2.8, 3.1],
            "cohort": ["A", "A", "B", "B", "A", "B", "A", "B"],
        }
    )

    ch = chartify.Chart(blank_labels=True, y_axis_type="density")
    ch.plot.histogram(df, values_column="score", color_column="cohort", bins=3, method="count")
    ch.set_title("Density histogram")
    ch.set_legend_location("outside_bottom")
    return ch, "density-axis histogram with color grouping"


def case_hexbin() -> Tuple[object, str]:
    df = pd.DataFrame(
        {
            "x": [0.1, 0.2, 0.25, 0.8, 0.9, 1.4, 1.5, 1.6],
            "y": [0.2, 0.3, 0.35, 0.7, 0.8, 1.2, 1.3, 1.35],
        }
    )

    ch = chartify.Chart(blank_labels=True, x_axis_type="density", y_axis_type="density")
    ch.plot.hexbin(df, x_values_column="x", y_values_column="y", size=0.5)
    ch.set_title("2D density hexbin")
    return ch, "density/density hexbin with tiny 2D points"


def case_radar_area() -> Tuple[object, str]:
    metric_order = ["speed", "quality", "cost", "reliability"]
    df = pd.DataFrame(
        {
            "metric": metric_order * 2,
            "model": ["baseline"] * 4 + ["candidate"] * 4,
            "score": [0.6, 0.8, 0.5, 0.7, 0.7, 0.9, 0.4, 0.8],
        }
    )
    df["metric"] = pd.Categorical(df["metric"], categories=metric_order, ordered=True)
    df = df.sort_values(["model", "metric"])

    ch = chartify.RadarChart(blank_labels=True, layout="slide_50%")
    ch.plot.area(df, radius_column="score", color_column="model", alpha=0.25)
    ch.plot.perimeter(df, radius_column="score", color_column="model", line_width=2)
    ch.set_title("Radar area")
    ch.set_legend_location("outside_bottom")
    return ch, "radar area/perimeter from ordered metric rows"


def case_second_axis() -> Tuple[object, str]:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "orders": [100, 120, 150],
            "revenue": [10_000, 13_000, 18_000],
        }
    )

    ch = chartify.Chart(
        blank_labels=True,
        x_axis_type="datetime",
        y_axis_type="linear",
        second_y_axis=True,
    )
    ch.plot.line(df, x_column="date", y_column="orders")
    ch.axes.set_yaxis_label("Orders")
    ch.second_axis.plot.line(
        df,
        x_column="date",
        y_column="revenue",
        line_dash="dashed",
    )
    ch.second_axis.axes.set_yaxis_label("Revenue")
    ch.set_title("Second y-axis")
    return ch, "numeric second y-axis with HTML-safe output path"


CASES: Dict[str, ChartCase] = {
    "numeric-line": case_numeric_line,
    "categorical-bar": case_categorical_bar,
    "heatmap": case_heatmap,
    "density-histogram": case_density_histogram,
    "hexbin": case_hexbin,
    "radar-area": case_radar_area,
    "second-axis": case_second_axis,
}


def iter_requested_cases(requested: Iterable[str]) -> Iterable[str]:
    for case_id in requested:
        if case_id == "all":
            yield from CASES.keys()
        else:
            yield case_id


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construct safe tiny Chartify smoke examples without calling show()."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available case ids and exit unless --case is also provided.",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Case id to run. Repeat for multiple cases, or use 'all'. Defaults to all when omitted.",
    )
    parser.add_argument(
        "--save-html",
        metavar="DIR",
        type=Path,
        help="Optional directory where each constructed chart is saved as an HTML file.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.list:
        print("Available cases:")
        for case_id in CASES:
            print(f"  {case_id}")
        if not args.case:
            return 0

    requested = list(iter_requested_cases(args.case or ["all"]))
    unknown = [case_id for case_id in requested if case_id not in CASES]
    if unknown:
        print(
            "ERROR: Unknown case(s): {}. Valid cases: {}".format(
                ", ".join(unknown), ", ".join(CASES.keys())
            ),
            file=sys.stderr,
        )
        return 2

    ensure_dependencies()

    if args.save_html is not None:
        args.save_html.mkdir(parents=True, exist_ok=True)

    for case_id in requested:
        chart, note = CASES[case_id]()
        sources = _source_count(chart)
        if sources <= 0:
            print(f"ERROR {case_id}: chart constructed but no data sources were found", file=sys.stderr)
            return 1

        saved = ""
        if args.save_html is not None:
            filename = args.save_html / f"{_safe_filename(case_id)}.html"
            chart.save(str(filename), format="html")
            saved = f" saved={filename}"

        print(f"PASS {case_id}: {note}; data_sources={sources}{saved}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Quick runtime checks for an installed Chartify package.

Examples:
  python check_chartify_runtime.py
  python check_chartify_runtime.py --check-html-save
  python check_chartify_runtime.py --probe-browser

This helper imports the installed package, constructs small charts, and avoids
network access or notebook display.
"""
from __future__ import annotations

import argparse
import inspect
import os
from pathlib import Path
import shutil
import sys
import tempfile


def import_chartify():
    try:
        import pandas as pd  # type: ignore
        import chartify  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on caller env
        print("ERROR: failed to import chartify and pandas.", file=sys.stderr)
        print("Install Chartify in the active environment, for example: pip install chartify", file=sys.stderr)
        print(f"Import detail: {exc}", file=sys.stderr)
        raise SystemExit(1)
    return chartify, pd


def smoke_chart(chartify, pd, save_html: bool) -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "value": [1, 3, 2],
        }
    )
    ch = chartify.Chart(blank_labels=True, x_axis_type="datetime")
    ch.plot.line(df, "date", "value")
    ch.set_title("Chartify runtime smoke")
    if not ch.data or "value" not in ch.data[0]:
        raise RuntimeError("chart constructed but expected ColumnDataSource data was not found")
    print(f"chart-smoke: PASS data_sources={len(ch.data)}")

    if save_html:
        out = Path(tempfile.gettempdir()) / "chartify_runtime_smoke.html"
        ch.save(str(out), format="html")
        print(f"html-save: PASS path={out} bytes={out.stat().st_size}")


def inspect_api(chartify) -> None:
    print(f"chartify-version: {getattr(chartify, '__version__', 'unknown')}")
    print(f"Chart-signature: {inspect.signature(chartify.Chart)}")
    print(f"RadarChart-signature: {inspect.signature(chartify.RadarChart)}")
    ch = chartify.Chart(blank_labels=True)
    print("default-plot-class:", type(ch.plot).__name__)
    print("default-axes-class:", type(ch.axes).__name__)
    methods = sorted(name for name in dir(ch.plot) if not name.startswith("_") and callable(getattr(ch.plot, name)))
    print("default-plot-methods:", ",".join(methods))


def probe_browser() -> None:
    names = ["google-chrome", "chromium", "chromium-browser", "chrome", "chromedriver"]
    found = []
    for name in names:
        path = shutil.which(name)
        if path:
            found.append(f"{name}={path}")
    if found:
        print("browser-probe: FOUND " + "; ".join(found))
    else:
        print("browser-probe: NOT_FOUND compatible browser/driver command not found on PATH")
        print("browser-probe-note: HTML output can still work; PNG/SVG export needs Selenium plus a compatible browser driver.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-check an installed Chartify runtime.")
    parser.add_argument("--check-html-save", action="store_true", help="Save a tiny chart to an HTML file in the temp directory.")
    parser.add_argument("--probe-browser", action="store_true", help="Probe common browser and chromedriver commands for PNG/SVG export readiness.")
    args = parser.parse_args(argv)

    chartify, pd = import_chartify()
    inspect_api(chartify)
    smoke_chart(chartify, pd, save_html=args.check_html_save)
    if args.probe_browser:
        probe_browser()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check that a Python environment can import and diagnose Lux.

This helper is safe to run from any directory after `lux-api` is installed. It
performs import/version checks, runs `lux.debug_info(return_string=True)`, and
optionally requires that the Jupyter widget appears enabled according to Lux's
own diagnostics. It does not read repository files, download data, start
services, or mutate Jupyter configuration.
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import metadata
from typing import Any, Dict, List, Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check Lux package imports and diagnostics.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    parser.add_argument(
        "--require-widget",
        action="store_true",
        help="Fail if Lux diagnostics do not report an enabled notebook or lab widget.",
    )
    return parser


def dist_version(name: str) -> Optional[str]:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        import lux
        import pandas as pd
        import altair
        import matplotlib
        import luxwidget
        from lux.vis.Vis import Vis  # noqa: F401
        from lux.vis.VisList import VisList  # noqa: F401
        from lux.vis.Clause import Clause  # noqa: F401
        from lux.core.frame import LuxDataFrame  # noqa: F401
        from lux.core.sqltable import LuxSQLTable  # noqa: F401
    except Exception as exc:  # pragma: no cover - intentionally broad diagnostic boundary
        print(f"Lux import check failed: {exc}", file=sys.stderr)
        return 2

    debug_text = lux.debug_info(return_string=True) or ""
    dataframe_patched = pd.DataFrame.__module__.startswith("lux.")
    widget_enabled_signal = "OK" in debug_text and "luxwidget" in debug_text

    result: Dict[str, Any] = {
        "ok": True,
        "python": sys.version.split()[0],
        "versions": {
            "lux-api": dist_version("lux-api"),
            "lux": getattr(lux, "__version__", None),
            "pandas": getattr(pd, "__version__", None),
            "altair": getattr(altair, "__version__", None),
            "matplotlib": getattr(matplotlib, "__version__", None),
            "lux-widget": dist_version("lux-widget") or getattr(luxwidget, "__version__", None),
        },
        "pandas_dataframe_patched_by_lux": dataframe_patched,
        "debug_info_contains_luxwidget": "luxwidget" in debug_text,
        "widget_enabled_signal": widget_enabled_signal,
    }

    if not dataframe_patched:
        result["ok"] = False
        result["error"] = "pandas.DataFrame was not patched by Lux; import lux before creating/loading dataframes."
    if args.require_widget and not widget_enabled_signal:
        result["ok"] = False
        result["error"] = "Lux diagnostics did not report an enabled Jupyter widget."

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "passed" if result["ok"] else "failed"
        print(f"Lux environment check {status}")
        for key, value in result["versions"].items():
            print(f"- {key}: {value}")
        print(f"- pandas.DataFrame patched by Lux: {dataframe_patched}")
        print(f"- debug_info mentions luxwidget: {'luxwidget' in debug_text}")
        if args.require_widget:
            print(f"- widget enabled signal: {widget_enabled_signal}")
        if not result["ok"]:
            print(result.get("error", "unknown failure"), file=sys.stderr)

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

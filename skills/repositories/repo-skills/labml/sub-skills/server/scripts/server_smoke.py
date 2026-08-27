#!/usr/bin/env python3
"""Inspect app-server analysis code without claiming to run the real server.

This is a **stub-based analysis smoke test**: it injects minimal settings
modules, never starts FastAPI/uvicorn, and never connects to MongoDB. A zero
exit status means only that the selected analysis objects worked under those
stubs; it is not a server health or deployment check.

Examples:
    python scripts/server_smoke.py
    python scripts/server_smoke.py --require-server-prereqs
"""

from __future__ import annotations

import argparse
import os
import sys
import types
from pathlib import Path

import numpy as np


def _install_lightweight_settings_stubs() -> None:
    """Install minimal settings modules for source-checkout inspection only."""
    if "labml_app.settings" not in sys.modules:
        settings = types.ModuleType("labml_app.settings")
        settings.PORT = "5005"
        settings.SERVER_URL = "http://localhost:5005"
        settings.WEB_URL = "http://localhost:5005"
        settings.SLACK_BOT_TOKEN = ""
        settings.SLACK_CHANNEL = ""
        settings.SENTRY_DSN = ""
        settings.FLOAT_PROJECT_TOKEN = "float"
        settings.SAMPLES_PROJECT_TOKEN = "samples"
        settings.LABML_VERSION = "0"
        settings.IS_LOCAL_SETUP = True
        settings.INDICATOR_LIMIT = 100
        settings.IS_DEBUG = False
        settings.LOG_CHAR_LIMIT = 3000
        settings.APP_API_VERSION = 0.1
        settings.DB_NAME = "labml"
        sys.modules["labml_app.settings"] = settings

    if "labml_app.analyses_settings" not in sys.modules:
        analyses_settings = types.ModuleType("labml_app.analyses_settings")
        analyses_settings.experiment_analyses = []
        analyses_settings.computer_analyses = []
        analyses_settings.INDICATORS_LIMIT = 100
        sys.modules["labml_app.analyses_settings"] = analyses_settings


def _static_candidates(package_root: Path):
    app_path = package_root.parent.parent
    return [app_path / "static", package_root.parent / "static", package_root / "static"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a stub-only LabML app analysis smoke test.")
    parser.add_argument(
        "--require-server-prereqs",
        action="store_true",
        help="Fail if real settings modules or static frontend assets are absent.",
    )
    args = parser.parse_args()

    print("SERVER_SMOKE_MODE=STUB_ANALYSIS_ONLY")
    print("REAL_SERVER=NOT_STARTED; MONGODB=NOT_CHECKED")
    import labml_app

    package_root = Path(os.path.dirname(os.path.abspath(labml_app.__file__)))
    settings_found = (package_root / "settings.py").is_file() and (
        package_root / "analyses_settings.py"
    ).is_file()
    _install_lightweight_settings_stubs()
    from labml_app.analyses.logs import LogPage
    from labml_app.analyses.series import Series

    static = [p for p in _static_candidates(package_root) if p.is_dir()]

    s = Series(max_buffer_length=4)
    s.update([1, 2, 3, 4, 5, 6], [1.0, np.nan, 3.0, 4.0, 5.0, 6.0])
    data = s.to_data()
    print(f"series_len={len(s)}")
    print(f"series_step_gap={data['step_gap']}")
    print(f"series_last={s.last_value}")

    lp = LogPage()
    lp.logs = ""
    lp.logs_unmerged = ""
    lp.update_logs("a\\rb\\ncd")
    print(f"log_data={lp.get_data()['logs']!r}")

    print(f"package_root={package_root}")
    print(f"real_settings_found={settings_found}")
    print(f"static_found={bool(static)}")
    for p in static:
        print(f"static_candidate={p}")

    if not settings_found:
        print(
            "server_prereq: FAIL settings missing; copy settings.sample.py and "
            "analyses_settings.sample.py, then configure both modules"
        )
    if not static:
        print(
            "server_prereq: FAIL static missing; run app/ui `npm install && npm run build` "
            "or install a wheel containing static assets"
        )
    print("STUB_RESULT=ANALYSIS_CHECK_ONLY; NOT_A_REAL_SERVER_PASS")

    if args.require_server_prereqs and (not settings_found or not static):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

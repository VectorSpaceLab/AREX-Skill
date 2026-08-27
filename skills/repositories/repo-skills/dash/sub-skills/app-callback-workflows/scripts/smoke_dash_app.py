#!/usr/bin/env python3
"""No-browser Dash app/layout/callback smoke check.

Examples:
    python smoke_dash_app.py --mode layout
    python smoke_dash_app.py --mode callback --json
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def run_smoke(mode: str) -> dict[str, Any]:
    import dash
    from dash import Dash, html, dcc, Input, Output

    app = Dash(__name__)
    app.layout = html.Div([
        html.H2("Smoke"),
        dcc.Input(id="input", value="dash"),
        html.Div(id="output"),
    ])
    layout_json = app.layout.to_plotly_json()
    result: dict[str, Any] = {
        "dash_version": dash.__version__,
        "layout_type": layout_json.get("type"),
        "layout_namespace": layout_json.get("namespace"),
        "callback_count": len(app.callback_map),
    }

    if mode == "callback":
        @app.callback(Output("output", "children"), Input("input", "value"))
        def update(value: str | None) -> str:
            return (value or "").upper()

        result["callback_count"] = len(app.callback_map)
        result["callback_result"] = update("ok")
        result["callback_ids"] = sorted(app.callback_map.keys())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a tiny Dash layout and optional callback without starting a server.")
    parser.add_argument("--mode", choices=["layout", "callback"], default="layout", help="Which smoke path to run.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    args = parser.parse_args()
    result = run_smoke(args.mode)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    if args.mode == "callback" and result.get("callback_result") != "OK":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

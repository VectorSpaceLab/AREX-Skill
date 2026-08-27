#!/usr/bin/env python3
"""No-browser Dash pages registration smoke check.

The script clears Dash's page registry for this process, registers two small
pages, creates a Dash app using pages, and prints route metadata. It does not
start a server or open a browser.

Examples:
    python smoke_pages_app.py
    python smoke_pages_app.py --json
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def run_smoke() -> dict[str, Any]:
    import dash
    from dash import Dash, html, dcc, page_container
    from dash import _pages  # public app code uses dash.page_registry; this helper resets process-local state.

    _pages.PAGE_REGISTRY.clear()
    app = Dash(__name__, use_pages=True, pages_folder="")

    dash.register_page(
        "smoke_home",
        path="/",
        layout=html.Div("Home", id="home-content"),
        title="Smoke Home",
        description="Home page smoke",
    )
    dash.register_page(
        "smoke_report",
        path_template="/report/<year>",
        layout=lambda year=None, **kwargs: html.Div(f"Report {year}", id="report-content"),
        title="Smoke Report",
    )

    app.layout = html.Div([dcc.Link("Home", href="/"), page_container])
    pages = [
        {
            "module": page["module"],
            "path": page["path"],
            "name": page["name"],
            "title": page["title"],
            "has_layout": page.get("layout") is not None,
        }
        for page in dash.page_registry.values()
    ]
    return {"page_count": len(pages), "pages": pages}


def main() -> int:
    parser = argparse.ArgumentParser(description="Register tiny Dash pages and print page metadata without a browser.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    args = parser.parse_args()
    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"page_count: {result['page_count']}")
        for page in result["pages"]:
            print(f"- {page['module']}: {page['path']} ({page['title']})")
    return 0 if result["page_count"] == 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())

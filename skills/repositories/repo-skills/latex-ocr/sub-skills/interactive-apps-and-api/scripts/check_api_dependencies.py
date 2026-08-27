#!/usr/bin/env python3
"""Check pix2tex API optional dependencies without starting a server."""
from __future__ import annotations

import argparse
import importlib
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Check pix2tex API imports and routes")
    parser.add_argument("--include-streamlit", action="store_true", help="also import streamlit frontend dependencies")
    args = parser.parse_args()

    modules = ["fastapi", "uvicorn", "python_multipart", "pix2tex.api.app"]
    if args.include_streamlit:
        modules += ["streamlit", "st_img_pastebutton", "pix2tex.api.streamlit"]
    report = {"python": sys.version, "imports": [], "routes": []}
    for name in modules:
        try:
            importlib.import_module(name)
            report["imports"].append({"name": name, "ok": True, "error": None})
        except Exception as exc:  # noqa: BLE001
            report["imports"].append({"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    try:
        from pix2tex.api.app import app

        report["routes"] = sorted({route.path for route in app.routes})
        report["title"] = app.title
    except Exception as exc:  # noqa: BLE001
        report["app_error"] = f"{type(exc).__name__}: {exc}"

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(item["ok"] for item in report["imports"]) and not report.get("app_error") else 1


if __name__ == "__main__":
    raise SystemExit(main())

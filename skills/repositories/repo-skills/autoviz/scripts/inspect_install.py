#!/usr/bin/env python3
"""Inspect an AutoViz runtime without relying on a source checkout.

Usage:
  python inspect_install.py
"""

from __future__ import annotations

import importlib
import json
from importlib import metadata

PACKAGES = [
    "autoviz",
    "pandas",
    "pandas-dq",
    "xgboost",
    "hvplot",
    "holoviews",
    "panel",
    "bokeh",
    "wordcloud",
    "nltk",
    "IPython",
]

IMPORTS = [
    "autoviz",
    "autoviz.AutoViz_Class",
    "autoviz.AutoViz_Holo",
    "autoviz.AutoViz_NLP",
    "autoviz.AutoViz_Utils",
]


def dist_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def import_status(name: str) -> str:
    try:
        importlib.import_module(name)
        return "ok"
    except Exception as exc:  # pragma: no cover - diagnostic script
        return f"failed: {type(exc).__name__}: {exc}"


def main() -> int:
    result = {
        "versions": {name: dist_version(name) for name in PACKAGES},
        "imports": {name: import_status(name) for name in IMPORTS},
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(status == "ok" for status in result["imports"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

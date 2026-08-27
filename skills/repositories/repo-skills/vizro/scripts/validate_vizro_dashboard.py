#!/usr/bin/env python3
"""Validate a Vizro dashboard YAML or Python file without starting a server.

YAML input is parsed into `vizro.models.Dashboard`. Python input is executed with
`runpy.run_path` and must define a `dashboard` variable containing a Dashboard
instance or dict.
"""

from __future__ import annotations

import argparse
import runpy
from pathlib import Path
from typing import Any

import yaml
from vizro import Vizro
from vizro.models import Dashboard


def load_dashboard(path: Path) -> Dashboard:
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise TypeError(f"Expected YAML object at top level, got {type(data).__name__}")
        return Dashboard(**data)

    if suffix == ".py":
        namespace = runpy.run_path(str(path))
        if "dashboard" not in namespace:
            raise KeyError("Python dashboard file must define a `dashboard` variable")
        obj: Any = namespace["dashboard"]
        if isinstance(obj, Dashboard):
            return obj
        if isinstance(obj, dict):
            return Dashboard(**obj)
        raise TypeError(f"`dashboard` must be a Dashboard or dict, got {type(obj).__name__}")

    raise ValueError("Expected a .py, .yaml, or .yml dashboard path")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Dashboard .py/.yaml/.yml path")
    parser.add_argument("--assets-folder", default=None, help="Optional assets folder passed to Vizro")
    parser.add_argument("--no-build", action="store_true", help="Only instantiate Dashboard; do not call Vizro().build")
    args = parser.parse_args()

    dashboard_path = args.path.resolve()
    dashboard = load_dashboard(dashboard_path)
    print(f"Dashboard OK: title={dashboard.title!r}, pages={len(dashboard.pages)}")

    if not args.no_build:
        kwargs = {"assets_folder": args.assets_folder} if args.assets_folder else {}
        wrapper = Vizro(**kwargs).build(dashboard)
        print(f"Build OK: wrapper={type(wrapper).__name__}, dash_title={wrapper.dash.title!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

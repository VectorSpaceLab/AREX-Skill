#!/usr/bin/env python3
"""Check that the PyCaret engine and Control Plane backend import cleanly."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def dist_version(dist_name: str) -> str:
    """Return the installed distribution version or a readable fallback."""

    try:
        return version(dist_name)
    except PackageNotFoundError:
        return "not-installed"


def build_snapshot() -> dict[str, Any]:
    """Collect a small cross-cutting runtime snapshot."""

    from pycaret.api import list_models
    from pycaret_server.app import create_app

    app = create_app()
    return {
        "pycaret": dist_version("pycaret"),
        "pycaret-server": dist_version("pycaret-server"),
        "classification_models": len(list_models("classification")),
        "regression_models": len(list_models("regression")),
        "routes": len(app.routes),
    }


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the snapshot as JSON instead of human-readable text.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the cross-cutting stack check."""

    args = parse_args()
    snapshot = build_snapshot()

    if args.json:
        print(json.dumps(snapshot, indent=2, sort_keys=True))
        return 0

    print(f"pycaret: {snapshot['pycaret']}")
    print(f"pycaret-server: {snapshot['pycaret-server']}")
    print(f"classification models: {snapshot['classification_models']}")
    print(f"regression models: {snapshot['regression_models']}")
    print(f"FastAPI routes: {snapshot['routes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

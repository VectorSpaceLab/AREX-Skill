#!/usr/bin/env python3
"""Quick AutoTrain Advanced install/import check.

Run from any environment where AutoTrain Advanced is installed:

    python skills/disco/autotrain-advanced/scripts/check_install.py
"""

from __future__ import annotations

import json
import sys
from importlib.metadata import PackageNotFoundError, version


def package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "<not installed>"


def main() -> int:
    try:
        import autotrain  # type: ignore
        from autotrain.cli import autotrain as cli_module  # type: ignore
    except Exception as exc:  # pragma: no cover - meant for environment triage
        print(f"ERROR: failed to import AutoTrain Advanced: {exc!r}", file=sys.stderr)
        return 1

    payload = {
        "python": sys.version.split()[0],
        "autotrain___version__": getattr(autotrain, "__version__", None),
        "metadata_autotrain_advanced": package_version("autotrain-advanced"),
        "autotrain_file": getattr(autotrain, "__file__", None),
        "cli_module_file": getattr(cli_module, "__file__", None),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

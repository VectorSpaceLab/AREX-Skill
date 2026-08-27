#!/usr/bin/env python3
"""Run OpenFlamingo's installed RICES feature-cache script with path fixes.

The upstream cache script imports evaluation helpers through package-relative
and unqualified names. This wrapper locates the installed `open_flamingo`
package, adds the package, `eval`, and `scripts` directories to `sys.path`, and
executes the packaged `scripts/cache_rices_features.py` as `__main__`.

Example:
    python scripts/run_cache_rices_entrypoint.py --help
"""

from __future__ import annotations

import importlib.util
import runpy
import sys
from pathlib import Path


def main() -> int:
    spec = importlib.util.find_spec("open_flamingo")
    if spec is None or spec.origin is None:
        raise SystemExit("Cannot find installed package `open_flamingo`.")
    package_dir = Path(spec.origin).resolve().parent
    eval_dir = package_dir / "eval"
    scripts_dir = package_dir / "scripts"
    entrypoint = scripts_dir / "cache_rices_features.py"
    if not entrypoint.exists():
        raise SystemExit(
            "Installed OpenFlamingo package does not include scripts/cache_rices_features.py; use a source checkout or refresh this skill."
        )
    for path in (str(package_dir), str(eval_dir), str(scripts_dir)):
        if path not in sys.path:
            sys.path.insert(0, path)
    sys.argv[0] = str(entrypoint)
    runpy.run_path(str(entrypoint), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

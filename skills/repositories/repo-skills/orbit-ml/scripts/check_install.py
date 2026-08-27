#!/usr/bin/env python3
"""Cross-cutting Orbit installation check.

This helper verifies that the installed `orbit-ml` package can be imported,
that the core public submodules load, and that CmdStan is discoverable through
`cmdstanpy`.

It is intentionally lightweight and does not fit a model.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from importlib.metadata import version


def probe() -> dict[str, object]:
    import orbit
    import orbit.diagnostics
    import orbit.models
    import orbit.utils
    import cmdstanpy

    cmdstan_path = cmdstanpy.cmdstan_path()
    summary: dict[str, object] = {
        "orbit_version": getattr(orbit, "__version__", version("orbit-ml")),
        "orbit_module": orbit.__name__,
        "models_module": orbit.models.__name__,
        "diagnostics_module": orbit.diagnostics.__name__,
        "utils_module": orbit.utils.__name__,
        "cmdstan_path_resolved": bool(cmdstan_path),
        "cmdstan_path_name": Path(cmdstan_path).name if cmdstan_path else None,
    }

    try:
        import torch

        summary["torch_version"] = torch.__version__
        summary["torch_cuda_available"] = bool(torch.cuda.is_available())
    except ModuleNotFoundError:
        summary["torch_version"] = None
        summary["torch_cuda_available"] = None

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    try:
        summary = probe()
    except ModuleNotFoundError as exc:
        print(f"orbit install check missing dependency: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"orbit install check failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("orbit install check: ok")
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

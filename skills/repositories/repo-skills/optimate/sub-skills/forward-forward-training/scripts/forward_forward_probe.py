#!/usr/bin/env python3
"""Safe import and signature probe for the Forward-Forward package.

Example:
  python scripts/forward_forward_probe.py
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    report = {"python": sys.version, "forward_forward": None, "collections_generator": None}
    try:
        module = importlib.import_module("forward_forward")
        from forward_forward import train_with_forward_forward_algorithm
        from forward_forward.root_op import ForwardForwardModelType

        report["forward_forward"] = {
            "status": "ok",
            "file": getattr(module, "__file__", None),
            "signature": str(inspect.signature(train_with_forward_forward_algorithm)),
            "model_types": [m.value for m in ForwardForwardModelType],
        }
    except Exception as exc:
        report["forward_forward"] = {"status": "missing", "error": f"{type(exc).__name__}: {exc}"}

    try:
        from collections import Generator  # type: ignore
        report["collections_generator"] = {"status": "ok", "value": str(Generator)}
    except Exception as exc:
        report["collections_generator"] = {"status": "missing", "error": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

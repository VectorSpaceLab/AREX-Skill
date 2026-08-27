#!/usr/bin/env python3
"""Inspect selected PennyLane API signatures and first docstring line.

Examples:
    python inspect_pennylane_api.py QNode qnode device grad qchem.Molecule estimator.estimate
"""

from __future__ import annotations

import argparse
import inspect
import sys
from typing import Any

import pennylane as qp


def resolve(name: str) -> Any:
    obj: Any = qp
    for part in name.split("."):
        obj = getattr(obj, part)
    return obj


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="*", help="API names relative to pennylane, e.g. QNode")
    args = parser.parse_args(argv)
    names = args.names or ["QNode", "qnode", "device", "grad", "transform", "compile"]
    print(f"pennylane_version={qp.version()}")
    for name in names:
        try:
            obj = resolve(name)
            try:
                signature = inspect.signature(obj)
            except (TypeError, ValueError) as exc:
                signature = f"<signature unavailable: {exc}>"
            doc = (inspect.getdoc(obj) or "").splitlines()[0] if inspect.getdoc(obj) else ""
            print(f"\n{name}{signature}")
            if doc:
                print(f"  {doc}")
        except Exception as exc:  # pragma: no cover - diagnostic helper
            print(f"\n{name}: ERROR {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

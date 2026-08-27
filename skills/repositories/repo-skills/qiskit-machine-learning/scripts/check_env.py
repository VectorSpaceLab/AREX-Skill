#!/usr/bin/env python3
"""Check public Qiskit Machine Learning imports and optional backends.

This diagnostic is deliberately independent of the source checkout. It only
imports installed public modules and performs an optional one-element CUDA
allocation when requested.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any


BASE_MODULES = (
    "qiskit_machine_learning",
    "qiskit_machine_learning.algorithms",
    "qiskit_machine_learning.circuit.library",
    "qiskit_machine_learning.datasets",
    "qiskit_machine_learning.gradients",
    "qiskit_machine_learning.kernels",
    "qiskit_machine_learning.neural_networks",
    "qiskit_machine_learning.optimizers",
    "qiskit_machine_learning.primitives",
    "qiskit_machine_learning.state_fidelities",
    "qiskit_machine_learning.utils",
)


def probe(name: str) -> dict[str, Any]:
    """Return a serializable import result for one module."""
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # import diagnostics should report, not traceback
        return {"module": name, "status": "missing", "error": f"{type(exc).__name__}: {exc}"}
    return {"module": name, "status": "ok", "version": getattr(module, "__version__", None)}


def main(argv: list[str] | None = None) -> int:
    """Run base, optional, and requested CUDA probes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-torch", action="store_true", help="fail unless torch imports")
    parser.add_argument("--require-sparse", action="store_true", help="fail unless sparse imports")
    parser.add_argument("--require-nlopt", action="store_true", help="fail unless nlopt imports")
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="fail unless torch reports CUDA and a tiny device allocation succeeds",
    )
    parser.add_argument("--json", action="store_true", help="emit one JSON object instead of text")
    args = parser.parse_args(argv)

    results = [probe(name) for name in BASE_MODULES]
    optional = {name: probe(name) for name in ("torch", "sparse", "nlopt", "qiskit_aer")}
    cuda: dict[str, Any] = {"status": "not-requested"}
    if args.require_cuda:
        try:
            import torch

            cuda = {
                "status": "ok" if torch.cuda.is_available() else "missing",
                "available": bool(torch.cuda.is_available()),
                "count": int(torch.cuda.device_count()),
                "version": torch.version.cuda,
            }
            if torch.cuda.is_available():
                cuda["device"] = torch.cuda.get_device_name(0)
                cuda["capability"] = list(torch.cuda.get_device_capability(0))
                torch.empty((1,), device="cuda")
                cuda["allocation"] = "ok"
            else:
                cuda["allocation"] = "not-run"
        except Exception as exc:
            cuda = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

    payload = {"base": results, "optional": optional, "cuda": cuda}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for item in results:
            suffix = "" if item["status"] == "ok" else f" — {item['error']}"
            print(f"{item['module']}: {item['status']}{suffix}")
        for name, item in optional.items():
            suffix = "" if item["status"] == "ok" else f" — {item['error']}"
            print(f"{name}: {item['status']}{suffix}")
        print(f"cuda: {cuda['status']}")

    required = list(results)
    if args.require_torch:
        required.append(optional["torch"])
    if args.require_sparse:
        required.append(optional["sparse"])
    if args.require_nlopt:
        required.append(optional["nlopt"])
    failed = any(item["status"] != "ok" for item in required)
    if args.require_cuda and cuda["status"] != "ok":
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

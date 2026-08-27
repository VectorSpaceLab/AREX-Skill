#!/usr/bin/env python3
"""Check a TorchDrug environment without downloads or training.

Example:
  python scripts/check_torchdrug_env.py --optional
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import sys


def optional_import(name: str) -> str:
    try:
        module = importlib.import_module(name)
    except Exception as error:  # pragma: no cover - diagnostic path
        return f"MISSING {name}: {type(error).__name__}: {error}"
    version = getattr(module, "__version__", None)
    if version is None:
        try:
            version = metadata.version(name.replace("_", "-"))
        except Exception:
            version = "unknown"
    return f"OK {name}: {version}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a no-download TorchDrug import and graph smoke check.")
    parser.add_argument("--optional", action="store_true", help="Also check optional/compiled dependency imports.")
    args = parser.parse_args()

    try:
        import torch
        import torchdrug
        from torchdrug import data
    except Exception as error:
        print(f"FAIL import: {type(error).__name__}: {error}", file=sys.stderr)
        return 1

    print(f"torchdrug={getattr(torchdrug, '__version__', 'unknown')}")
    print(f"torch={torch.__version__} cuda={torch.version.cuda} cuda_available={torch.cuda.is_available()}")

    graph = data.Graph([[0, 1], [1, 0]], num_node=2)
    print(f"graph num_node={int(graph.num_node)} num_edge={int(graph.num_edge)}")

    if args.optional:
        for name in ["torch_scatter", "torch_cluster", "rdkit", "esm", "lmdb"]:
            print(optional_import(name))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

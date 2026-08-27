#!/usr/bin/env python3
"""Safe Spektral installation and API sanity check.

This script performs read-only imports and optional signature reporting. It does
not download datasets, train models, or write files.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:  # Python 3.7 compatibility
    from importlib_metadata import PackageNotFoundError, version  # type: ignore
from typing import List, Optional


def _dist_version(name: str) -> Optional[str]:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def build_report(show_signatures: bool) -> dict:
    import spektral
    import tensorflow as tf

    report = {
        "python": sys.version.split()[0],
        "spektral_version": getattr(spektral, "__version__", _dist_version("spektral")),
        "spektral_distribution_version": _dist_version("spektral"),
        "tensorflow_version": getattr(tf, "__version__", None),
        "gpu_devices": [device.name for device in tf.config.list_physical_devices("GPU")],
        "core_imports": {},
    }

    from spektral.data import BatchLoader, Dataset, DisjointLoader, Graph, MixedLoader, SingleLoader
    from spektral.layers import GCNConv, GeneralConv, GraphMasking, MessagePassing
    from spektral.models import GCN, GNNExplainer, GeneralGNN
    from spektral.transforms import GCNFilter, LayerPreprocess

    imported = {
        "Graph": Graph,
        "Dataset": Dataset,
        "SingleLoader": SingleLoader,
        "DisjointLoader": DisjointLoader,
        "BatchLoader": BatchLoader,
        "MixedLoader": MixedLoader,
        "GCNConv": GCNConv,
        "GeneralConv": GeneralConv,
        "MessagePassing": MessagePassing,
        "GraphMasking": GraphMasking,
        "GCN": GCN,
        "GeneralGNN": GeneralGNN,
        "GNNExplainer": GNNExplainer,
        "GCNFilter": GCNFilter,
        "LayerPreprocess": LayerPreprocess,
    }
    report["core_imports"] = {name: True for name in imported}

    if show_signatures:
        report["signatures"] = {
            name: str(inspect.signature(obj)) for name, obj in imported.items()
        }

    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check Spektral imports and key API signatures.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--show-signatures",
        action="store_true",
        help="Include signatures for key public classes.",
    )
    args = parser.parse_args(argv)

    report = build_report(args.show_signatures)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Spektral: {report['spektral_version']}")
        print(f"TensorFlow: {report['tensorflow_version']}")
        print(f"GPU devices: {len(report['gpu_devices'])}")
        print("Core imports: ok")
        if args.show_signatures:
            print("\nSignatures:")
            for name, signature in report["signatures"].items():
                print(f"- {name}{signature}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

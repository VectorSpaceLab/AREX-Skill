#!/usr/bin/env python3
"""Safe StellarGraph environment diagnostic.

This script verifies that the current Python can import StellarGraph, construct a
tiny in-memory graph, and, by default, build a representative GCN tensor graph.
It never downloads datasets, starts Neo4j, trains a model, or requires a GPU.

Examples:
  python scripts/check_stellargraph_environment.py
  python scripts/check_stellargraph_environment.py --show-backends
  python scripts/check_stellargraph_environment.py --repo-root /path/to/checkout
"""

from __future__ import annotations

import argparse
import importlib
import sys
import traceback
from importlib import metadata
from pathlib import Path


def _add_repo_root(path):
    if not path:
        return
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"--repo-root does not exist: {root}")
    sys.path.insert(0, str(root))


def _warn_python_version() -> None:
    version = sys.version_info
    print(f"python: {version.major}.{version.minor}.{version.micro}")
    if version >= (3, 9):
        print(
            "warning: StellarGraph 1.x package metadata targets Python >=3.6,<3.9; "
            "prefer Python 3.8 for reproducible installs."
        )


def _import_package():
    sg = importlib.import_module("stellargraph")
    try:
        dist_version = metadata.version("stellargraph")
    except metadata.PackageNotFoundError:
        dist_version = "metadata-not-found"
    print(f"stellargraph module version: {getattr(sg, '__version__', 'unknown')}")
    print(f"stellargraph distribution version: {dist_version}")
    return sg


def _basic_graph_smoke(sg) -> None:
    import pandas as pd

    nodes = pd.DataFrame(
        {"x": [1.0, 0.0, 1.0], "y": [0.0, 1.0, 1.0]}, index=["a", "b", "c"]
    )
    edges = pd.DataFrame({"source": ["a", "b"], "target": ["b", "c"]})
    graph = sg.StellarGraph(nodes, edges)
    sizes = graph.node_feature_sizes()
    if graph.number_of_nodes() != 3 or graph.number_of_edges() != 2 or sizes != {"default": 2}:
        raise RuntimeError(
            f"unexpected tiny graph summary: nodes={graph.number_of_nodes()} "
            f"edges={graph.number_of_edges()} feature_sizes={sizes}"
        )
    print("graph smoke: ok (3 nodes, 2 edges, 2 default features)")
    return graph


def _gcn_smoke(graph) -> None:
    import tensorflow as tf
    from stellargraph.mapper import FullBatchNodeGenerator
    from stellargraph.layer import GCN

    total = tf.reduce_sum(tf.constant([1.0, 2.0])).numpy()
    if float(total) != 3.0:
        raise RuntimeError("TensorFlow constant smoke returned an unexpected value")
    generator = FullBatchNodeGenerator(graph, method="gcn", sparse=False)
    model = GCN(layer_sizes=[2], generator=generator)
    x_in, x_out = model.in_out_tensors()
    print(f"tensorflow: {tf.__version__}")
    print(f"gcn smoke: ok (inputs={len(x_in)}, output_shape={x_out.shape})")


def _show_backends(require_gpu: bool) -> None:
    import tensorflow as tf

    gpus = tf.config.list_physical_devices("GPU")
    print(f"tensorflow visible GPUs: {len(gpus)}")
    for index, gpu in enumerate(gpus):
        print(f"  gpu[{index}]: {gpu}")
    if require_gpu and not gpus:
        raise RuntimeError("--require-gpu was set but TensorFlow reports no GPU devices")


def _check_neo4j_import() -> None:
    mod = importlib.import_module("stellargraph.connector.neo4j")
    names = [
        "Neo4jStellarGraph",
        "Neo4jStellarDiGraph",
        "Neo4jGraphSAGENodeGenerator",
        "Neo4jDirectedGraphSAGENodeGenerator",
    ]
    missing = [name for name in names if not hasattr(mod, name)]
    if missing:
        raise RuntimeError(f"neo4j connector import missing expected names: {missing}")
    print("neo4j connector import: ok (service connectivity not tested)")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        help="Optional local checkout root to prepend to sys.path before importing stellargraph.",
    )
    parser.add_argument(
        "--skip-gcn-smoke",
        action="store_true",
        help="Only import StellarGraph and construct a tiny graph; skip the representative GCN/TensorFlow smoke.",
    )
    parser.add_argument(
        "--show-backends",
        action="store_true",
        help="Print TensorFlow-visible GPU devices. This does not require a GPU.",
    )
    parser.add_argument(
        "--require-gpu",
        action="store_true",
        help="Fail if TensorFlow cannot see a GPU. Use only when GPU execution is required.",
    )
    parser.add_argument(
        "--check-neo4j-import",
        action="store_true",
        help="Import Neo4j connector classes without starting or connecting to a database.",
    )
    parser.add_argument("--verbose", action="store_true", help="Show a traceback on failure.")
    args = parser.parse_args(argv)

    try:
        _add_repo_root(args.repo_root)
        _warn_python_version()
        sg = _import_package()
        graph = _basic_graph_smoke(sg)
        if not args.skip_gcn_smoke:
            _gcn_smoke(graph)
        if args.show_backends or args.require_gpu:
            _show_backends(args.require_gpu)
        if args.check_neo4j_import:
            _check_neo4j_import()
        print("stellargraph environment check: ok")
        return 0
    except Exception as exc:  # noqa: BLE001 - diagnostic CLI should report any failure
        print(f"stellargraph environment check: failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Tiny StellarGraph data-loading smoke.

Checks that the package can construct representative tiny graphs from Pandas,
NumPy, IndexedArray, and NetworkX inputs, and inspects dataset loader metadata
without downloading any data.

Examples:
  python sub-skills/graph-data-loading/scripts/stellargraph_data_smoke.py
  python sub-skills/graph-data-loading/scripts/stellargraph_data_smoke.py --repo-root /path/to/checkout
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _add_repo_root(path):
    if not path:
        return
    root = Path(path).expanduser().resolve()
    sys.path.insert(0, str(root))


def _build_graphs():
    import networkx as nx
    import numpy as np
    import pandas as pd
    from stellargraph import IndexedArray, StellarGraph, StellarDiGraph
    from stellargraph import datasets

    nodes = pd.DataFrame({"f0": [1.0, 0.0, 1.0], "f1": [0.0, 1.0, 1.0]}, index=["a", "b", "c"])
    edges = pd.DataFrame({"source": ["a", "b"], "target": ["b", "c"]})
    g_pd = StellarGraph(nodes, edges)

    arr_nodes = np.array([[1.0, 0.0], [0.0, 1.0]])
    arr_edges = pd.DataFrame({"source": [0], "target": [1]})
    g_np = StellarGraph(arr_nodes, arr_edges)

    indexed = IndexedArray(np.array([[2.0, 3.0], [4.0, 5.0]], dtype="float32"), index=["x", "y"])
    g_ix = StellarDiGraph(indexed, pd.DataFrame({"source": ["x"], "target": ["y"]}))

    nx_graph = nx.Graph()
    nx_graph.add_node("n1", feature=[1.0, 2.0], label="paper")
    nx_graph.add_node("n2", feature=[3.0, 4.0], label="paper")
    nx_graph.add_edge("n1", "n2", weight=1.0, label="cites")
    g_nx = StellarGraph.from_networkx(
        nx_graph,
        node_features="feature",
        node_type_attr="label",
        edge_type_attr="label",
        edge_weight_attr="weight",
    )

    hetero_nodes = {
        "user": pd.DataFrame({"age": [20.0, 30.0]}, index=["user:1", "user:2"]),
        "movie": pd.DataFrame({"year": [2001.0]}, index=["movie:1"]),
    }
    hetero_edges = {
        "rates": pd.DataFrame({"source": ["user:1"], "target": ["movie:1"], "weight": [5.0]})
    }
    g_hetero = StellarGraph(hetero_nodes, hetero_edges)

    print(f"pandas graph: nodes={g_pd.number_of_nodes()} edges={g_pd.number_of_edges()} features={g_pd.node_feature_sizes()}")
    print(f"numpy graph: nodes={g_np.number_of_nodes()} edges={g_np.number_of_edges()} features={g_np.node_feature_sizes()}")
    print(f"indexed graph: nodes={g_ix.number_of_nodes()} edges={g_ix.number_of_edges()} features={g_ix.node_feature_sizes()}")
    print(f"networkx graph: nodes={g_nx.number_of_nodes()} edges={g_nx.number_of_edges()} features={g_nx.node_feature_sizes()}")
    print(f"heterogeneous graph: node_types={sorted(g_hetero.node_types)} edge_types={sorted(g_hetero.edge_types)}")

    return datasets


def _dataset_metadata_smoke(datasets) -> None:
    classes = [datasets.Cora, datasets.CiteSeer, datasets.PubMedDiabetes, datasets.MovieLens, datasets.METR_LA]
    for cls in classes:
        ds = cls()
        print(f"dataset {cls.__name__}: base_directory={ds.base_directory} data_directory={ds.data_directory}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Optional local checkout root to prepend to sys.path.")
    parser.add_argument(
        "--skip-dataset-metadata",
        action="store_true",
        help="Only build tiny graphs; skip dataset loader metadata inspection.",
    )
    args = parser.parse_args(argv)

    try:
        _add_repo_root(args.repo_root)
        datasets = _build_graphs()
        if not args.skip_dataset_metadata:
            _dataset_metadata_smoke(datasets)
        print("graph data loading smoke: ok")
        return 0
    except Exception as exc:  # noqa: BLE001 - diagnostic CLI should report any failure
        print(f"graph data loading smoke: failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

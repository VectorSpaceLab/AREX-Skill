#!/usr/bin/env python3
"""Deterministic Graph Nets NumPy/NetworkX graph-data smoke test.

The script imports the installed graph_nets package, builds one tiny NetworkX
example and one tiny data-dictionary example, batches them through
utils_np.data_dicts_to_graphs_tuple, round-trips back to dictionaries and
NetworkX graphs, and prints a JSON summary.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings

try:  # Python 3.8+.
    from importlib import metadata
except ImportError:  # Python 3.7 inspection stacks may use the backport.
    try:
        import importlib_metadata as metadata  # type: ignore
    except ImportError:  # Version reporting is optional.
        metadata = None


def _package_version():
    if metadata is None:
        return None
    package_not_found = getattr(metadata, "PackageNotFoundError", Exception)
    for dist_name in ("graph-nets", "graph_nets"):
        try:
            return metadata.version(dist_name)
        except package_not_found:
            continue
    return None


def _shape_or_none(value):
    return None if value is None else list(value.shape)


def _tolist_or_none(value):
    return None if value is None else value.tolist()


def _run_smoke():
    import networkx as nx
    import numpy as np
    from graph_nets import graphs
    from graph_nets import utils_np

    if not hasattr(nx, "OrderedMultiDiGraph"):
        raise RuntimeError(
            "networkx.OrderedMultiDiGraph is missing; Graph Nets NumPy "
            "NetworkX conversion is verified with networkx<3")

    warnings.filterwarnings(
        "ignore", category=DeprecationWarning, message=".*OrderedMultiDiGraph.*")
    graph_nx = nx.OrderedMultiDiGraph()
    graph_nx.add_node(0, features=np.array([1.0, 0.0], dtype=np.float32))
    graph_nx.add_node(1, features=np.array([0.0, 1.0], dtype=np.float32))
    graph_nx.add_edge(
        0,
        1,
        features=np.array([0.5, 1.5], dtype=np.float32),
        index=0,
    )
    graph_nx.graph["features"] = np.array([3.0], dtype=np.float32)

    from_nx = utils_np.networkx_to_data_dict(graph_nx)

    from_dict = {
        graphs.NODES: np.array([[2.0, 2.5]], dtype=np.float32),
        graphs.EDGES: np.zeros((0, 2), dtype=np.float32),
        graphs.RECEIVERS: np.zeros((0,), dtype=np.int32),
        graphs.SENDERS: np.zeros((0,), dtype=np.int32),
        graphs.GLOBALS: np.array([4.0], dtype=np.float32),
        graphs.N_NODE: np.array(1, dtype=np.int32),
        graphs.N_EDGE: np.array(0, dtype=np.int32),
    }

    batch = utils_np.data_dicts_to_graphs_tuple([from_nx, from_dict])
    data_dicts = utils_np.graphs_tuple_to_data_dicts(batch)
    networkxs = utils_np.graphs_tuple_to_networkxs(batch)
    first = utils_np.get_graph(batch, 0)

    assert batch.n_node.tolist() == [2, 1]
    assert batch.n_edge.tolist() == [1, 0]
    assert batch.receivers.tolist() == [1]
    assert batch.senders.tolist() == [0]
    assert [g.number_of_nodes() for g in networkxs] == [2, 1]
    assert [g.number_of_edges() for g in networkxs] == [1, 0]
    assert first.n_node.tolist() == [2]
    assert first.n_edge.tolist() == [1]

    return {
        "ok": True,
        "graph_nets_version": _package_version(),
        "networkx_version": getattr(nx, "__version__", None),
        "fields": list(graphs.ALL_FIELDS),
        "batch": {
            "n_node": batch.n_node.tolist(),
            "n_edge": batch.n_edge.tolist(),
            "nodes_shape": _shape_or_none(batch.nodes),
            "edges_shape": _shape_or_none(batch.edges),
            "globals_shape": _shape_or_none(batch.globals),
            "receivers": _tolist_or_none(batch.receivers),
            "senders": _tolist_or_none(batch.senders),
        },
        "roundtrip_data_dicts": [
            {
                "n_node": int(d[graphs.N_NODE]),
                "n_edge": int(d[graphs.N_EDGE]),
                "nodes_shape": _shape_or_none(d[graphs.NODES]),
                "edges_shape": _shape_or_none(d[graphs.EDGES]),
                "receivers": _tolist_or_none(d[graphs.RECEIVERS]),
                "senders": _tolist_or_none(d[graphs.SENDERS]),
                "globals": _tolist_or_none(d[graphs.GLOBALS]),
            }
            for d in data_dicts
        ],
        "roundtrip_networkx": [
            {
                "nodes": g.number_of_nodes(),
                "edges": g.number_of_edges(),
                "globals": _tolist_or_none(g.graph.get("features")),
            }
            for g in networkxs
        ],
        "get_graph_0": {
            "n_node": first.n_node.tolist(),
            "n_edge": first.n_edge.tolist(),
            "receivers": _tolist_or_none(first.receivers),
            "senders": _tolist_or_none(first.senders),
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic Graph Nets graph-data round-trip smoke test "
            "using installed graph_nets, NumPy, and NetworkX."
        )
    )
    parser.add_argument(
        "--json-indent",
        type=int,
        default=2,
        help="Indentation for the JSON report; use 0 for compact output.",
    )
    args = parser.parse_args(argv)

    try:
        report = _run_smoke()
        print(json.dumps(report, indent=None if args.json_indent == 0 else args.json_indent, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - diagnostic path.
        report = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "graph_nets_version": _package_version(),
        }
        print(json.dumps(report, indent=None if args.json_indent == 0 else args.json_indent, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())

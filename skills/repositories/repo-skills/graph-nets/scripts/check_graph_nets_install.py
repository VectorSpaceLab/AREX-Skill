#!/usr/bin/env python3
"""Check an installed DeepMind Graph Nets runtime.

This script is a safe, deterministic diagnostic. It imports the installed
packages, checks version-sensitive symbols, round-trips a tiny graph through
utils_np, runs a tiny GraphIndependent model through TF1 session or TF2 eager
execution, and prints JSON. It does not read a source checkout.
"""

from __future__ import print_function

import argparse
import json
import sys

try:
    from importlib import metadata
except ImportError:  # Python 3.7 backport used in legacy stacks.
    try:
        import importlib_metadata as metadata  # type: ignore
    except ImportError:
        metadata = None


def _dist_version(*names):
    if metadata is None:
        return None
    package_not_found = getattr(metadata, "PackageNotFoundError", Exception)
    for name in names:
        try:
            return metadata.version(name)
        except package_not_found:
            pass
    return None


def _jsonify_array(np_module, value):
    arr = np_module.asarray(value)
    return {
        "shape": list(arr.shape),
        "sum": float(arr.sum()) if arr.size else 0.0,
        "values": arr.astype(float).tolist() if arr.size <= 8 else None,
    }


def _tiny_data(np_module):
    return [{
        "nodes": np_module.array([[1.0, 0.0], [0.0, 1.0]], dtype=np_module.float32),
        "edges": np_module.array([[0.5]], dtype=np_module.float32),
        "senders": np_module.array([0], dtype=np_module.int32),
        "receivers": np_module.array([1], dtype=np_module.int32),
        "globals": np_module.array([1.0], dtype=np_module.float32),
    }]


def _affine(scale, offset):
    def apply(x):
        return x * scale + offset
    return apply


def _model(modules):
    return modules.GraphIndependent(
        edge_model_fn=lambda: _affine(2.0, 1.0),
        node_model_fn=lambda: _affine(3.0, -1.0),
        global_model_fn=lambda: _affine(0.5, 2.0),
        name="check_graph_nets_install")


def _session_cls(tf):
    if hasattr(tf, "Session"):
        return tf.Session
    if hasattr(tf, "compat") and hasattr(tf.compat, "v1"):
        return getattr(tf.compat.v1, "Session", None)
    return None


def _global_initializer(tf):
    if hasattr(tf, "global_variables_initializer"):
        return tf.global_variables_initializer
    if hasattr(tf, "compat") and hasattr(tf.compat, "v1"):
        return getattr(tf.compat.v1, "global_variables_initializer", None)
    return None


def _reset_graph(tf):
    if hasattr(tf, "reset_default_graph"):
        tf.reset_default_graph()
    elif hasattr(tf, "compat") and hasattr(tf.compat, "v1") and hasattr(tf.compat.v1, "reset_default_graph"):
        tf.compat.v1.reset_default_graph()


def _run_numpy_smoke(nx, np_module, utils_np):
    if not hasattr(nx, "OrderedMultiDiGraph"):
        return {
            "ok": False,
            "error": "networkx.OrderedMultiDiGraph is missing; install networkx<3 for Graph Nets NetworkX conversion helpers"
        }
    graph_nx = nx.OrderedMultiDiGraph()
    graph_nx.add_node(0, features=np_module.array([1.0, 0.0], dtype=np_module.float32))
    graph_nx.add_node(1, features=np_module.array([0.0, 1.0], dtype=np_module.float32))
    graph_nx.add_edge(0, 1, features=np_module.array([0.5], dtype=np_module.float32), index=0)
    graph_nx.graph["features"] = np_module.array([1.0], dtype=np_module.float32)
    data_dict = utils_np.networkx_to_data_dict(graph_nx)
    graph = utils_np.data_dicts_to_graphs_tuple([data_dict])
    round_trip = utils_np.graphs_tuple_to_networkxs(graph)[0]
    return {
        "ok": True,
        "n_node": graph.n_node.astype(int).tolist(),
        "n_edge": graph.n_edge.astype(int).tolist(),
        "nodes_shape": list(graph.nodes.shape),
        "edges_shape": list(graph.edges.shape),
        "round_trip_nodes": int(round_trip.number_of_nodes()),
        "round_trip_edges": int(round_trip.number_of_edges()),
    }


def _run_model_smoke(np_module, tf, modules, utils_tf):
    eager = getattr(tf, "executing_eagerly", lambda: False)()
    _reset_graph(tf)
    graph = utils_tf.data_dicts_to_graphs_tuple(_tiny_data(np_module))
    output = _model(modules)(graph)
    if eager:
        return {
            "ok": True,
            "mode": "tf2-eager",
            "nodes": _jsonify_array(np_module, output.nodes.numpy()),
            "edges": _jsonify_array(np_module, output.edges.numpy()),
            "globals": _jsonify_array(np_module, output.globals.numpy()),
            "n_node": np_module.asarray(output.n_node.numpy()).astype(int).tolist(),
            "n_edge": np_module.asarray(output.n_edge.numpy()).astype(int).tolist(),
        }
    sess_cls = _session_cls(tf)
    init = _global_initializer(tf)
    if sess_cls is None or init is None:
        return {"ok": False, "error": "TensorFlow session APIs are unavailable and eager execution is not enabled"}
    with sess_cls() as sess:
        sess.run(init())
        result = sess.run(output)
    return {
        "ok": True,
        "mode": "tf1-session",
        "nodes": _jsonify_array(np_module, result.nodes),
        "edges": _jsonify_array(np_module, result.edges),
        "globals": _jsonify_array(np_module, result.globals),
        "n_node": np_module.asarray(result.n_node).astype(int).tolist(),
        "n_edge": np_module.asarray(result.n_edge).astype(int).tolist(),
    }


def run():
    import graph_nets  # pylint: disable=import-outside-toplevel
    from graph_nets import modules  # pylint: disable=import-outside-toplevel
    from graph_nets import utils_np  # pylint: disable=import-outside-toplevel
    from graph_nets import utils_tf  # pylint: disable=import-outside-toplevel
    import networkx as nx  # pylint: disable=import-outside-toplevel
    import numpy as np  # pylint: disable=import-outside-toplevel
    import sonnet as snt  # pylint: disable=import-outside-toplevel
    import tensorflow as tf  # pylint: disable=import-outside-toplevel

    payload = {
        "ok": True,
        "versions": {
            "graph_nets_distribution": _dist_version("graph-nets", "graph_nets"),
            "tensorflow": getattr(tf, "__version__", None),
            "sonnet": getattr(snt, "__version__", None),
            "networkx": getattr(nx, "__version__", None),
            "numpy": getattr(np, "__version__", None),
        },
        "symbols": {
            "tf_has_session": hasattr(tf, "Session"),
            "tf_has_placeholder": hasattr(tf, "placeholder"),
            "tf_executing_eagerly": getattr(tf, "executing_eagerly", lambda: False)(),
            "networkx_has_ordered_multidigraph": hasattr(nx, "OrderedMultiDiGraph"),
        }
    }
    payload["numpy_smoke"] = _run_numpy_smoke(nx, np, utils_np)
    payload["model_smoke"] = _run_model_smoke(np, tf, modules, utils_tf)
    payload["ok"] = bool(payload["numpy_smoke"].get("ok") and payload["model_smoke"].get("ok"))
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check an installed Graph Nets runtime and print JSON.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    args = parser.parse_args(argv)
    try:
        payload = run()
    except Exception as exc:  # pylint: disable=broad-except
        payload = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

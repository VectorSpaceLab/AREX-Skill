#!/usr/bin/env python3
"""Small deterministic Graph Nets utils_tf smoke.

The script imports the installed graph_nets and tensorflow packages, builds a
node-only GraphsTuple, completes it with TensorFlow utility ops, and prints a
JSON summary. It intentionally does not read the source checkout and can be run
from any current working directory.
"""

import argparse
import json
import sys


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run a deterministic Graph Nets utils_tf smoke and print JSON.")
    parser.add_argument(
        "--connect-mode",
        choices=("auto", "static", "dynamic"),
        default="auto",
        help="Fully-connected edge helper to exercise; auto tries static then dynamic.")
    padding_group = parser.add_mutually_exclusive_group()
    padding_group.add_argument(
        "--include-padding",
        dest="include_padding",
        action="store_true",
        default=True,
        help="Also exercise pad/remove-padding/mask utilities (default).")
    padding_group.add_argument(
        "--skip-padding",
        dest="include_padding",
        action="store_false",
        help="Skip pad/remove-padding utilities.")
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level; use 0 for a single line.")
    return parser.parse_args(argv)


def _import_runtime():
    import numpy as np  # pylint: disable=import-outside-toplevel
    import tensorflow as tf  # pylint: disable=import-outside-toplevel
    import graph_nets  # pylint: disable=import-outside-toplevel
    from graph_nets import utils_np  # pylint: disable=import-outside-toplevel
    from graph_nets import utils_tf  # pylint: disable=import-outside-toplevel
    return np, tf, graph_nets, utils_np, utils_tf


def _node_only_data_dicts(np):
    return [
        {"nodes": np.array([[0.0], [1.0]], dtype=np.float32)},
        {"nodes": np.array([[2.0], [3.0]], dtype=np.float32)},
    ]


def _reset_default_graph_if_available(tf):
    reset = getattr(tf, "reset_default_graph", None)
    if reset is None and hasattr(tf, "compat"):
        reset = getattr(tf.compat.v1, "reset_default_graph", None)
    if reset is not None:
        reset()


def _executing_eagerly(tf):
    fn = getattr(tf, "executing_eagerly", None)
    return bool(fn()) if fn is not None else False


def _session_class(tf):
    session = getattr(tf, "Session", None)
    if session is None and hasattr(tf, "compat"):
        session = getattr(tf.compat.v1, "Session", None)
    return session


def _fully_connect(utils_tf, graph, connect_mode):
    if connect_mode in ("static", "auto"):
        try:
            return (utils_tf.fully_connect_graph_static(
                graph, exclude_self_edges=True), "static")
        except ValueError:
            if connect_mode == "static":
                raise
    return (utils_tf.fully_connect_graph_dynamic(
        graph, exclude_self_edges=True), "dynamic")


def _build_ops(np, tf, utils_tf, connect_mode, include_padding):
    graph = utils_tf.data_dicts_to_graphs_tuple(_node_only_data_dicts(np))
    graph, actual_connect_mode = _fully_connect(utils_tf, graph, connect_mode)
    graph = utils_tf.set_zero_edge_features(graph, edge_size=1)
    graph = utils_tf.set_zero_global_features(graph, global_size=1)
    graph = utils_tf.identity(graph)

    repeated = utils_tf.repeat(
        tf.constant([[1], [2], [3]], dtype=tf.int32),
        tf.constant([1, 2, 0], dtype=tf.int32),
        axis=0,
        sum_repeats_hint=3,
    )
    concatenated = utils_tf.concat([graph, graph], axis=0)
    sliced = utils_tf.get_graph(concatenated, slice(1, 3))
    num_graphs = tf.convert_to_tensor(utils_tf.get_num_graphs(graph), dtype=tf.int32)
    size = utils_tf.get_graphs_tuple_size(graph)
    mask = utils_tf.get_mask(size.num_nodes, 6)

    padded = None
    recovered = None
    if include_padding:
        # The deterministic graph has 4 nodes, 4 edges, and 2 graphs. Padding
        # targets are integers so padded tensors get static leading shapes.
        padded = utils_tf.pad_graphs_tuple(
            graph,
            pad_nodes_to=5,
            pad_edges_to=4,
            pad_graphs_to=3,
        )
        recovered = utils_tf.remove_graphs_tuple_padding(padded, size)

    specs = None
    tensor_spec = getattr(tf, "TensorSpec", None)
    if tensor_spec is not None:
        specs = utils_tf.specs_from_graphs_tuple(
            graph,
            dynamic_num_graphs=False,
            dynamic_num_nodes=True,
            dynamic_num_edges=True,
        )

    return {
        "graph": graph,
        "connect_mode": actual_connect_mode,
        "repeated": repeated,
        "concatenated": concatenated,
        "sliced": sliced,
        "num_graphs": num_graphs,
        "size": size,
        "mask": mask,
        "padded": padded,
        "recovered": recovered,
        "specs": specs,
    }


def _shape(value):
    if value is None:
        return None
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    try:
        return [int(x) if x is not None else None for x in list(shape)]
    except TypeError:
        return str(shape)


def _tolist(value):
    if value is None:
        return None
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return [_tolist(v) for v in value]
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def _spec_summary(specs):
    if specs is None:
        return None
    fields = {}
    for name in ("nodes", "edges", "globals", "senders", "receivers", "n_node", "n_edge"):
        spec = getattr(specs, name)
        fields[name] = str(spec)
    return fields


def _summarize_arrays(arrays, tf, graph_nets, ops, placeholder_info=None):
    graph = arrays["graph"]
    sliced = arrays["sliced"]
    size = arrays["size"]
    padded = arrays.get("padded")
    recovered = arrays.get("recovered")
    specs = arrays.get("specs") or ops.get("specs")

    summary = {
        "ok": True,
        "mode": "tf2-eager" if _executing_eagerly(tf) else "tf1-session",
        "tensorflow": getattr(tf, "__version__", "unknown"),
        "graph_nets": getattr(graph_nets, "__version__", "unknown"),
        "tf_has_session": hasattr(tf, "Session"),
        "tf_has_placeholder": hasattr(tf, "placeholder"),
        "connect_mode": ops["connect_mode"],
        "graph": {
            "nodes_shape": _shape(graph.nodes),
            "edges_shape": _shape(graph.edges),
            "globals_shape": _shape(graph.globals),
            "n_node": _tolist(graph.n_node),
            "n_edge": _tolist(graph.n_edge),
            "senders": _tolist(graph.senders),
            "receivers": _tolist(graph.receivers),
        },
        "repeat_values": _tolist(arrays["repeated"]),
        "num_graphs": _tolist(arrays["num_graphs"]),
        "size": {
            "num_nodes": _tolist(size.num_nodes),
            "num_edges": _tolist(size.num_edges),
            "num_graphs": _tolist(size.num_graphs),
        },
        "mask": _tolist(arrays["mask"]),
        "sliced": {
            "n_node": _tolist(sliced.n_node),
            "n_edge": _tolist(sliced.n_edge),
            "senders": _tolist(sliced.senders),
            "receivers": _tolist(sliced.receivers),
        },
        "padding": None,
        "specs": _spec_summary(specs),
        "placeholder_feed": placeholder_info,
    }

    if padded is not None and recovered is not None:
        summary["padding"] = {
            "padded_nodes_shape": _shape(padded.nodes),
            "padded_edges_shape": _shape(padded.edges),
            "padded_globals_shape": _shape(padded.globals),
            "recovered_n_node": _tolist(recovered.n_node),
            "recovered_n_edge": _tolist(recovered.n_edge),
        }
    return summary


def _run_eager(np, tf, graph_nets, utils_tf, args):
    ops = _build_ops(np, tf, utils_tf, args.connect_mode, args.include_padding)
    arrays = {
        "graph": utils_tf.nest_to_numpy(ops["graph"]),
        "repeated": utils_tf.nest_to_numpy(ops["repeated"]),
        "sliced": utils_tf.nest_to_numpy(ops["sliced"]),
        "num_graphs": utils_tf.nest_to_numpy(ops["num_graphs"]),
        "size": utils_tf.nest_to_numpy(ops["size"]),
        "mask": utils_tf.nest_to_numpy(ops["mask"]),
        "padded": utils_tf.nest_to_numpy(ops["padded"]) if ops["padded"] is not None else None,
        "recovered": utils_tf.nest_to_numpy(ops["recovered"]) if ops["recovered"] is not None else None,
    }
    placeholder_info = "skipped: TF2/eager path does not use top-level tf.placeholder"
    return _summarize_arrays(arrays, tf, graph_nets, ops, placeholder_info)


def _run_session(np, tf, graph_nets, utils_np, utils_tf, args):
    _reset_default_graph_if_available(tf)
    ops = _build_ops(np, tf, utils_tf, args.connect_mode, args.include_padding)

    placeholder_info = "skipped: top-level tf.placeholder unavailable"
    placeholder_fetch = None
    placeholder_feed = None
    if hasattr(tf, "placeholder"):
        placeholders = utils_tf.placeholders_from_data_dicts(
            _node_only_data_dicts(np), force_dynamic_num_graphs=True)
        feed_graph = utils_np.data_dicts_to_graphs_tuple(_node_only_data_dicts(np))
        placeholder_fetch = utils_tf.make_runnable_in_session(placeholders)
        placeholder_feed = utils_tf.get_feed_dict(placeholders, feed_graph)

    session_cls = _session_class(tf)
    if session_cls is None:
        raise RuntimeError("No TensorFlow Session API is available and eager execution is disabled.")

    fetches = {
        "graph": ops["graph"],
        "repeated": ops["repeated"],
        "sliced": ops["sliced"],
        "num_graphs": ops["num_graphs"],
        "size_values": [ops["size"].num_nodes, ops["size"].num_edges, ops["size"].num_graphs],
        "mask": ops["mask"],
    }
    if ops["padded"] is not None:
        fetches["padded"] = ops["padded"]
        fetches["recovered"] = ops["recovered"]
    if placeholder_fetch is not None:
        fetches["placeholder"] = placeholder_fetch

    with session_cls() as sess:
        results = sess.run(fetches, feed_dict=placeholder_feed)

    size_tuple = type(ops["size"])(*results.pop("size_values"))
    arrays = {
        "graph": results["graph"],
        "repeated": results["repeated"],
        "sliced": results["sliced"],
        "num_graphs": results["num_graphs"],
        "size": size_tuple,
        "mask": results["mask"],
        "padded": results.get("padded"),
        "recovered": results.get("recovered"),
    }

    if placeholder_fetch is not None:
        fed = results["placeholder"]
        placeholder_info = {
            "nodes_shape": _shape(fed.nodes),
            "n_node": _tolist(fed.n_node),
            "none_fields_preserved": [
                name for name in ("edges", "senders", "receivers", "globals")
                if getattr(fed, name) is None
            ],
        }

    return _summarize_arrays(arrays, tf, graph_nets, ops, placeholder_info)


def main(argv=None):
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    np, tf, graph_nets, utils_np, utils_tf = _import_runtime()
    if _executing_eagerly(tf):
        summary = _run_eager(np, tf, graph_nets, utils_tf, args)
    else:
        summary = _run_session(np, tf, graph_nets, utils_np, utils_tf, args)
    indent = None if args.indent == 0 else args.indent
    print(json.dumps(summary, indent=indent, sort_keys=True))


if __name__ == "__main__":
    main()

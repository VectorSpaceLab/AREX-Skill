#!/usr/bin/env python3
"""Check the legacy TensorFlow graph APIs required by PointCNN.

This is a read-only probe. It never installs packages, downloads data, creates
checkpoints, enumerates devices, or runs a TensorFlow session. Exit status is
zero only when the required APIs are present, graph mode is available, and an
optional static graph smoke (when requested) succeeds.
"""

from __future__ import print_function

import argparse
import json
import sys


_REQUIRED_APIS = {
    "tf.Graph": lambda tf: hasattr(tf, "Graph"),
    "tf.Session": lambda tf: hasattr(tf, "Session"),
    "tf.placeholder": lambda tf: hasattr(tf, "placeholder"),
    "tf.get_default_graph": lambda tf: hasattr(tf, "get_default_graph"),
    "tf.py_func": lambda tf: hasattr(tf, "py_func"),
    "tf.gather_nd": lambda tf: hasattr(tf, "gather_nd"),
    "tf.cond": lambda tf: hasattr(tf, "cond"),
    "tf.nn.top_k": lambda tf: hasattr(getattr(tf, "nn", None), "top_k"),
    "tf.layers": lambda tf: hasattr(tf, "layers"),
    "tf.layers.dense": lambda tf: hasattr(getattr(tf, "layers", None), "dense"),
    "tf.layers.conv2d": lambda tf: hasattr(getattr(tf, "layers", None), "conv2d"),
    "tf.layers.separable_conv2d": lambda tf: hasattr(
        getattr(tf, "layers", None), "separable_conv2d"
    ),
    "tf.layers.dropout": lambda tf: hasattr(
        getattr(tf, "layers", None), "dropout"
    ),
    "tf.layers.batch_normalization": lambda tf: hasattr(
        getattr(tf, "layers", None), "batch_normalization"
    ),
    "tf.contrib": lambda tf: hasattr(tf, "contrib"),
    "tf.contrib.layers": lambda tf: hasattr(
        getattr(tf, "contrib", None), "layers"
    ),
    "tf.contrib.layers.separable_conv2d": lambda tf: hasattr(
        getattr(getattr(tf, "contrib", None), "layers", None), "separable_conv2d"
    ),
    "tf.load_op_library": lambda tf: hasattr(tf, "load_op_library"),
}


def _graph_mode(tf):
    """Return True/False when graph/eager mode can be established."""
    executing_eagerly = getattr(tf, "executing_eagerly", None)
    if executing_eagerly is not None:
        try:
            return not bool(executing_eagerly())
        except Exception:
            return None

    # TensorFlow 1.x predates executing_eagerly in some minor releases.  The
    # legacy top-level graph APIs plus a 1.x major version are the safe fallback
    # for this probe; graph construction below remains the decisive check.
    version = str(getattr(tf, "__version__", ""))
    if version.startswith("1.") and hasattr(tf, "Graph"):
        return True
    return None


def _api_probe(tf):
    result = {}
    for name, check in _REQUIRED_APIS.items():
        try:
            result[name] = bool(check(tf))
        except Exception:
            result[name] = False
    return result


def _graph_smoke(tf):
    """Build representative static graph fragments without running them."""
    graph = tf.Graph()
    with graph.as_default():
        is_training = tf.placeholder(tf.bool, shape=(), name="is_training")
        points = tf.placeholder(tf.float32, shape=(None, 4, 3), name="points")
        dense = tf.layers.dense(points, 4, name="dense")
        if dense.shape.as_list() != [None, 4, 4]:
            raise RuntimeError("unexpected dense shape: %s" % dense.shape)

        # The X-Conv algebra applies 2-D kernels to [N, P, K, C] tensors.
        neighborhood = tf.reshape(dense, (-1, 1, 4, 4), name="neighborhood")
        separable = tf.layers.separable_conv2d(
            neighborhood, 4, kernel_size=(1, 4), padding="VALID", name="separable"
        )
        if separable.shape.as_list() != [None, 1, 1, 4]:
            raise RuntimeError("unexpected separable-conv shape: %s" % separable.shape)

        # Exercise the legacy contrib symbol used by pointfly's depthwise path.
        depthwise = tf.contrib.layers.separable_conv2d(
            neighborhood, num_outputs=None, kernel_size=(1, 4), padding="VALID",
            scope="depthwise",
        )
        if depthwise.shape.ndims != 4:
            raise RuntimeError("unexpected depthwise rank: %s" % depthwise.shape)

        # Keep the control dependency in the graph so placeholder/cond APIs are
        # covered without executing a session.
        tf.cond(is_training, lambda: tf.identity(separable), lambda: separable)
    return True


def _finish(result, as_json, code):
    if as_json:
        print(json.dumps(result, sort_keys=True))
        return code

    print("status: %s" % result["status"])
    print("tensorflow: %s" % result["tensorflow_version"])
    print("graph_mode: %s" % result["graph_mode"])
    print("cuda_build: %s" % result["cuda_build"])
    print("required_apis:")
    for name in sorted(result["required_apis"]):
        print("  %s: %s" % (name, result["required_apis"][name]))
    print("graph_smoke: %s" % result["graph_smoke"])
    for note in result["notes"]:
        print("note: %s" % note)
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Check TensorFlow 1.x graph APIs used by PointCNN without installing "
            "packages, downloading data, enumerating devices, or running a session."
        )
    )
    parser.add_argument(
        "--graph-smoke",
        action="store_true",
        help="build representative dense/separable-convolution graph fragments",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit one JSON object instead of a report"
    )
    args = parser.parse_args(argv)

    result = {
        "status": "blocked",
        "tensorflow_imported": False,
        "tensorflow_version": None,
        "graph_mode": None,
        "cuda_build": None,
        "required_apis": {},
        "graph_smoke": "not-requested",
        "notes": [],
    }

    try:
        import tensorflow as tf
    except Exception as exc:  # pragma: no cover - depends on host installation
        result["notes"].append(
            "TensorFlow import failed: %s" % str(exc).splitlines()[0]
        )
        return _finish(result, args.json, 2)

    result["tensorflow_imported"] = True
    result["tensorflow_version"] = getattr(tf, "__version__", "unknown")
    result["graph_mode"] = _graph_mode(tf)

    built_with_cuda = getattr(getattr(tf, "test", None), "is_built_with_cuda", None)
    if built_with_cuda is not None:
        try:
            result["cuda_build"] = bool(built_with_cuda())
        except Exception:
            result["cuda_build"] = "probe-error"

    result["required_apis"] = _api_probe(tf)
    missing = [
        name for name, present in result["required_apis"].items() if not present
    ]
    if missing:
        result["notes"].append("Missing legacy APIs: %s" % ", ".join(sorted(missing)))

    graph_ok = True
    if args.graph_smoke:
        try:
            _graph_smoke(tf)
            result["graph_smoke"] = "passed"
        except Exception as exc:
            graph_ok = False
            result["graph_smoke"] = "failed"
            result["notes"].append(
                "Static graph construction failed: %s" % str(exc).splitlines()[0]
            )

    if result["graph_mode"] is False:
        result["notes"].append(
            "Eager execution is enabled; PointCNN requires TensorFlow 1.x graph mode."
        )
    elif result["graph_mode"] is None:
        result["notes"].append(
            "Could not establish graph mode from this TensorFlow API."
        )

    api_ok = not missing
    graph_mode_ok = result["graph_mode"] is True
    if api_ok and graph_mode_ok and graph_ok:
        result["status"] = "ok"
        return _finish(result, args.json, 0)

    result["notes"].append(
        "This probe does not test GPU discovery, custom-op loading, or kernel execution."
    )
    return _finish(result, args.json, 2)


if __name__ == "__main__":
    sys.exit(main())

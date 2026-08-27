#!/usr/bin/env python
"""Tiny GraphIndependent smoke for an installed Graph Nets package.

The script is self-contained and does not read a source checkout. It prints JSON
summarizing TensorFlow/Sonnet/Graph Nets versions, execution mode, and output
shapes/sums for a tiny feature-only GraphIndependent model.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json
import re
import sys


def _clean_error(text):
  """Avoid printing machine-specific absolute paths in JSON errors."""
  return re.sub(r"(?<![A-Za-z0-9_])/(?:[^\s:;,)]+/)+[^\s:;,)]+", "<path>", str(text))


def _load_deps():
  import graph_nets  # pylint: disable=import-outside-toplevel
  from graph_nets import modules  # pylint: disable=import-outside-toplevel
  from graph_nets import utils_tf  # pylint: disable=import-outside-toplevel
  import numpy as np  # pylint: disable=import-outside-toplevel
  import sonnet as snt  # pylint: disable=import-outside-toplevel
  import tensorflow as tf  # pylint: disable=import-outside-toplevel
  return graph_nets, modules, utils_tf, np, snt, tf


def _tiny_graph(utils_tf):
  return utils_tf.data_dicts_to_graphs_tuple([{
      "globals": [0.5, -0.5],
      "nodes": [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
      "edges": [[0.2, 0.3], [0.4, 0.5]],
      "senders": [0, 1],
      "receivers": [1, 2],
  }])


def _affine(scale, offset):
  def apply(x):
    return x * scale + offset
  return apply


def _model(modules):
  return modules.GraphIndependent(
      edge_model_fn=lambda: _affine(2.0, 1.0),
      node_model_fn=lambda: _affine(3.0, -1.0),
      global_model_fn=lambda: _affine(0.5, 2.0),
      name="graph_model_smoke")


def _set_seed(tf):
  if hasattr(tf, "random") and hasattr(tf.random, "set_seed"):
    tf.random.set_seed(0)
  elif hasattr(tf, "set_random_seed"):
    tf.set_random_seed(0)


def _reset_graph(tf):
  if hasattr(tf, "reset_default_graph"):
    tf.reset_default_graph()
  elif hasattr(tf, "compat") and hasattr(tf.compat, "v1"):
    tf.compat.v1.reset_default_graph()


def _session_cls(tf):
  if hasattr(tf, "Session"):
    return tf.Session
  if hasattr(tf, "compat") and hasattr(tf.compat, "v1"):
    return tf.compat.v1.Session
  return None


def _global_variables_initializer(tf):
  if hasattr(tf, "global_variables_initializer"):
    return tf.global_variables_initializer
  if hasattr(tf, "compat") and hasattr(tf.compat, "v1"):
    return tf.compat.v1.global_variables_initializer
  return None


def _field_summary(np_module, value):
  arr = np_module.asarray(value)
  return {
      "shape": list(arr.shape),
      "sum": float(arr.sum()),
  }


def _payload_base(graph_nets, snt, tf):
  return {
      "graph_nets_version": getattr(graph_nets, "__version__", None),
      "tensorflow_version": getattr(tf, "__version__", None),
      "sonnet_version": getattr(snt, "__version__", None),
  }


def _run_tf2_eager(graph_nets, modules, utils_tf, np_module, snt, tf):
  if not getattr(tf, "executing_eagerly", lambda: False)():
    raise RuntimeError("TensorFlow eager execution is not enabled")
  _set_seed(tf)
  graph = _tiny_graph(utils_tf)
  output = _model(modules)(graph)
  payload = _payload_base(graph_nets, snt, tf)
  payload.update({
      "ok": True,
      "mode": "tf2-eager",
      "edges": _field_summary(np_module, output.edges.numpy()),
      "nodes": _field_summary(np_module, output.nodes.numpy()),
      "globals": _field_summary(np_module, output.globals.numpy()),
      "n_node": np_module.asarray(output.n_node.numpy()).astype(int).tolist(),
      "n_edge": np_module.asarray(output.n_edge.numpy()).astype(int).tolist(),
  })
  return payload


def _run_tf1_session(graph_nets, modules, utils_tf, np_module, snt, tf, disable_eager=False):
  if disable_eager:
    if not (hasattr(tf, "compat") and hasattr(tf.compat, "v1") and
            hasattr(tf.compat.v1, "disable_eager_execution")):
      raise RuntimeError("Cannot disable eager execution in this TensorFlow build")
    tf.compat.v1.disable_eager_execution()
  _reset_graph(tf)
  _set_seed(tf)
  sess_cls = _session_cls(tf)
  init_fn = _global_variables_initializer(tf)
  if sess_cls is None or init_fn is None:
    raise RuntimeError("TensorFlow session APIs are unavailable")
  graph = _tiny_graph(utils_tf)
  output = _model(modules)(graph)
  with sess_cls() as sess:
    sess.run(init_fn())
    result = sess.run(output)
  payload = _payload_base(graph_nets, snt, tf)
  payload.update({
      "ok": True,
      "mode": "tf1-session",
      "edges": _field_summary(np_module, result.edges),
      "nodes": _field_summary(np_module, result.nodes),
      "globals": _field_summary(np_module, result.globals),
      "n_node": np_module.asarray(result.n_node).astype(int).tolist(),
      "n_edge": np_module.asarray(result.n_edge).astype(int).tolist(),
  })
  return payload


def run(mode="auto"):
  graph_nets, modules, utils_tf, np_module, snt, tf = _load_deps()
  eager = getattr(tf, "executing_eagerly", lambda: False)()
  if mode == "tf2-eager":
    return _run_tf2_eager(graph_nets, modules, utils_tf, np_module, snt, tf)
  if mode == "tf1-session":
    return _run_tf1_session(
        graph_nets, modules, utils_tf, np_module, snt, tf,
        disable_eager=bool(eager))
  if eager:
    return _run_tf2_eager(graph_nets, modules, utils_tf, np_module, snt, tf)
  return _run_tf1_session(graph_nets, modules, utils_tf, np_module, snt, tf)


def main(argv=None):
  parser = argparse.ArgumentParser(
      description="Run a tiny GraphIndependent smoke and emit JSON.")
  parser.add_argument(
      "--mode",
      choices=["auto", "tf1-session", "tf2-eager"],
      default="auto",
      help="Execution style. Default chooses TF2 eager when eager is enabled, otherwise TF1 session.")
  parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
  args = parser.parse_args(argv)
  try:
    payload = run(args.mode)
  except Exception as exc:  # pylint: disable=broad-except
    payload = {
        "ok": False,
        "error_type": type(exc).__name__,
        "error": _clean_error(exc),
    }
  print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
  return 0 if payload.get("ok") else 1


if __name__ == "__main__":
  raise SystemExit(main(sys.argv[1:]))

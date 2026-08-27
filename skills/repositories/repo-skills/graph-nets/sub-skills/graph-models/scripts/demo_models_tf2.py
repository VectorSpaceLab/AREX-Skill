#!/usr/bin/env python
"""TF2/Sonnet2 demo graph model constructors for Graph Nets.

Adapted from the public DeepMind Graph Nets TF2 demo model architectures and
bundled with this skill so future agents do not need a source checkout or
notebooks to reuse the architecture pattern.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json

from six.moves import range

_IMPORT_ERROR = None
try:
  import graph_nets
  from graph_nets import modules
  from graph_nets import utils_tf
  import sonnet as snt
  import tensorflow as tf
except Exception as exc:  # pylint: disable=broad-except
  _IMPORT_ERROR = exc
  graph_nets = None
  modules = None
  utils_tf = None
  snt = None
  tf = None

NUM_LAYERS = 2
LATENT_SIZE = 16


def _require_deps():
  if _IMPORT_ERROR is not None:
    raise RuntimeError("required Graph Nets/TensorFlow/Sonnet packages are unavailable: {}".format(_IMPORT_ERROR))


def _sonnet_major():
  _require_deps()
  return int(getattr(snt, "__version__", "0").split(".")[0])


def _require_sonnet2():
  _require_deps()
  if _sonnet_major() != 2 or not hasattr(snt, "Module"):
    raise RuntimeError(
        "demo_models_tf2.py requires Sonnet 2.x with snt.Module; "
        "use demo_models_tf1.py in Sonnet 1 environments")


def make_mlp_model():
  """Instantiates a new MLP followed by LayerNorm.

  Parameters are not shared across independent calls to this factory.
  """
  _require_sonnet2()
  return snt.Sequential([
      snt.nets.MLP([LATENT_SIZE] * NUM_LAYERS, activate_final=True),
      snt.LayerNorm(axis=-1, create_offset=True, create_scale=True),
  ])


if snt is not None and hasattr(snt, "Module"):

  class MLPGraphIndependent(snt.Module):
    """GraphIndependent with MLP edge, node, and global models."""

    def __init__(self, name="MLPGraphIndependent"):
      _require_sonnet2()
      super(MLPGraphIndependent, self).__init__(name=name)
      self._network = modules.GraphIndependent(
          edge_model_fn=make_mlp_model,
          node_model_fn=make_mlp_model,
          global_model_fn=make_mlp_model)

    def __call__(self, inputs):
      return self._network(inputs)


  class MLPGraphNetwork(snt.Module):
    """GraphNetwork with MLP edge, node, and global models."""

    def __init__(self, name="MLPGraphNetwork"):
      _require_sonnet2()
      super(MLPGraphNetwork, self).__init__(name=name)
      self._network = modules.GraphNetwork(
          make_mlp_model, make_mlp_model, make_mlp_model)

    def __call__(self, inputs):
      return self._network(inputs)


  class EncodeProcessDecode(snt.Module):
    """Full encode-process-decode graph network.

    The model independently encodes graph fields, repeatedly applies a core
    message-passing GraphNetwork to the concatenation of the initial and current
    latent graphs, decodes every processing step, and optionally projects output
    fields to requested sizes.
    """

    def __init__(self,
                 edge_output_size=None,
                 node_output_size=None,
                 global_output_size=None,
                 name="EncodeProcessDecode"):
      _require_sonnet2()
      super(EncodeProcessDecode, self).__init__(name=name)
      self._encoder = MLPGraphIndependent()
      self._core = MLPGraphNetwork()
      self._decoder = MLPGraphIndependent()
      edge_fn = None if edge_output_size is None else (
          lambda: snt.Linear(edge_output_size, name="edge_output"))
      node_fn = None if node_output_size is None else (
          lambda: snt.Linear(node_output_size, name="node_output"))
      global_fn = None if global_output_size is None else (
          lambda: snt.Linear(global_output_size, name="global_output"))
      self._output_transform = modules.GraphIndependent(
          edge_fn, node_fn, global_fn)

    def __call__(self, input_op, num_processing_steps):
      latent = self._encoder(input_op)
      latent0 = latent
      output_ops = []
      for _ in range(num_processing_steps):
        core_input = utils_tf.concat([latent0, latent], axis=1)
        latent = self._core(core_input)
        decoded_op = self._decoder(latent)
        output_ops.append(self._output_transform(decoded_op))
      return output_ops

else:

  class MLPGraphIndependent(object):
    def __init__(self, *args, **kwargs):
      _require_sonnet2()


  class MLPGraphNetwork(object):
    def __init__(self, *args, **kwargs):
      _require_sonnet2()


  class EncodeProcessDecode(object):
    def __init__(self, *args, **kwargs):
      _require_sonnet2()


def _tiny_graph():
  return utils_tf.data_dicts_to_graphs_tuple([{
      "globals": [0.5, -0.5],
      "nodes": [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
      "edges": [[0.2, 0.3], [0.4, 0.5]],
      "senders": [0, 1],
      "receivers": [1, 2],
  }])


def _shape(tensor):
  return list(tensor.shape.as_list() if hasattr(tensor.shape, "as_list")
              else tensor.shape)


def smoke(processing_steps=2):
  """Runs a tiny TF2 eager smoke and returns JSON-serializable metadata."""
  _require_sonnet2()
  if not getattr(tf, "executing_eagerly", lambda: False)():
    raise RuntimeError("demo_models_tf2.py expects TensorFlow eager execution")
  if hasattr(tf.random, "set_seed"):
    tf.random.set_seed(0)
  model = EncodeProcessDecode(
      edge_output_size=2, node_output_size=3, global_output_size=1)
  outputs = model(_tiny_graph(), processing_steps)
  result = outputs[-1]
  return {
      "ok": True,
      "script": "demo_models_tf2",
      "graph_nets_version": getattr(graph_nets, "__version__", None),
      "tensorflow_version": getattr(tf, "__version__", None),
      "sonnet_version": getattr(snt, "__version__", None),
      "processing_steps": processing_steps,
      "edge_shape": _shape(result.edges),
      "node_shape": _shape(result.nodes),
      "global_shape": _shape(result.globals),
  }


def main(argv=None):
  parser = argparse.ArgumentParser(
      description="Instantiate the bundled TF2/Sonnet2 Graph Nets demo model.")
  parser.add_argument("--processing-steps", type=int, default=2)
  parser.add_argument("--pretty", action="store_true")
  args = parser.parse_args(argv)
  try:
    payload = smoke(args.processing_steps)
  except Exception as exc:  # pylint: disable=broad-except
    payload = {
        "ok": False,
        "script": "demo_models_tf2",
        "error_type": type(exc).__name__,
        "error": str(exc),
        "tensorflow_version": getattr(tf, "__version__", None),
        "sonnet_version": getattr(snt, "__version__", None),
    }
  print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
  return 0 if payload.get("ok") else 1


if __name__ == "__main__":
  raise SystemExit(main())

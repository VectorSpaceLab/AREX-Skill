#!/usr/bin/env python3
"""Check that the active Python can import and minimally use Sonnet."""
from __future__ import annotations
import argparse, json, sys

def positive_int(value: str) -> int:
  parsed = int(value)
  if parsed <= 0: raise argparse.ArgumentTypeError("must be a positive integer")
  return parsed

def main() -> int:
  parser = argparse.ArgumentParser(description="Run a no-download import and API smoke check for dm-sonnet.")
  parser.add_argument("--batch-size", type=positive_int, default=2)
  parser.add_argument("--input-size", type=positive_int, default=4)
  parser.add_argument("--hidden-size", type=positive_int, default=5)
  parser.add_argument("--json", action="store_true")
  args = parser.parse_args()
  try:
    import tensorflow as tf
    import sonnet as snt
  except ModuleNotFoundError as exc:
    print("Import failed. Install with: python -m pip install tensorflow dm-sonnet", file=sys.stderr)
    print(f"Missing module: {exc.name}", file=sys.stderr)
    return 2
  tf.random.set_seed(23)
  x = tf.ones([args.batch_size, args.input_size], dtype=tf.float32)
  mlp = snt.nets.MLP([args.hidden_size, 2])
  y = mlp(x)
  opt = snt.optimizers.SGD(0.01)
  with tf.GradientTape() as tape:
    loss = tf.reduce_mean(tf.square(mlp(x)))
  opt.apply(tape.gradient(loss, mlp.trainable_variables), mlp.trainable_variables)
  seq = tf.ones([3, args.batch_size, args.input_size], dtype=tf.float32)
  core = snt.LSTM(args.hidden_size)
  out, state = snt.dynamic_unroll(core, seq, core.initial_state(args.batch_size))
  summary = {
    "status":"ok", "python":sys.version.split()[0], "tensorflow_version":tf.__version__,
    "sonnet_version":getattr(snt,"__version__","unknown"),
    "devices":[d.device_type for d in tf.config.list_physical_devices()],
    "mlp_output_shape":y.shape.as_list(), "mlp_trainable_variable_count":len(mlp.trainable_variables),
    "optimizer_step_loss":float(loss.numpy()), "rnn_output_shape":out.shape.as_list(),
    "rnn_state_shapes":{"hidden":state.hidden.shape.as_list(), "cell":state.cell.shape.as_list()}}
  print(json.dumps(summary, sort_keys=True if args.json else False, indent=None if args.json else 2))
  return 0
if __name__ == "__main__": raise SystemExit(main())

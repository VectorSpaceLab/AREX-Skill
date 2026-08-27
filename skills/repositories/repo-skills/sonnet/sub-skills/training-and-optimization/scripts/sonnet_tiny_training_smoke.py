#!/usr/bin/env python3
"""Train a tiny Sonnet model on deterministic synthetic data."""
from __future__ import annotations
import argparse, json
import tensorflow as tf
import sonnet as snt

def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--steps", type=int, default=40)
  parser.add_argument("--json", action="store_true")
  args = parser.parse_args()
  tf.random.set_seed(11)
  x = tf.reshape(tf.linspace(-1.0, 1.0, 64), [32, 2])
  y = tf.reduce_sum(x, axis=1, keepdims=True)
  model = snt.Linear(1)
  opt = snt.optimizers.SGD(0.1)
  def loss_value():
    return tf.reduce_mean(tf.square(model(x) - y))
  _ = model(x)
  initial = float(loss_value().numpy())
  for _step in range(args.steps):
    with tf.GradientTape() as tape:
      loss = tf.reduce_mean(tf.square(model(x) - y))
    opt.apply(tape.gradient(loss, model.trainable_variables), model.trainable_variables)
  final = float(loss_value().numpy())
  assert final < initial, (initial, final)
  out = {"status":"ok","initial_loss":initial,"final_loss":final,"variable_count":len(model.trainable_variables)}
  print(json.dumps(out, indent=None if args.json else 2, sort_keys=args.json))
  return 0
if __name__ == "__main__":
  raise SystemExit(main())

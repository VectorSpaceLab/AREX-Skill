#!/usr/bin/env python3
"""No-download Sonnet functional transform and optimizer smoke check."""
from __future__ import annotations
import argparse, json
import tensorflow as tf
import sonnet as snt

fn = snt.functional

def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--steps", type=int, default=5)
  parser.add_argument("--json", action="store_true")
  args = parser.parse_args()
  tf.random.set_seed(19)
  x = tf.reshape(tf.linspace(-1.0, 1.0, 12), [4, 3])
  target = tf.ones([4, 1])
  with fn.variables():
    net = snt.nets.MLP([4, 1])
  def loss_fn(inputs, labels):
    pred = net(inputs)
    return tf.reduce_mean(tf.square(pred - labels))
  transformed = fn.transform(loss_fn)
  optimizer = fn.sgd(0.05)
  params = transformed.init(x, target)
  opt_state = optimizer.init(params)
  grad_apply = fn.value_and_grad(transformed.apply)
  initial, _ = grad_apply(params, x, target)
  loss = initial
  for _ in range(args.steps):
    loss, grads = grad_apply(params, x, target)
    params, opt_state = optimizer.apply(opt_state, grads, params)
  final, _ = grad_apply(params, x, target)
  assert float(final.numpy()) < float(initial.numpy()), (float(initial.numpy()), float(final.numpy()))
  out = {"status":"ok","initial_loss":float(initial.numpy()),"final_loss":float(final.numpy()),"param_tree_type":type(params).__name__}
  print(json.dumps(out, indent=None if args.json else 2, sort_keys=args.json))
  return 0
if __name__ == "__main__":
  raise SystemExit(main())

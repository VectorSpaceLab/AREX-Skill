#!/usr/bin/env python3
"""No-download Sonnet built-in layer/net shape and state smoke check."""
from __future__ import annotations
import argparse, json
import tensorflow as tf
import sonnet as snt

def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--json", action="store_true")
  args = parser.parse_args()
  tf.random.set_seed(7)
  linear = snt.Linear(3, name="linear_smoke")
  dense = linear(tf.ones([2, 4]))
  mlp = snt.nets.MLP([8, 2])
  logits = mlp(tf.ones([2, 4]))
  conv = snt.Conv2D(4, kernel_shape=3, padding="SAME", with_bias=False)
  bn = snt.BatchNorm(create_scale=True, create_offset=True)
  image = tf.ones([2, 6, 6, 3])
  conv_out = conv(image)
  normed = bn(conv_out, is_training=True)
  flat = snt.Flatten()(normed)
  assert dense.shape.as_list() == [2, 3]
  assert logits.shape.as_list() == [2, 2]
  assert conv_out.shape.as_list() == [2, 6, 6, 4]
  assert flat.shape.as_list() == [2, 6 * 6 * 4]
  out = {"status":"ok","linear_shape":dense.shape.as_list(),"mlp_shape":logits.shape.as_list(),"conv_shape":conv_out.shape.as_list(),"batch_norm_variables":len(bn.variables)}
  print(json.dumps(out, indent=None if args.json else 2, sort_keys=args.json))
  return 0
if __name__ == "__main__":
  raise SystemExit(main())

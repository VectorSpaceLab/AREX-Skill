#!/usr/bin/env python3
"""No-download Sonnet custom-module and composition smoke check."""
from __future__ import annotations
import argparse, json
import tensorflow as tf
import sonnet as snt

class LazyAffine(snt.Module):
  def __init__(self, output_size: int, name=None):
    super().__init__(name=name)
    self.output_size = output_size
  @snt.once
  def _initialize(self, x):
    in_size = x.shape[-1]
    if in_size is None:
      raise ValueError("final input dimension must be statically known")
    self.w = tf.Variable(tf.ones([in_size, self.output_size]), name="w")
    self.b = tf.Variable(tf.zeros([self.output_size]), name="b")
  def __call__(self, x):
    self._initialize(x)
    return tf.matmul(x, self.w) + self.b

def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--json", action="store_true")
  args = parser.parse_args()
  module = LazyAffine(3, name="lazy_affine")
  try:
    _ = module.trainable_variables
    raises_before_build = False
  except ValueError:
    raises_before_build = True
  y1 = module(tf.ones([2, 4]))
  y2 = module(tf.ones([2, 4]))
  batch_linear = snt.BatchApply(snt.Linear(5), num_dims=2)
  z = batch_linear(tf.ones([2, 3, 4]))
  assert raises_before_build
  assert y1.shape.as_list() == [2, 3] and y2.shape.as_list() == [2, 3]
  assert len(module.trainable_variables) == 2
  assert z.shape.as_list() == [2, 3, 5]
  out = {"status":"ok","raises_before_build":raises_before_build,"lazy_variables":len(module.trainable_variables),"output_shape":y1.shape.as_list(),"batch_apply_shape":z.shape.as_list()}
  print(json.dumps(out, indent=None if args.json else 2, sort_keys=args.json))
  return 0
if __name__ == "__main__":
  raise SystemExit(main())

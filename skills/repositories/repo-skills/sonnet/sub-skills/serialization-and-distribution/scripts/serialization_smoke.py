#!/usr/bin/env python3
"""CPU checkpoint and SavedModel smoke for a tiny Sonnet module."""
from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path
import tensorflow as tf
import sonnet as snt

class ExportModule(tf.Module):
  def __init__(self, model):
    super().__init__()
    self.model = model
  @tf.function(input_signature=[tf.TensorSpec([None, 4], tf.float32)])
  def __call__(self, x):
    return self.model(x)

def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--keep-temp", action="store_true")
  parser.add_argument("--json", action="store_true")
  args = parser.parse_args()
  model = snt.nets.MLP([5, 2])
  x = tf.ones([2, 4])
  y = model(x)
  with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    ckpt = tf.train.Checkpoint(model=model)
    save_path = ckpt.save(str(tmp_path / "ckpt"))
    restored = snt.nets.MLP([5, 2])
    restored(x)
    tf.train.Checkpoint(model=restored).restore(save_path).assert_existing_objects_matched()
    restored_y = restored(x)
    saved_model_dir = tmp_path / "saved_model"
    tf.saved_model.save(ExportModule(model), str(saved_model_dir))
    loaded = tf.saved_model.load(str(saved_model_dir))
    loaded_y = loaded(x)
    assert y.shape.as_list() == [2, 2]
    assert tf.reduce_max(tf.abs(y - restored_y)).numpy() < 1e-5
    assert loaded_y.shape.as_list() == [2, 2]
    out = {"status":"ok","checkpoint_prefix":Path(save_path).name,"output_shape":y.shape.as_list(),"saved_model_output_shape":loaded_y.shape.as_list()}
    if args.keep_temp:
      print("--keep-temp is accepted for CLI compatibility; temporary data is still removed by default smoke design.")
  print(json.dumps(out, indent=None if args.json else 2, sort_keys=args.json))
  return 0
if __name__ == "__main__":
  raise SystemExit(main())

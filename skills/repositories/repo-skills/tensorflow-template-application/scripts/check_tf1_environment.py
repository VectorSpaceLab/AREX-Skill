#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import argparse
import json
import os
import sys
import tempfile
import warnings

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


def _distribution_version(name):
  try:
    from importlib_metadata import version as metadata_version
  except Exception:
    try:
      from importlib.metadata import version as metadata_version  # type: ignore
    except Exception:
      metadata_version = None

  if metadata_version is None:
    return "unknown"

  try:
    return metadata_version(name)
  except Exception:
    return "unknown"


def _check_tfrecord_smoke(tf_module):
  tf_v1 = getattr(getattr(tf_module, "compat", None), "v1", tf_module)
  tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tfrecord")
  tmp_path = tmp.name
  tmp.close()
  try:
    writer = tf_v1.python_io.TFRecordWriter(tmp_path)
    example = tf_v1.train.Example(
        features=tf_v1.train.Features(
            feature={
                "label": tf_v1.train.Feature(
                    int64_list=tf_v1.train.Int64List(value=[1])),
                "features": tf_v1.train.Feature(
                    float_list=tf_v1.train.FloatList(value=[1.0, 2.0])),
            }))
    writer.write(example.SerializeToString())
    writer.close()
    dataset = tf_v1.data.TFRecordDataset([tmp_path])
    iterator = tf_v1.data.make_one_shot_iterator(dataset)
    next_record = iterator.get_next()
    count = 0
    with warnings.catch_warnings():
      warnings.simplefilter("ignore")
      with tf_v1.Session() as sess:
        while True:
          try:
            sess.run(next_record)
            count += 1
          except tf_v1.errors.OutOfRangeError:
            break
    return {"status": "passed" if count == 1 else "failed", "records": count}
  finally:
    try:
      os.remove(tmp_path)
    except OSError:
      pass


def _check_serving_imports():
  from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc
  return {
      "predict_pb2": hasattr(predict_pb2, "PredictRequest"),
      "prediction_service_pb2_grpc": hasattr(prediction_service_pb2_grpc,
                                             "PredictionServiceStub"),
  }


def build_parser():
  parser = argparse.ArgumentParser(
      description="Check the TensorFlow 1.x template environment.")
  parser.add_argument("--check-serving",
                      action="store_true",
                      help="Also verify the TensorFlow Serving Python imports.")
  parser.add_argument("--skip-tfrecord-smoke",
                      action="store_true",
                      help="Skip the tiny TFRecord write/read smoke check.")
  parser.add_argument("--json",
                      action="store_true",
                      help="Emit machine-readable JSON instead of human output.")
  return parser


def main(argv=None):
  args = build_parser().parse_args(argv)

  try:
    import trainer  # noqa: F401
    import tensorflow as tf
  except Exception as exc:
    print("Core import failed: {}".format(exc), file=sys.stderr)
    return 2

  tf1_symbols = {
      "app": tf.__dict__.get("app") is not None,
      "Session": tf.__dict__.get("Session") is not None,
      "contrib": tf.__dict__.get("contrib") is not None,
      "python_io": tf.__dict__.get("python_io") is not None,
  }

  report = {
      "python": sys.version.split()[0],
      "executable": sys.executable,
      "trainer_version": _distribution_version("trainer"),
      "tensorflow_version": getattr(tf, "__version__", "unknown"),
      "tf1_symbols": tf1_symbols,
  }

  if not args.skip_tfrecord_smoke:
    report["tfrecord_smoke"] = _check_tfrecord_smoke(tf)
    if report["tfrecord_smoke"]["status"] != "passed":
      print("TFRecord smoke failed: {}".format(report["tfrecord_smoke"]),
            file=sys.stderr)
      return 2
  else:
    report["tfrecord_smoke"] = {"status": "skipped"}

  if args.check_serving:
    try:
      report["serving_imports"] = _check_serving_imports()
    except Exception as exc:
      print("Serving import check failed: {}".format(exc), file=sys.stderr)
      return 2
  else:
    report["serving_imports"] = {"status": "skipped"}

  if args.json:
    print(json.dumps(report, indent=2, sort_keys=True))
  else:
    print("trainer_version: {}".format(report["trainer_version"]))
    print("tensorflow_version: {}".format(report["tensorflow_version"]))
    print("tf1_symbols: {}".format(report["tf1_symbols"]))
    print("tfrecord_smoke: {}".format(report["tfrecord_smoke"]))
    print("serving_imports: {}".format(report["serving_imports"]))

  return 0


if __name__ == "__main__":
  sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import argparse
import json
import re
import sys

import tensorflow as tf

DEFAULT_FEATURE_ROWS = "1,2,3,4,5,6,7,8,9;1,1,1,1,1,1,1,1,1;9,8,7,6,5,4,3,2,1;9,9,9,9,9,9,9,9,9"


def _parse_int_list(text):
  values = []
  for item in text.split(","):
    item = item.strip()
    if item:
      values.append(int(item))
  if not values:
    raise ValueError("no keys were provided")
  return values


def _parse_feature_rows(text=None, file_path=None):
  if file_path:
    with open(file_path, "r") as handle:
      raw_rows = [line.strip() for line in handle if line.strip()]
  else:
    if text is None:
      text = DEFAULT_FEATURE_ROWS
    raw_rows = [chunk.strip() for chunk in re.split(r"[;\n]+", text) if chunk.strip()]

  rows = []
  for raw_row in raw_rows:
    cells = [cell.strip() for cell in raw_row.split(",") if cell.strip()]
    if not cells:
      continue
    rows.append([float(cell) for cell in cells])

  if not rows:
    raise ValueError("no feature rows were provided")

  width = len(rows[0])
  for index, row in enumerate(rows, start=1):
    if len(row) != width:
      raise ValueError("row {} has width {}, expected {}".format(
          index, len(row), width))

  return rows


def _build_request(keys, feature_rows, model_name, model_version, signature_name):
  from tensorflow_serving.apis import predict_pb2

  keys_proto = tf.compat.v1.make_tensor_proto(keys, dtype=tf.int32)
  features_proto = tf.compat.v1.make_tensor_proto(feature_rows, dtype=tf.float32)

  request = predict_pb2.PredictRequest()
  request.model_spec.name = model_name
  if model_version > 0:
    request.model_spec.version.value = model_version
  if signature_name:
    request.model_spec.signature_name = signature_name
  request.inputs["keys"].CopyFrom(keys_proto)
  request.inputs["features"].CopyFrom(features_proto)
  return request


def _summarize_request(keys, feature_rows, args):
  return {
      "mode": "dense",
      "transport": "dry-run",
      "model_spec": {
          "name": args.model_name,
          "version": args.model_version if args.model_version > 0 else None,
          "signature_name": args.signature_name or None,
      },
      "inputs": {
          "keys": {
              "dtype": "int32",
              "shape": [len(keys), 1],
              "values": [[key] for key in keys],
          },
          "features": {
              "dtype": "float32",
              "shape": [len(feature_rows), len(feature_rows[0])],
              "values": feature_rows,
          },
      },
      "host": args.host,
      "port": args.port,
      "timeout": args.timeout,
  }


def _send_request(request, host, port, timeout):
  import grpc
  from tensorflow_serving.apis import prediction_service_pb2_grpc

  channel = grpc.insecure_channel("{}:{}".format(host, port))
  stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
  return stub.Predict(request, timeout)


def build_parser():
  parser = argparse.ArgumentParser(
      description="Inspect or send the dense TensorFlow Serving request.")
  parser.add_argument("--host", default="127.0.0.1", help="TensorFlow Serving host.")
  parser.add_argument("--port", type=int, default=9000, help="TensorFlow Serving port.")
  parser.add_argument("--model-name", default="dense", help="Exported model name.")
  parser.add_argument("--model-version", type=int, default=1, help="Model version to request; <=0 leaves it unset.")
  parser.add_argument("--signature-name", default="", help="Optional signature name.")
  parser.add_argument("--timeout", type=float, default=10.0, help="gRPC timeout in seconds.")
  parser.add_argument("--keys", default="1,2,3,4", help="Comma-separated int32 keys.")
  parser.add_argument("--features", default=DEFAULT_FEATURE_ROWS, help="Semicolon-separated dense rows, each row comma-separated.")
  parser.add_argument("--features-file", default="", help="Read dense rows from a file, one row per line.")
  parser.add_argument("--send", action="store_true", help="Send the request to a running TensorFlow Serving process.")
  return parser


def main(argv=None):
  args = build_parser().parse_args(argv)
  try:
    feature_rows = _parse_feature_rows(args.features, args.features_file or None)
    keys = _parse_int_list(args.keys)
    if len(keys) != len(feature_rows):
      raise ValueError("keys length {} does not match feature rows {}".format(
          len(keys), len(feature_rows)))
    request = _build_request(keys, feature_rows, args.model_name,
                             args.model_version, args.signature_name)
  except (OSError, ValueError) as exc:
    print("Dense request build failed: {}".format(exc), file=sys.stderr)
    return 1

  if not args.send:
    print(json.dumps(_summarize_request(keys, feature_rows, args), indent=2, sort_keys=True))
    return 0

  try:
    response = _send_request(request, args.host, args.port, args.timeout)
  except Exception as exc:
    print("Dense request failed: {}".format(exc), file=sys.stderr)
    return 2

  print(response)
  return 0


if __name__ == "__main__":
  sys.exit(main())

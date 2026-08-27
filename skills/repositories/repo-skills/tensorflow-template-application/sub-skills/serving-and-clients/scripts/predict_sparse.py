#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import argparse
import json
import re
import sys

import tensorflow as tf

DEFAULT_EXAMPLES = (
    "0 5:1 6:1 17:1 21:1 35:1 40:1 53:1 63:1 71:1 73:1 74:1 76:1 80:1 83:1;"
    "1 5:1 7:1 17:1 22:1 36:1 40:1 51:1 63:1 67:1 73:1 74:1 76:1 81:1 83:1"
)


def _parse_int_list(text):
  values = []
  for item in text.split(","):
    item = item.strip()
    if item:
      values.append(int(item))
  if not values:
    raise ValueError("no keys were provided")
  return values


def _parse_sparse_rows(text=None, file_path=None):
  if file_path:
    with open(file_path, "r") as handle:
      raw_rows = [line.strip() for line in handle if line.strip()]
  else:
    if text is None:
      text = DEFAULT_EXAMPLES
    raw_rows = [chunk.strip() for chunk in re.split(r"[;\n]+", text) if chunk.strip()]

  rows = []
  for raw_row in raw_rows:
    tokens = raw_row.split()
    if len(tokens) < 2:
      raise ValueError("sparse row {!r} needs a label and at least one id:value pair".format(raw_row))
    label = int(float(tokens[0]))
    pairs = []
    for token in tokens[1:]:
      if token.startswith("#"):
        break
      if ":" not in token:
        raise ValueError("sparse token {!r} is missing ':'".format(token))
      feature_id, feature_value = token.split(":", 1)
      pairs.append((int(feature_id), float(feature_value)))
    if not pairs:
      raise ValueError("sparse row {!r} did not contain any feature pairs".format(raw_row))
    rows.append((label, pairs))

  if not rows:
    raise ValueError("no sparse rows were provided")

  return rows


def _build_request(keys, sparse_rows, feature_size, model_name, model_version,
                   signature_name):
  from tensorflow_serving.apis import predict_pb2

  indexs = []
  ids = []
  values = []
  for row_index, (_, pairs) in enumerate(sparse_rows):
    for feature_index, (feature_id, feature_value) in enumerate(pairs):
      indexs.append([row_index, feature_index])
      ids.append(feature_id)
      values.append(feature_value)

  keys_proto = tf.compat.v1.make_tensor_proto(keys, dtype=tf.int32)
  indexs_proto = tf.compat.v1.make_tensor_proto(indexs, dtype=tf.int64)
  ids_proto = tf.compat.v1.make_tensor_proto(ids, dtype=tf.int64)
  values_proto = tf.compat.v1.make_tensor_proto(values, dtype=tf.float32)
  shape_proto = tf.compat.v1.make_tensor_proto([len(sparse_rows), feature_size], dtype=tf.int64)

  request = predict_pb2.PredictRequest()
  request.model_spec.name = model_name
  if model_version > 0:
    request.model_spec.version.value = model_version
  if signature_name:
    request.model_spec.signature_name = signature_name
  request.inputs["keys"].CopyFrom(keys_proto)
  request.inputs["indexs"].CopyFrom(indexs_proto)
  request.inputs["ids"].CopyFrom(ids_proto)
  request.inputs["values"].CopyFrom(values_proto)
  request.inputs["shape"].CopyFrom(shape_proto)
  return request, indexs, ids, values


def _summarize_request(keys, sparse_rows, feature_size, args, indexs, ids, values):
  return {
      "mode": "sparse",
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
          "indexs": {
              "dtype": "int64",
              "shape": [len(indexs), 2],
              "values": indexs,
          },
          "ids": {
              "dtype": "int64",
              "shape": [len(ids)],
              "values": ids,
          },
          "values": {
              "dtype": "float32",
              "shape": [len(values)],
              "values": values,
          },
          "shape": {
              "dtype": "int64",
              "shape": [2],
              "values": [len(sparse_rows), feature_size],
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
      description="Inspect or send the sparse TensorFlow Serving request.")
  parser.add_argument("--host", default="127.0.0.1", help="TensorFlow Serving host.")
  parser.add_argument("--port", type=int, default=9000, help="TensorFlow Serving port.")
  parser.add_argument("--model-name", default="sparse", help="Exported model name.")
  parser.add_argument("--model-version", type=int, default=1, help="Model version to request; <=0 leaves it unset.")
  parser.add_argument("--signature-name", default="", help="Optional signature name.")
  parser.add_argument("--timeout", type=float, default=10.0, help="gRPC timeout in seconds.")
  parser.add_argument("--feature-size", type=int, default=124, help="Sparse feature width used in the exported model.")
  parser.add_argument("--keys", default="1,2", help="Comma-separated int32 keys.")
  parser.add_argument("--examples", default=DEFAULT_EXAMPLES, help="Semicolon-separated libsvm-style sparse rows.")
  parser.add_argument("--examples-file", default="", help="Read sparse rows from a file, one row per line.")
  parser.add_argument("--send", action="store_true", help="Send the request to a running TensorFlow Serving process.")
  return parser


def main(argv=None):
  args = build_parser().parse_args(argv)
  try:
    sparse_rows = _parse_sparse_rows(args.examples, args.examples_file or None)
    keys = _parse_int_list(args.keys)
    if len(keys) != len(sparse_rows):
      raise ValueError("keys length {} does not match sparse rows {}".format(
          len(keys), len(sparse_rows)))
    request, indexs, ids, values = _build_request(keys, sparse_rows,
                                                  args.feature_size,
                                                  args.model_name,
                                                  args.model_version,
                                                  args.signature_name)
  except (OSError, ValueError) as exc:
    print("Sparse request build failed: {}".format(exc), file=sys.stderr)
    return 1

  if not args.send:
    print(json.dumps(_summarize_request(keys, sparse_rows, args.feature_size,
                                        args, indexs, ids, values),
                     indent=2,
                     sort_keys=True))
    return 0

  try:
    response = _send_request(request, args.host, args.port, args.timeout)
  except Exception as exc:
    print("Sparse request failed: {}".format(exc), file=sys.stderr)
    return 2

  print(response)
  return 0


if __name__ == "__main__":
  sys.exit(main())

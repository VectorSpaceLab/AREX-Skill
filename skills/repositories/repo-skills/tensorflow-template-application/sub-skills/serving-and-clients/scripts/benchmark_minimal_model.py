#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import tensorflow as tf



def _make_features(vector_length):
  return np.ones(vector_length, dtype=np.float32)


def _build_request(features, model_name, model_version, signature_name):
  from tensorflow_serving.apis import predict_pb2

  request = predict_pb2.PredictRequest()
  request.model_spec.name = model_name
  if model_version > 0:
    request.model_spec.version.value = model_version
  if signature_name:
    request.model_spec.signature_name = signature_name
  request.inputs["features"].CopyFrom(
      tf.compat.v1.make_tensor_proto(features, dtype=tf.float32))
  return request


def _summarize(args, features):
  return {
      "mode": args.mode,
      "transport": "dry-run",
      "model_spec": {
          "name": args.model_name,
          "version": args.model_version if args.model_version > 0 else None,
          "signature_name": args.signature_name or None,
      },
      "features": {
          "dtype": "float32",
          "shape": [len(features)],
          "values": features.tolist(),
      },
      "benchmark_batch_size": args.benchmark_batch_size,
      "benchmark_test_number": args.benchmark_test_number,
      "benchmark_thread_number": args.benchmark_thread_number,
      "host": args.host,
      "port": args.port,
      "request_timeout": args.request_timeout,
  }


def _run_local_latency(benchmark_batch_size, benchmark_test_number):
  features = _make_features(benchmark_batch_size)
  weight = 1.0
  bias = 1.0

  start = time.time()
  for _ in range(benchmark_test_number):
    _ = features * weight + bias
  elapsed = time.time() - start
  latency_ms = (elapsed * 1000.0) / float(benchmark_test_number)
  print("Average latency is: {} ms".format(latency_ms))
  return 0


def _run_grpc_latency(args, features):
  import grpc
  from tensorflow_serving.apis import prediction_service_pb2_grpc

  request = _build_request(features, args.model_name, args.model_version,
                           args.signature_name)
  channel = grpc.insecure_channel("{}:{}".format(args.host, args.port))
  stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

  start = time.time()
  for _ in range(args.benchmark_test_number):
    _ = stub.Predict(request, args.request_timeout)
  elapsed = time.time() - start
  latency_ms = (elapsed * 1000.0) / float(args.benchmark_test_number)
  print("Average latency is: {} ms".format(latency_ms))
  return 0


def _grpc_worker(args, worker_index):
  import grpc
  from tensorflow_serving.apis import prediction_service_pb2_grpc

  features = np.ones(args.benchmark_batch_size, dtype=np.float32)
  request = _build_request(features, args.model_name, args.model_version,
                           args.signature_name)
  channel = grpc.insecure_channel("{}:{}".format(args.host, args.port))
  stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
  for _ in range(args.benchmark_test_number):
    _ = stub.Predict(request, args.request_timeout)


def _run_grpc_qps(args):
  start = time.time()
  with ThreadPoolExecutor(max_workers=args.benchmark_thread_number) as pool:
    futures = [pool.submit(_grpc_worker, args, index)
               for index in range(args.benchmark_thread_number)]
    for future in futures:
      future.result()
  elapsed = time.time() - start
  total_requests = args.benchmark_test_number * args.benchmark_thread_number
  qps = float(total_requests) / elapsed
  print("Average qps is: {}".format(qps))
  return 0


def build_parser():
  parser = argparse.ArgumentParser(
      description="Benchmark the minimal linear model in local or gRPC mode.")
  parser.add_argument("--mode",
                      choices=["local-latency", "grpc-latency", "grpc-qps"],
                      default="local-latency",
                      help="Benchmark mode.")
  parser.add_argument("--host", default="127.0.0.1", help="TensorFlow Serving host.")
  parser.add_argument("--port", type=int, default=9000, help="TensorFlow Serving port.")
  parser.add_argument("--model-name", default="minimal", help="Exported model name.")
  parser.add_argument("--model-version", type=int, default=1, help="Model version to request; <=0 leaves it unset.")
  parser.add_argument("--signature-name", default="", help="Optional signature name.")
  parser.add_argument("--request-timeout", type=float, default=10.0, help="gRPC timeout in seconds.")
  parser.add_argument("--benchmark-batch-size", type=int, default=1, help="Batch size for each request.")
  parser.add_argument("--benchmark-test-number", type=int, default=10000, help="Iterations per worker.")
  parser.add_argument("--benchmark-thread-number", type=int, default=10, help="Worker count for grpc-qps.")
  parser.add_argument("--dry-run", action="store_true", help="Print the benchmark plan instead of executing it.")
  return parser


def main(argv=None):
  args = build_parser().parse_args(argv)
  features = _make_features(args.benchmark_batch_size)

  if args.dry_run:
    print(json.dumps(_summarize(args, features), indent=2, sort_keys=True))
    return 0

  if args.mode == "local-latency":
    return _run_local_latency(args.benchmark_batch_size,
                              args.benchmark_test_number)
  try:
    if args.mode == "grpc-latency":
      return _run_grpc_latency(args, features)
    if args.mode == "grpc-qps":
      return _run_grpc_qps(args)
  except Exception as exc:
    print("Benchmark failed: {}".format(exc), file=sys.stderr)
    return 2

  print("Unsupported benchmark mode: {}".format(args.mode), file=sys.stderr)
  return 1


if __name__ == "__main__":
  sys.exit(main())

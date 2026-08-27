# Minimal Model Benchmark

## Purpose

This page explains the safe benchmark route for the minimal model example.
It separates the local NumPy latency check from the live gRPC request path so
future agents can answer benchmark questions without reopening the original
scripts.

## What the repo shows

- `minimal_model/train.py` exports a very small TF1-era model with the
  `features -> prediction` signature pattern.
- `minimal_model/benchmark_predict.py` measures local prediction latency inside
  a TensorFlow session.
- `minimal_model/python_predict_client/benchmark_latency.py` and
  `benchmark_qps.py` measure live serving latency and throughput.

The original benchmark scripts are useful as evidence, but they rely on TF1-era
export helpers and hidden local assumptions. The bundled helper keeps the same
intent while making the arguments explicit.

## Bundled helper modes

Use `scripts/benchmark_minimal_model.py` in one of three ways:

- `local-latency`: run a pure NumPy stand-in for the minimal linear model
  `prediction = features * weight + bias`.
- `grpc-latency`: call a running TensorFlow Serving process synchronously and
  report average latency.
- `grpc-qps`: issue concurrent gRPC requests and report requests per second.

## Core request contract

- Input tensor name: `features`
- Input dtype: `float32`
- Input shape: 1-D vector whose length matches the benchmark request size
- The source benchmark scripts use the request batch size as the vector length
- Model name: whatever the server was exported with; the repo examples use
  `minimal` in the server command and older client examples sometimes use a
  typo such as `minial`
- Model version: optional; set it when you know the export version
- Port: whatever the server bound; the repo examples commonly use `9000`

## Why the helper is safe

- It does not depend on a hard-coded local checkpoint path.
- It does not assume the original repository checkout is present.
- It can print the benchmark plan without contacting a server when `--dry-run`
  is set.
- It keeps the live gRPC request path separate from the local latency check.

## When to use each mode

### Local latency

Use this when the user wants to understand the benchmark shape but does not
have a serving process running yet. The helper should:

1. build a deterministic float vector,
2. run the NumPy linear stand-in repeatedly,
3. and print the average latency per iteration.

### gRPC latency

Use this when the model is already exported and TensorFlow Serving is running.
The helper should repeatedly call `Predict` with the same request and print the
average latency.

### gRPC QPS

Use this when the user wants a throughput-oriented check. The helper should run
multiple workers, each sending repeated prediction requests, then print total
requests per second.

## TF1 compatibility note

The source benchmark and export code are TF1-era. That is fine as a reference,
but it means the original `train.py` / `benchmark_predict.py` path should not be
presented as a universal TF2-safe recipe. If the environment only needs a safe
smoke check, the bundled local mode is the lowest-risk path.

## Common benchmark mistakes

- Using the wrong model name, especially when copy-pasting the older `minial`
  typo from the source README.
- Measuring a port that no server is listening on.
- Comparing local NumPy latency to live serving latency without saying which
  path was used.
- Treating the source benchmark's large request counts as a smoke-test default.

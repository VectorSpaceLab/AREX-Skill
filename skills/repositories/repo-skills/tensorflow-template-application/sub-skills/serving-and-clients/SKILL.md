---
name: "serving-and-clients"
description: "Use this sub-skill to build TensorFlow Serving PredictRequest
  payloads, run the Python gRPC dense and sparse clients, benchmark the minimal
  model, or reason about the legacy HTTP and non-Python client surfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serving and Clients

Use this route when a user asks how to send predictions to an exported model,
why a serving request fails, which model name or port to use, or how the repo's
legacy client examples map to dense and sparse tensors.

## Read first

- [references/python-grpc-client.md](references/python-grpc-client.md) for the dense and sparse `PredictRequest` contract, tensor names, dtypes, and shape rules.
- [references/minimal-benchmark.md](references/minimal-benchmark.md) for the safe minimal-model latency and QPS helper.
- [references/http-service.md](references/http-service.md) for the legacy Django checkpoint-backed wrapper and its failure modes.
- [references/alternate-clients.md](references/alternate-clients.md) when the question is about Java, Go, C++, Android, iOS, or Spark clients.
- [references/troubleshooting.md](references/troubleshooting.md) when the user reports a timeout, connection refusal, model mismatch, or shape error.

## What this sub-skill owns

- Python gRPC dense and sparse serving payloads.
- Model name, version, port, and signature behavior for serving calls.
- The safe dry-run path that prints request tensors without contacting a server.
- The minimal model benchmark helper for local latency and live gRPC checks.
- The legacy HTTP cancer prediction wrapper as a checkpoint-backed pattern.
- Alternate clients as reference-only surfaces that need external toolchains.

## Use these bundled helpers

- Run [scripts/predict_dense.py](scripts/predict_dense.py) to inspect or send the dense serving payload.
- Run [scripts/predict_sparse.py](scripts/predict_sparse.py) to inspect or send the sparse serving payload.
- Run [scripts/benchmark_minimal_model.py](scripts/benchmark_minimal_model.py) for the minimal model's local or gRPC benchmark modes.

## Route boundaries

- If the user needs data conversion, TFRecords, or fixture creation, route that to the data-preparation sub-skill.
- If the user needs training, checkpointing, SavedModel export, or TensorBoard, route that to the training-and-export sub-skill.
- If the user wants Java, Go, C++, Android, or iOS build instructions, keep those as reference-only and do not promise a runnable helper in this environment.
- If the user wants to modify the exported model itself, stay within the serving contract and do not drift into training logic.

## Common questions this route should answer

- Which `model_name`, `model_version`, and `port` values should match the server?
- What are the dense and sparse input tensor names, dtypes, and shapes?
- When should `signature_name` be set or omitted?
- How do I tell a connection refusal from a request-shape mismatch?
- Why does the legacy HTTP wrapper exit when the checkpoint is missing?

## Working style

1. Use the dry-run mode first when the user only needs to validate request shape or payload construction.
2. Use the live gRPC path only when a server is already running and the model export is known.
3. Prefer the dense or sparse reference that matches the user's tensor layout rather than guessing from the serving port alone.
4. For non-Python clients, answer from the bundled reference pages and call out external toolchain needs clearly.

## Notes

- The dense and sparse helpers normalize request tensors before sending them.
- The bundled benchmark helper separates a local NumPy check from the live serving call so the user can reason about minimal-model behavior without a server.
- This sub-skill intentionally does not bundle native Java, Go, C++, Android, or iOS build systems.

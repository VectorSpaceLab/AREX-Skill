# Python gRPC Client Contract

## Purpose

This page records the serving request contract used by the bundled Python gRPC
helpers. It is the reference for dense and sparse `PredictRequest` payloads,
not a copy of the original client scripts.

The bundled helpers use the public `tensorflow_serving.apis` imports and the
standard gRPC stub, so future agents do not need local generated `pb2` files.

## Connection and model-spec behavior

- `host` and `port` must match the running TensorFlow Serving process.
- The repo's examples show both `8500` and `9000`; use the port that the
  server actually bound.
- `model_name` must match the export name exactly.
- `model_version` is optional at the protocol level. The bundled helpers treat
  values `<= 0` as "unset" and leave the version off the request so TensorFlow
  Serving can resolve the latest version.
- `signature_name` is optional. Set it only when the export exposes multiple
  signatures or the default signature is not the one you want.

## Dense request payload

| Field | Type | Shape | Notes |
| --- | --- | --- | --- |
| `keys` | `int32` | `[batch, 1]` | The bundled helper normalizes flat key lists to a column vector. |
| `features` | `float32` | `[batch, feature_size]` | The repo's dense cancer example uses `feature_size = 9`. |

Dense serving requests in the source material are centered on the cancer-style
feature vector. The bundled helper keeps the `features` tensor 2-D and prints
the normalized tensor before any live call when `--dry-run` is set.

### Dense output names

The dense export path in the repo may expose `keys`, `prediction`, and, in some
variants, `softmax`. The exact output set depends on the SavedModel signature
that was exported.

## Sparse request payload

| Field | Type | Shape | Notes |
| --- | --- | --- | --- |
| `keys` | `int32` | `[batch, 1]` | The bundled helper normalizes flat keys to a column vector. |
| `indexs` | `int64` | `[nnz, 2]` | The source spelling is `indexs`; keep it for compatibility. |
| `ids` | `int64` | `[nnz]` | Sparse feature ids.
| `values` | `float32` | `[nnz]` | Sparse feature weights.
| `shape` | `int64` | `[2]` | Example: `[2, 124]` for the a8a-style sparse model. |

Sparse requests must keep `nnz == len(ids) == len(values)` and must keep the
row count of `indexs` equal to `nnz`.

## Dry-run behavior

Use the bundled `--dry-run` mode when you only need to validate the request
shape or explain the payload.

The dry-run output should report:

- normalized tensor names,
- dtypes,
- shapes,
- model spec fields,
- and any shape mismatches before a live request is attempted.

## Live call behavior

When `--dry-run` is not set, the helper:

1. imports TensorFlow and `tensorflow_serving.apis.predict_pb2`,
2. creates a `PredictRequest`,
3. copies each tensor into `request.inputs`,
4. opens an insecure gRPC channel to `host:port`, and
5. calls `PredictionServiceStub.Predict(...)` with the configured timeout.

If the call fails, the first thing to check is whether the server is listening
on the requested port. If the server is reachable, check the model name,
version, signature, and tensor shapes next.

## Practical examples

- Dense cancer-style request: four key rows, nine float features per row.
- Sparse a8a-style request: two example rows, `indexs` / `ids` / `values` /
  `shape` payloads matching the sparse exporter contract.

## Why this matters

Most user questions in this workflow are not about gRPC syntax; they are about
which tensor shape is accepted by the serving export, whether a version should
be set, and whether a timeout means transport failure or payload mismatch.

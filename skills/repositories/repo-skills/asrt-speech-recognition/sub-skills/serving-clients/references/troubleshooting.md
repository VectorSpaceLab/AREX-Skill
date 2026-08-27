# Troubleshooting

Use this guide after confirming which serving surface is in use: [HTTP JSON API](http-api.md) or [gRPC API](grpc-api.md).

## Missing weights or language assets

Symptoms:

- Server exits during startup/import.
- HTTP never binds to port `20001` or gRPC never binds to port `20002`.
- Logs mention `save_models/SpeechModel251bn.model.h5`, `model_language`, weight loading, or model-file not found.

Cause and action:

- The original server scripts load `save_models/SpeechModel251bn.model.h5` and `model_language` at import time.
- This is not a client payload issue. Provide the expected released/trained model files before debugging endpoints.

## Endpoint path and method mistakes

Symptoms:

- HTTP 404 from the web server.
- JSON response with `status_code: 400000`.
- HTML response when JSON was expected.

Checks:

- `GET /` returns HTML, not JSON.
- `POST /` returns JSON health/ping status.
- Use exactly `POST /speech`, `POST /language`, or `POST /all` for model calls.
- Avoid misspelled or multi-segment paths. The server route recognizes one path segment as the `level` value.
- Confirm the HTTP client is using port `20001`, not the gRPC port `20002`.

## Base64 text vs bytes for HTTP audio

Symptoms:

- `500000` with base64 decode errors.
- Server-side decode/reshape exceptions.
- Payload contains strings that start with `b'` and end with `'`.

Checks:

- `samples` must be URL-safe base64 encoded raw WAV sample-frame bytes.
- In JSON, `samples` must be plain text such as `"AAAA..."`, not a Python byte-literal representation.
- The `/speech` handler converts the text to UTF-8 bytes before decoding; the `/all` handler decodes the JSON string directly. A plain ASCII base64 JSON string is safe for both.
- Do not base64 encode the entire WAV container unless your server has been changed to expect container bytes. The native decode helper expects sample frames.

## Sample rate and channel metadata

Symptoms:

- Recognition fails, produces poor results, or throws shape errors.
- Server receives audio but model output is unusable.

Checks:

- Read `sample_rate`, `channels`, and `byte_width` from the WAV header and send them unchanged with the corresponding sample bytes.
- Do not override `sample_rate` unless the audio was actually resampled.
- Confirm channel count matches the sample byte layout; the server reshapes decoded samples with `wave_data.shape = -1, channels`.

## `byte_width` 2 vs 4 and the `np.int` caveat

Symptoms:

- Exception like unsupported byte width.
- Exception from NumPy about `np.int` being missing.
- Decode works for 16-bit WAV files but fails for 32-bit WAV files.

Checks:

- ASRT's `decode_wav_bytes` maps `byte_width == 2` to `np.short`.
- It maps `byte_width == 4` to `np.int`. Modern NumPy versions removed `np.int`, so 32-bit WAV input can fail unless the runtime pins an older NumPy or the server code is patched to an explicit dtype such as `np.int32`.
- Other sample widths raise an unsupported-byte-width exception.
- Prefer 16-bit PCM WAV (`byte_width: 2`) unless the serving runtime has been verified for 32-bit samples.

## Ports, listeners, and firewalls

Symptoms:

- Connection refused, timeout, or no response.
- Docker container is running but host clients cannot connect.

Checks:

- HTTP default: host `0.0.0.0`, port `20001`.
- gRPC default: host `0.0.0.0`, port `20002`.
- Publish both ports when using Docker and open firewall/security-group rules for the client network.
- Verify that a process is listening before debugging payload content.
- If only `POST /` succeeds but model endpoints fail, networking is probably not the primary issue.

## Protobuf/gRPC version mismatch

Symptoms:

- Import errors in generated gRPC modules.
- Runtime errors from protobuf descriptors.
- Client and server disagree on request/response fields.

Checks:

- Generate client stubs from the same `asrt.proto` contract documented in [gRPC API](grpc-api.md).
- Keep `grpcio`, `grpcio-tools`, and `protobuf` versions compatible between stub generation and client runtime.
- The Dockerfile evidence pins `grpcio==1.34.0` and `grpcio-tools==1.34.0`; newer host tooling can generate code that needs different protobuf behavior.

## Generated stubs and import paths

Symptoms:

- `ModuleNotFoundError` for `asrt_pb2`, `asrt_pb2_grpc`, or package-prefixed generated modules.
- Generated files import each other with paths that do not match the client package layout.

Checks:

- Ensure generated `asrt_pb2.py` and `asrt_pb2_grpc.py` are on the client `PYTHONPATH` or inside an importable package.
- Regenerate stubs after moving the proto or changing package layout.
- Do not debug ASRT model code until a minimal gRPC client can import the generated modules and construct `AsrtGrpcServiceStub`.

## Docker CPU limitation

Symptoms:

- Inference is much slower than expected.
- GPU is visible on the host but not used by the ASRT container.

Checks:

- Dockerfile evidence installs `tensorflow-cpu==2.5.3`; the container is CPU inference serving only.
- Do not expect GPU acceleration from that image without rebuilding the runtime with a GPU-compatible TensorFlow/CUDA stack.
- Docker serving is not a training path.

## Status-code triage

- `200000`: success/final success.
- `206000`: streaming partial success; keep reading until final `200000` when using gRPC `Stream`.
- `400000`, `400001`, `400002`: client-side path, data format, or unsupported configuration issue.
- `500000`, `500001`: server-side runtime issue, often missing assets, decode errors, model errors, or dependency mismatch.

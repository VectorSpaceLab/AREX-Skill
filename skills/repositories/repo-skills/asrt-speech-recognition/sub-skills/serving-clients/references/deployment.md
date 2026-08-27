# Deployment Boundaries and Startup

This sub-skill describes ASRT serving integration. It does not bundle server copies because the original server scripts perform heavyweight work at import time and then run long-lived listeners.

## Why server code is not bundled here

The original HTTP and gRPC server scripts instantiate the `SpeechModel251BN` acoustic model globally, then call:

```text
ms.load_model('save_models/' + sm251bn.get_model_name() + '.model.h5')
```

For the 251bn model, that resolves to `save_models/SpeechModel251bn.model.h5`. The same modules also load the language model from `model_language` globally. Importing either server script without the expected weights/assets can fail before any route or service is available.

After import-time model setup, the HTTP server enters `waitress.serve(...)`; the gRPC server creates a `grpc.server(...)`, starts it, and sleeps in a long-lived loop. Because of those side effects, this runtime contains only client and payload helpers under `../scripts/`, not server implementations.

## Native server entry points

HTTP service:

```bash
python asrserver_http.py --listen 0.0.0.0 --port 20001
```

- Default listen address: `0.0.0.0`.
- Default HTTP port: `20001`.
- Uses Flask routes served by Waitress.
- Health checks: `GET /` returns HTML; `POST /` returns JSON with `status_code: 200000`.

gRPC service:

```bash
python asrserver_grpc.py --listen 0.0.0.0 --port 20002
```

- Default listen address: `0.0.0.0`.
- Default gRPC port: `20002`.
- Registers `AsrtGrpcService` with methods `Speech`, `Language`, `All`, and `Stream`.
- Requires generated protobuf/gRPC stubs that match the proto contract in [gRPC API](grpc-api.md).

## Docker behavior

The Dockerfile evidence starts both services from a shell script, exposes `20001/tcp` and `20002/tcp`, and installs `tensorflow-cpu==2.5.3` with `grpcio==1.34.0` and `grpcio-tools==1.34.0`.

Operational implications:

- The container is for CPU inference serving, not training and not GPU acceleration.
- CPU inference can be slower than a GPU-backed native deployment.
- Both ports must be published when both HTTP and gRPC clients are expected.
- Version pins in the image can differ from a host Python environment; keep generated stubs and client dependencies compatible with the serving environment.

## Client-only smoke checks

After the server is running and reachable, use the bundled helpers from the sub-skill root:

```bash
python scripts/asrt_http_client.py health --base-url http://127.0.0.1:20001
python scripts/asrt_http_client.py post-root --base-url http://127.0.0.1:20001
python scripts/make_http_payload.py --endpoint /language --sequence-pinyin ni3 hao3 ya5 --pretty
python scripts/asrt_http_client.py language --sequence-pinyin ni3 hao3 ya5 --base-url http://127.0.0.1:20001
```

For `/speech` or `/all`, provide an actual WAV file:

```bash
python scripts/make_http_payload.py --endpoint /all --wav sample.wav --pretty > all-payload.json
python scripts/asrt_http_client.py all --wav sample.wav --base-url http://127.0.0.1:20001
```

If `health` fails, debug network/port binding first. If `post-root` succeeds but `/speech` or `/all` returns `500000`, check model files and WAV metadata in [Troubleshooting](troubleshooting.md).

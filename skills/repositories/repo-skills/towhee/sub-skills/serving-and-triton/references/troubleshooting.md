# Serving and Triton troubleshooting

Use this guide to diagnose Towhee service construction and Triton deployment
plans without unnecessarily starting side-effectful workloads.

## Pydantic and service schema mistakes

Symptoms:

- route registration works, but HTTP/gRPC calls fail during parsing;
- a route receives a raw dict when the function expects a Pydantic object, or the
  reverse;
- responses fail serialization.

Fixes:

- Wrap Pydantic models in `towhee.serve.io.JSON(Model)` for both input and output
  when model parsing/serialization is required.
- Use `JSON()` for plain JSON-compatible dict/list/scalar payloads.
- Do not pass a bare Pydantic class as `input_model` or `output_model`.
- Make the function signature match the decoded body:
  - one function parameter for one decoded object;
  - multiple parameters only when the decoded value is a dict with matching keys
    or a positional list/tuple of matching length.
- Return JSON-compatible values, Pydantic models wrapped by `JSON(Model)`, bytes
  for `BYTES()`, strings for `TEXT()`, and NumPy arrays for `NDARRAY()`.
- Towhee 1.1.3 was validated with Pydantic v1-style parsing. If a newer Pydantic
  emits compatibility warnings or parsing errors, reproduce with Pydantic v1
  before changing service logic.

## Missing imports and optional serving dependencies

Towhee core service-object construction can work without live server packages,
but live HTTP, gRPC, and Triton clients need extras.

| Error or symptom | Likely missing package | Action |
|---|---|---|
| `ModuleNotFoundError: pkg_resources` during `import towhee` | setuptools compatibility | Use an environment that still provides `pkg_resources` (for example, setuptools before its removal) and a Towhee-supported Python version. |
| Importing HTTP server fails on FastAPI | `fastapi` | Install FastAPI in the serving environment. |
| HTTP server startup fails on ASGI server import | `uvicorn` | Install Uvicorn. |
| FastAPI test client or form/multipart routes fail | `httpx` or `python-multipart` | Install the test/client or multipart dependency matching the workflow. |
| Importing gRPC server/client fails | `grpcio` and compatible protobuf | Install gRPC runtime packages. |
| `tritonclient not found` | `tritonclient[http]` | Install the Triton HTTP client extra in the client environment. |

Towhee's lazy dependency helpers may attempt interactive or automatic installs in
some contexts. For reproducible agents, prefer explicit environment preparation
rather than relying on a prompt during execution.

## Port conflicts and live server startup

Symptoms:

- HTTP/gRPC startup raises address-in-use errors;
- client calls hang or connect to an older process;
- expected route returns unexpected content.

Checks and fixes:

```bash
ss -ltnp | grep -E ':(40001|50001|8000|8001|8002)\b' || true
```

- Pick ports that are not already listening.
- Remember `towhee server` starts gRPC when `--grpc-port` is present; otherwise it
  starts HTTP on `--http-port`.
- Use explicit host/port in clients and set request timeouts for HTTP tests.
- Stop spawned processes after tests; do not leave background servers running.

## Docker daemon and GPU/CUDA requirements

Symptoms:

- `docker build` cannot connect to daemon;
- `docker run --gpus=all` fails;
- Triton image starts but model load fails with CUDA/runtime errors.

Checks before running side-effectful commands:

```bash
docker info
nvidia-smi
```

Requirements and cautions:

- Docker image builds require Docker daemon access and enough disk space for large
  Triton/Torch/ONNX layers.
- GPU containers require NVIDIA drivers, the NVIDIA container runtime, and a CUDA
  selector compatible with the chosen Triton base image.
- Towhee's built-in CUDA selectors are `11.3`, `11.4`, `11.6`, `11.7`, and
  `117dev`. Unsupported selectors fail before a build.
- `--shm-size=1g` is part of the documented container shape; increase only when
  model behavior requires it and the user approves.

## Triton image size and model repository layout

Why images are large:

- NVIDIA Triton base images are large.
- The Dockerfiles install Torch/TorchVision/Torchaudio, ONNX tooling, Towhee, and
  model dependencies.
- Exporting real neural operators may include weights and generated model files.

Expected model repository layout:

```text
models/
├── pipeline/
│   ├── 1/
│   │   ├── model.py
│   │   └── pipe.pickle
│   └── config.pbtxt
└── <exported-model>/
    ├── 1/
    │   └── model.onnx
    └── config.pbtxt
```

Common layout problems:

- missing `models/pipeline/1/model.py`: pipeline Python backend was not created;
- missing `models/pipeline/1/pipe.pickle`: pipeline DAG serialization failed;
- missing exported `model.onnx`: operator did not support requested format or
  export failed;
- stale directories from previous builds: build into a fresh root or clean only
  after confirming overwrite policy.

## Remote Triton client failures

Symptoms:

- connection refused or timeout;
- `OUTPUT0` missing;
- single call shape works but batch shape does not;
- batch with `safe=True` returns `None` entries.

Fixes:

- Confirm Triton readiness logs for HTTP port 8000 and model name `pipeline`.
- Use `triton_client.Client(url="host:8000")` for Towhee's pipeline client; it is
  HTTP-oriented even though Triton also exposes gRPC on 8001.
- For multi-input pipelines, call `client(input_a, input_b)` for one item or
  `client.batch([[input_a, input_b], ...])` for a batch.
- If `safe=True`, failures are reported as `None` for every item in the failed
  chunk. Reduce `batch_size` to isolate the bad input.
- Ensure returned data is serializable through Towhee's JSON serializer.

## When to stop instead of running builds

Stop and ask for explicit deployment approval when the next step would do any of
these:

- bind a live HTTP/gRPC/Triton port;
- run `docker build`, `docker run`, or `tritonserver`;
- download model weights, Triton base images, or large ML dependencies;
- use GPUs or alter CUDA-visible state;
- overwrite an existing model repository or Docker image tag;
- rely on external network access or private registries.

For ordinary verification, construct the service object and run the bundled smoke
script only.

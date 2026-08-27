# Runtime Commands

## Standard container launch

A typical Docker launch maps Triton's HTTP, gRPC, and metrics ports and mounts a model repository into the container:

```bash
docker run --rm --net=host --gpus=all \
  -v /absolute/model_repository:/models:ro \
  nvcr.io/nvidia/tritonserver:26.07-py3 \
  tritonserver --model-repository=/models
```

Use `--gpus=1` or a Docker device selection only when the host has NVIDIA Container Toolkit and the model/backend requires GPU. For CPU-only launches, omit `--gpus`:

```bash
docker run --rm --net=host \
  -v /absolute/model_repository:/models:ro \
  nvcr.io/nvidia/tritonserver:26.07-py3 \
  tritonserver --model-repository=/models
```

CPU-only Triton cannot load model configurations or backends that require GPU instances.

## Ports and health

| Port | Protocol | Default purpose |
| --- | --- | --- |
| `8000` | HTTP/REST | KServe v2 health, metadata, infer, repository control, metrics-control extensions |
| `8001` | gRPC | KServe v2 gRPC inference and health services |
| `8002` | HTTP | Prometheus metrics endpoint |

Readiness check:

```bash
curl -v http://localhost:8000/v2/health/ready
```

HTTP 200 means ready. A non-200 response can indicate startup in progress, model load failure under strict readiness, or network/port mismatch.

## Model-control choices

- `--model-control-mode=none` loads all models at startup and ignores repository changes. This is the default.
- `--model-control-mode=explicit` loads only `--load-model` names at startup and enables load/unload through model repository APIs.
- In explicit mode, `--load-model=*` must be the only `--load-model` argument.
- `--model-control-mode=poll --repository-poll-secs=N` watches the repository, but can observe partial updates; avoid for production unless updates are staged atomically.

## Command planner

Use the bundled planner for dry-run command construction:

```bash
python3 scripts/plan_triton_launch.py --context cpu --model-repository /models --gpu none
python3 scripts/plan_triton_launch.py --context gpu --model-repository /models --gpu all --model-control-mode explicit --load-model resnet50 --json
```

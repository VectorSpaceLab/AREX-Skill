---
name: server-runtime
description: "Guides clip_server installation, Jina Flow YAML,
  PyTorch/ONNX/TensorRT runtime selection, scaling, deployment, and backend
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Server Runtime

Use this sub-skill when the user needs to run or configure the CLIP-as-service server package (`clip_server`) or diagnose backend/model service startup.

## Trigger examples

- "Start a CLIP-as-service server on CPU/GPU."
- "Write a Flow YAML for `clip_server` with ONNX or TensorRT."
- "Use replicas, WebSocket/HTTP/gRPC, monitoring, TLS, or Docker."
- "Choose a model name and output dimension."
- "Debug missing ONNX Runtime, TensorRT, model download, OOM, or YAML issues."

## Read first

- [references/configuration.md](references/configuration.md) for install commands, `python -m clip_server`, Flow YAML, runtime parameters, scaling, protocol, monitoring, TLS, Docker, and environment variables.
- [references/model-overview.md](references/model-overview.md) for supported model families, runtime support caveats, dimensions, image sizes, and model-selection notes.
- [references/api-reference.md](references/api-reference.md) for verified executor/helper/tokenizer signatures and behavior that affects configs and troubleshooting.
- [references/troubleshooting.md](references/troubleshooting.md) for backend ImportError, TensorRT/CUDA, ONNX custom model paths, model caches, OOM, and YAML failures.
- [scripts/check_server_config.py](scripts/check_server_config.py) to validate Flow YAML shape without starting the service.
- [scripts/benchmark_client.py](scripts/benchmark_client.py) for a bounded benchmark against an already-running server.
- [scripts/onnx_model_tools.py](scripts/onnx_model_tools.py) for optional ONNX fp16/quantization helpers.

## Bundled Flow templates

- [scripts/torch-flow.yml](scripts/torch-flow.yml): PyTorch CLIPEncoder template.
- [scripts/onnx-flow.yml](scripts/onnx-flow.yml): ONNX Runtime CLIPEncoder template.
- [scripts/tensorrt-flow.yml](scripts/tensorrt-flow.yml): TensorRT CLIPEncoder template.

Copy a bundled template into the user's project and edit it there. Do not edit the skill-owned template in place.

## Boundary routing

- If the task is to call `clip_client.Client` against an already-running server, route to [client-api](../client-api/SKILL.md).
- If the task is to add an AnnLite indexer, choose `n_dim`, or operate a retrieval workspace, route to [search-retrieval](../search-retrieval/SKILL.md).
- If the task is generic deployment unrelated to CLIP-as-service, prefer a more appropriate service/deployment skill.

## Minimal start commands

```bash
python -m clip_server                    # built-in PyTorch Flow
python -m clip_server torch-flow.yml     # explicit PyTorch Flow
python -m clip_server onnx-flow.yml      # built-in ONNX Flow after installing the ONNX extra
python -m clip_server tensorrt-flow.yml  # built-in TensorRT Flow after TensorRT setup
```

The CLI accepts a Flow YAML path or `-i` to read YAML from standard input. It does not expose arbitrary runtime flags; put model/backend/server settings in YAML.

## Backend gate rule

- CPU or CUDA PyTorch can validate base server behavior.
- ONNX requires ONNX Runtime imports and model files/sessions.
- TensorRT requires CUDA, TensorRT Python/runtime packages, and engine build/load evidence. CPU checks do not verify TensorRT.
- Optional M-CLIP, CN-CLIP, search, and flash-attention dependencies must be installed only when selected by the user task.

## Safe validation sequence

1. Install only the needed package/extras.
2. Validate imports with the root `scripts/check_install.py`.
3. Validate YAML statically with [scripts/check_server_config.py](scripts/check_server_config.py).
4. Start the server with a small model/config only when the user approves model downloads and long-running service startup.
5. Use [client-api](../client-api/SKILL.md) `Client.profile()` from the caller side before large requests.

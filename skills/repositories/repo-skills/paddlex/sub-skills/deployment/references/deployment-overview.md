# PaddleX deployment overview

This reference covers deployment surfaces in PaddleX 3.7.2: high-performance inference, serving, high-stability serving, Paddle2ONNX, GenAI client/server, and hardware-specific caveats.

## Deployment family map

| Family | Entry point | Needs |
| --- | --- | --- |
| High-performance inference (HPI) | `create_pipeline(..., use_hpip=True, hpi_config=...)` or `paddlex --pipeline ... --use_hpip` | `hpi-cpu`, `hpi-gpu`, or vendor HPI plugin; matching backend; cache management |
| Basic serving | `paddlex --serve --pipeline ... --host ... --port ...` | `serving` plugin and selected pipeline runtime deps |
| High-stability serving | deployment SDK / Triton-style server package | Linux, Docker Engine, generated pipeline SDK package, server config files |
| Paddle2ONNX | `paddlex --paddle2onnx --paddle_model_dir ... --onnx_model_dir ...` | exported Paddle inference model directory and `paddle2onnx` plugin |
| GenAI client | pipeline/model config with `genai_config`, remote/server backend, `server_url` | `genai-client`, reachable server, API key or backend URL where required |
| GenAI server | `paddlex_genai_server ...` | server plugin such as `genai-vllm-server` or `genai-sglang-server`, model dir, GPU/backend resources |
| On-device / vendor accelerator | platform-specific tools and Paddle/PaddleX builds | Android/NDK/CMake/ADB or NPU/XPU/MLU/DCU/GCU runtime stack |

## Plugin install boundaries

PaddleX base installs do not include every deployment stack. Install only what the workflow needs:

```bash
paddlex --install serving
paddlex --install paddle2onnx
paddlex --install hpi-cpu
paddlex --install hpi-gpu
paddlex --install genai-client
paddlex --install genai-vllm-server
paddlex --install genai-sglang-server
```

Use `--no_deps` only when intentionally managing dependencies yourself. `--platform github.com|gitee.com`, `--use_local_repos`, and `--deps_to_replace ...` are maintainer/advanced install controls; avoid them in ordinary user recipes unless the user has a clear reason.

## HPI operating pattern

Python:

```python
from paddlex import create_pipeline

pipeline = create_pipeline(
    pipeline="image_classification",
    device="gpu:0",
    use_hpip=True,
    hpi_config={"selected_backends": {"paddle_infer": {}}},
)
```

CLI:

```bash
paddlex --pipeline image_classification --input demo.jpg --save_path output --device gpu:0 --use_hpip
```

Notes:

- HPI may use Paddle static graph, ONNX, TensorRT, OpenVINO, or vendor backends depending on plugin and config.
- `engine`, `engine_config`, `use_hpip`, and `hpi_config` interact. Explicit engine/backend overrides can win over broad auto-selection.
- HPI caches generated/backend artifacts under model cache locations. Clear cache after backend, TensorRT, or dynamic-shape changes.
- GPU HPI requires a compatible GPU PaddlePaddle/runtime stack; CPU import is not proof of GPU HPI readiness.

## Serving

Basic serving exposes a pipeline as a service:

```bash
paddlex --serve --pipeline image_classification --host 0.0.0.0 --port 8080
```

Default host/port are commonly `0.0.0.0:8080`. Device selection may auto-pick GPU if available, but explicit `--device` is safer for reproducible runs.

High-stability serving is a different packaging path, typically Linux/Docker/Triton-oriented. It uses server-side pipeline/model repository configs and may need object storage settings when returning file URLs.

## Paddle2ONNX

Use after exporting a module/inference model directory:

```bash
paddlex --paddle2onnx \
  --paddle_model_dir ./inference_model \
  --onnx_model_dir ./onnx \
  --opset_version 7
```

The input directory should contain exported Paddle model artifacts and required config/scaler files. Do not point Paddle2ONNX at an arbitrary training checkpoint directory.

## GenAI client/server

GenAI-backed pipelines split into two sides:

- **client side** inside a PaddleX pipeline/model config, often with `genai_config` and a `server_url`.
- **server side** launched with `paddlex_genai_server` and a backend such as FastDeploy, vLLM, or SGLang.

Common install paths:

```bash
paddlex --install genai-client
paddlex --install genai-vllm-server
paddlex --install genai-sglang-server
paddlex_genai_server --help
```

PaddleOCR-VL / document VLM workflows are the most common GenAI-adjacent PaddleX routes. Treat them as advanced unless GPU/server resources and model downloads are allowed.

## Hardware-specific notes

- CPU baseline: install CPU PaddlePaddle and PaddleX extras needed by the workflow.
- NVIDIA GPU: install a compatible `paddlepaddle-gpu` wheel and match CUDA/cuDNN/TensorRT constraints for HPI or serving.
- Vendor devices such as NPU/XPU/MLU/DCU/GCU: follow vendor Paddle/PaddleX builds and device strings from the multi-device guide; do not claim verification without hardware evidence.
- On-device Android: requires CMake/NDK/ADB and converted Lite/edge artifacts; keep it as an advanced path unless the toolchain is prepared.

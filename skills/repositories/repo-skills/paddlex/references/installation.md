# PaddleX installation and environment notes

PaddleX separates the PaddlePaddle framework, PaddleX package extras, and deployment plugins. Install the smallest set needed for the user's task.

## Python and framework baseline

PaddleX 3.x supports modern Python versions and depends on PaddlePaddle 3.0+ for actual model execution. Install PaddlePaddle first, then PaddleX.

CPU baseline:

```bash
python -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python -m pip install "paddlex[base]"
```

NVIDIA GPU examples:

```bash
# CUDA 11.8 wheel channel
python -m pip install paddlepaddle-gpu==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
python -m pip install "paddlex[base]"

# CUDA 12.6 wheel channel
python -m pip install paddlepaddle-gpu==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
python -m pip install "paddlex[base]"
```

A visible GPU is not enough: verify that `paddle.is_compiled_with_cuda()` is true before using `gpu:*`, HPI GPU, or TensorRT routes.

## PaddleX extras

PaddleX base dependencies cover package import and common utilities. Domain extras are grouped by capability in the package metadata:

- `cv` for OpenCV/COCO/image tooling.
- `ocr-core` and `ocr` for OCR/document pipelines and modules.
- `multimodal` for VLM/multimodal support.
- `ie` and `trans` for document information extraction and translation flows.
- `speech` for speech/TTS utilities.
- `ts` for time-series utilities.
- `video` for video decoder/codec support.
- `base` is a broad domain bundle; use it when broad local PaddleX functionality is desired.

Prefer a narrow extra if the task is narrow. Use `base` for broad researcher workflows that need many pipeline/module families.

## Deployment plugins

Install deployment plugins only when needed:

```bash
paddlex --install serving
paddlex --install paddle2onnx
paddlex --install hpi-cpu
paddlex --install hpi-gpu
paddlex --install genai-client
paddlex --install genai-vllm-server
paddlex --install genai-sglang-server
```

Do not install server/GPU/HPI stacks for a simple CPU pipeline smoke.

## Quick verification

```bash
python - <<'PY'
import paddle
import paddlex
print('paddle', paddle.__version__, 'cuda?', paddle.is_compiled_with_cuda())
print('paddlex', paddlex.__version__)
PY
paddlex --help
```

Or use the bundled helper:

```bash
python scripts/check_paddlex_install.py
```

## Environment-selection checklist

- CPU-only inference/docs work: CPU PaddlePaddle + selected PaddleX extras.
- GPU inference/training: GPU PaddlePaddle matching driver/wheel channel + selected PaddleX extras.
- HPI/serving/Paddle2ONNX/GenAI: add the matching plugin after base install.
- Vendor accelerators (NPU/XPU/MLU/DCU/GCU): use vendor-specific PaddlePaddle/PaddleX instructions and do not claim verification without hardware.
- Video routes: verify decoder/codec stack separately.
- Credentialed/remote LLM routes: prepare API keys/server URL outside the skill content.

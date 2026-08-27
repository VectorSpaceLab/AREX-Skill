# Installation and deployment

Read this when choosing a runtime, backend, codec, container, or local UI.

## Supported baseline

The repository snapshot is `PytorchWildlife` 1.3.0 and declares Python `>=3.10`.
Use an isolated environment rather than mutating a system or base environment.
The package metadata installs PyTorch, TorchVision, TorchAudio, Pillow,
`supervision==0.23.0`, patched Gradio `>=6.15.1,<7`, Ultralytics, YOLOv5,
`timm`, Lightning, `scikit-learn`, OmegaConf, and related dependencies. The
bioacoustic companion additionally needs `librosa`, `soundfile`, PyYAML, and
TorchMetrics; install only the groups needed by the selected workflow.

```bash
python -m pip install PytorchWildlife
# only for the audio companion when not already present
python -m pip install librosa soundfile pyyaml torchmetrics
```

The source checkout's `requirements.txt` also contains documentation-build and
ONNX Runtime packages. Do not install every line merely to run image inference.

## CPU and CUDA

Core APIs expose `device="cpu"` defaults and can be inspected on CPU. CUDA is
an optional acceleration path for model inference, bioacoustic spectrograms,
and training. Choose a PyTorch wheel compatible with the installed NVIDIA
driver; the CUDA toolkit reported by a driver is not the same thing as an
installed compiler. Verify the actual backend before claiming GPU execution:

```bash
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print("cuda:", torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device="cuda")
PY
```

Do not use a CPU import or a synthetic response as evidence that a required
GPU model forward pass works. If CUDA is unavailable, use CPU for structural
checks and state the limitation.

## Weights, data, and containers

Pretrained constructors generally fetch weights into a Torch cache when the
local weight is absent. For offline work, pass `weights=<local-checkpoint>` and
avoid constructors whose default `pretrained=True` would start a download.
Never treat a checkpoint filename as proof of architecture or class mapping.

The repository documents a Docker/Gradio showcase. A local Gradio app accepts
single images, ZIP batches, and videos, but has no built-in authentication; bind
it to a trusted interface, constrain uploads, and do not expose it as a
multi-tenant service. Real video handling may require FFmpeg and a compatible
OpenCV codec. Container pulls, server launches, external datasets, and model
weight downloads are explicit operations, not installation smoke tests.

## Companion modules

`PW_Bioacoustics` and `PW_FT_*` are repository companion workflows rather than
separate core distribution entry points. Keep their configs, dependency
variants, outputs, and checkpoints separate. Read the relevant sub-skill before
running their scripts; use parser/preflight checks before training or inference.

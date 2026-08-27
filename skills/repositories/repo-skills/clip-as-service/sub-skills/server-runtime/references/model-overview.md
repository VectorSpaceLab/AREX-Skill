# Model Overview

## When to read

Read this before choosing a CLIP model name, setting an AnnLite `n_dim`, switching runtimes, or explaining why two embedding indexes are incompatible.

## Model-name conventions

CLIP-as-service uses strings such as:

- `ViT-B-32::openai`
- `RN50::openai`
- `ViT-H-14::laion2b-s32b-b79k`
- `M-CLIP/LABSE-Vit-L-14`
- `CN-CLIP/ViT-B-16`

For OpenCLIP-style names, the part before `::` is the architecture and the part after `::` is the pretrained source. Older aliases such as `ViT-B/32` are accepted in some runtime-specific maps.

## Common model dimensions

| Model family/name pattern | Output dimension | Image size | Notes |
| --- | ---: | ---: | --- |
| `RN50::*` | 1024 | 224 | PyTorch/ONNX/TensorRT supported for common variants. |
| `RN101::*` | 512 | 224 | PyTorch/ONNX/TensorRT supported for common variants. |
| `RN50x4::*` | 640 | 288 | TensorRT supports common RN50x4 variants. |
| `RN50x16::*` | 768 | 384 | TensorRT not supported by the documented matrix. |
| `RN50x64::*` | 1024 | 448 | TensorRT not supported by the documented matrix. |
| `ViT-B-32::*` | 512 | 224 | Default family; broad PyTorch/ONNX/TensorRT support for many variants. |
| `ViT-B-16::*` | 512 | 224 | Broad PyTorch/ONNX/TensorRT support for many variants. |
| `ViT-B-16-plus-240::*` | 640 | 240 | TensorRT marked work-in-progress in docs. |
| `ViT-L-14::*` | 768 | 224 | PyTorch/ONNX supported; TensorRT not supported in the documented matrix. |
| `ViT-L-14-336::openai` / `ViT-L/14@336px` | 768 | 336 | Larger image size; TensorRT not supported. |
| `ViT-H-14::*` | 1024 | 224 | Strong benchmark performance but larger disk/RAM/VRAM footprint. |
| `ViT-g-14::*` | 1024 | 224 | Strong benchmark performance but large model footprint. |
| `M-CLIP/LABSE-Vit-L-14` | 768 | 224 | Requires multilingual dependencies and combines multilingual text with an OpenCLIP visual model. |
| `M-CLIP/XLM-Roberta-Large-Vit-B-32` | 512 | 224 | Requires `transformers`; TensorRT marked work-in-progress in docs. |
| `M-CLIP/XLM-Roberta-Large-Vit-B-16Plus` | 640 | 240 | Requires `transformers`; TensorRT marked work-in-progress. |
| `M-CLIP/XLM-Roberta-Large-Vit-L-14` | 768 | 224 | Requires `transformers`; TensorRT not supported in docs. |
| `CN-CLIP/ViT-B-16` | 512 | 224 | Requires `cn_clip`; PyTorch route only in source code. |
| `CN-CLIP/ViT-L-14` | 768 | 224 | Requires `cn_clip`. |
| `CN-CLIP/ViT-L-14-336` | 768 | 336 | Requires `cn_clip`. |
| `CN-CLIP/ViT-H-14` | 1024 | 224 | Requires `cn_clip`. |
| `CN-CLIP/RN50` | 1024 | 224 | Requires `cn_clip`. |

## Runtime support rules

- **PyTorch** routes model names through `CLIPModel`, which dispatches to OpenCLIP, multilingual CLIP, or CN-CLIP classes based on model maps and optional imports.
- **ONNX** has its own `_MODELS` map and downloads or loads `textual.onnx` and `visual.onnx` files. It supports many OpenCLIP and M-CLIP names but not CN-CLIP in the inspected ONNX model map.
- **TensorRT** supports a smaller documented list and requires CUDA/TensorRT. It builds or loads serialized engines derived from ONNX assets.
- **Search indexes** must set `n_dim` to the selected model's output dimension. Changing model dimensions requires rebuilding the index.

## Model selection guidance

- Start with `ViT-B-32::openai` for a small default smoke test and broad runtime support.
- Prefer ViT models over RN models for many general retrieval/classification tasks according to bundled benchmark evidence, unless domain benchmarks favor an RN variant.
- Larger ViT-H/ViT-g models can improve zero-shot performance but increase disk, RAM, VRAM, startup, and serving costs.
- For multilingual text, select an `M-CLIP/...` model and install the transformers extra. Do not expect a base OpenCLIP tokenizer to reproduce M-CLIP behavior.
- For Chinese CLIP, install the `cn_clip` extra and use `CN-CLIP/...` names.
- For TensorRT, choose only a documented TensorRT-supported model; unsupported names fail before serving.

## Verification implications

Model constructor tests can trigger network downloads or large cache use. Prefer static config and import checks for planning. Run model-backed native verification only when the user explicitly approves downloads, cache use, and backend hardware requirements.

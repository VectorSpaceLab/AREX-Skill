# Setup and Checkpoints

## Purpose

Read this before choosing install commands, optional packages, model types, checkpoints, or devices for Segment Anything workflows.

## Core Requirements

- Python 3.8 or newer.
- PyTorch and TorchVision installed for the target CPU/CUDA environment.
- A SAM checkpoint file supplied by the user; checkpoints are not part of the Python package.
- `segment_anything` package installed from the public repository or an editable checkout.

## Model Types and Checkpoints

| Model type | Builder | Notes |
| --- | --- | --- |
| `default` | `build_sam_vit_h` | Alias for the largest ViT-H model. |
| `vit_h` | `build_sam_vit_h` | Largest documented SAM backbone; highest memory use. |
| `vit_l` | `build_sam_vit_l` | Mid-sized ViT-L backbone. |
| `vit_b` | `build_sam_vit_b` | Smallest documented backbone; best first choice for constrained machines. |

The checkpoint must match the selected model type. If the model loads but `load_state_dict` reports missing or unexpected keys, verify the checkpoint/model pair before debugging prompts or images.

## Installation Choices

Base package inspection and prompted APIs need PyTorch/TorchVision plus the SAM package:

```bash
pip install torch torchvision
pip install git+https://github.com/facebookresearch/segment-anything.git
```

Optional packages are workflow-specific:

| Package | Needed for |
| --- | --- |
| `opencv-python` or `opencv-python-headless` | Reading/writing images in CLI helpers and small-region AMG post-processing. |
| `pycocotools` | COCO RLE mask output and decoding. |
| `matplotlib` | Notebook-style visualization and plotting recipes. |
| `onnx` | ONNX export tooling. |
| `onnxruntime` | ONNX export validation and dynamic quantization. |

Avoid installing broad dev extras unless the user is editing or linting the repository itself.

## Device Selection

- Prefer CUDA for real SAM inference when a compatible CUDA PyTorch wheel is installed.
- Use CPU for import checks, parser checks, and small examples when no GPU is available.
- The repo scripts default to CUDA in some places; pass `--device cpu` explicitly on CPU-only machines.
- Do not diagnose poor throughput until the device, PyTorch CUDA availability, and checkpoint size are known.

## Minimal Model Construction

```python
import torch
from segment_anything import sam_model_registry

model_type = "vit_b"
checkpoint = "sam_vit_b_01ec64.pth"
device = "cuda" if torch.cuda.is_available() else "cpu"
sam = sam_model_registry[model_type](checkpoint=checkpoint)
sam.to(device=device)
```

## Verification Checklist

1. `import segment_anything` succeeds.
2. `sorted(sam_model_registry.keys())` returns `default`, `vit_b`, `vit_h`, and `vit_l`.
3. `torch.cuda.is_available()` matches the intended device choice.
4. The checkpoint path exists and matches `model_type`.
5. Optional imports match the selected workflow: `cv2`, `pycocotools`, `onnx`, or `onnxruntime` as needed.

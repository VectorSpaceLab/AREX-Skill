---
name: segment-anything
description: "Use Meta Segment Anything (SAM) for prompt-based segmentation,
  automatic mask generation, ONNX export, browser deployment, checkpoints,
  optional dependencies, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Segment Anything

Use this repo skill when a user asks for help with the original Segment Anything (SAM) Python package, including checkpoint setup, promptable image segmentation, automatic mask generation, ONNX export, or browser deployment.

## Start Here

1. Install the package and required backend dependencies. SAM requires Python 3.8+, PyTorch, and TorchVision; CUDA is recommended for real workloads but CPU is usable for small inspections and examples.
2. Choose a checkpoint/model pair from `references/setup-and-checkpoints.md` before writing code or commands.
3. Run `scripts/check_environment.py --check-optional` to verify imports and optional packages before troubleshooting deeper issues.
4. Route the user request to the narrowest sub-skill below.

## Route by Task

- Use `sub-skills/prompted-segmentation/` for `SamPredictor`, point/box prompts, repeated prompts on one image, iterative low-resolution mask refinement, and image embedding extraction.
- Use `sub-skills/automatic-mask-generation/` for `SamAutomaticMaskGenerator`, all-object masks, folder runs, PNG/CSV outputs, COCO RLE JSON, and AMG CLI tuning.
- Use `sub-skills/onnx-and-browser/` for ONNX export, quantization, ONNXRuntime inputs, browser asset wiring, image embeddings for web demos, and SharedArrayBuffer/header issues.

## Installation Pattern

For package users, prefer the public install path plus explicit backend packages:

```bash
pip install git+https://github.com/facebookresearch/segment-anything.git
pip install torch torchvision
```

For local development against a checkout:

```bash
pip install -e .
```

Optional workflows need extra packages:

```bash
pip install opencv-python pycocotools matplotlib onnx onnxruntime
```

Install only the extras needed for the selected workflow: OpenCV for image I/O and small-region cleanup, `pycocotools` for COCO RLE, `matplotlib` for notebook-style visualization, and `onnx`/`onnxruntime` for export, validation, and quantization.

## Minimal Import Check

```python
from segment_anything import SamPredictor, SamAutomaticMaskGenerator, sam_model_registry
print(sorted(sam_model_registry.keys()))  # ['default', 'vit_b', 'vit_h', 'vit_l']
```

`default` is equivalent to `vit_h`. Checkpoint files are not bundled with the package; the user must provide the matching `.pth` checkpoint.

## Shared References and Scripts

- Read `references/setup-and-checkpoints.md` before selecting a model type, checkpoint, device, or optional dependency set.
- Read `references/data-formats.md` when handling prompt arrays, mask outputs, annotation records, or SA-1B-style JSON.
- Read `references/troubleshooting.md` for install/import, checkpoint, optional dependency, backend, and cross-workflow failures.
- Read `references/repo-provenance.md` before deciding whether this generated skill is stale for a current checkout.
- Run `scripts/check_environment.py` for a safe import and optional dependency diagnostic.

## Common Decisions

- Use `vit_b` for lower memory and faster experiments, `vit_l` for a larger backbone, and `vit_h` or `default` for the largest documented model.
- Prefer `device="cuda"` for real segmentation throughput when CUDA PyTorch is correctly installed; use `device="cpu"` for parser checks, tiny examples, or machines without GPU access.
- Use prompted segmentation when the user has object hints; use automatic mask generation when the user wants proposal masks for every object.
- Use ONNX only for the lightweight prompt/mask-decoder path; image embeddings still come from the SAM image encoder in Python and must match the exported checkpoint/model type.

## Self-Containment Notes

This skill distills repository evidence into bundled references and scripts. Future agents should not need to open original notebooks, demo files, or repo scripts to answer normal SAM usage questions; use the bundled sub-skills and helpers instead.

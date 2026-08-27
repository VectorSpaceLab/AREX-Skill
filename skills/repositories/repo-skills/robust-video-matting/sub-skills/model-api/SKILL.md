---
name: model-api
description: "Use when working with RobustVideoMatting MattingNetwork APIs,
  recurrent states, model variants, refiners, tensor shapes, and safe synthetic
  forward checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# RobustVideoMatting Model API

Use this sub-skill when the task is about constructing or calling the RVM PyTorch
model itself rather than converting videos, preparing training data, or running
evaluation metrics.

## Read this when

- The user asks how to instantiate `MattingNetwork` with `mobilenetv3` or
  `resnet50`.
- The task mentions recurrent states, ConvGRU memory, `downsample_ratio`,
  `segmentation_pass`, foreground/alpha tensor shapes, or channel/rank errors.
- You need a safe import/forward smoke test before writing inference or training
  code.
- You need to decide whether to use `deep_guided_filter` or
  `fast_guided_filter` as the refiner.

Route other tasks elsewhere:

- Video/image conversion, checkpoints, TorchHub, TorchScript, ONNX, TensorFlow,
  or CoreML usage: [inference-workflows](../inference-workflows/SKILL.md).
- Dataset layouts, `DATA_PATHS`, training stages, losses, or augmentations:
  [training-data](../training-data/SKILL.md).
- LR/HR metric evaluation or speed benchmarking:
  [evaluation-tools](../evaluation-tools/SKILL.md).

## Core workflow

1. Ensure the RVM source modules are importable as `model` and that PyTorch and
   TorchVision are installed. If in doubt, run the bundled smoke helper:

   ```bash
   python scripts/rvm_model_smoke.py --repo-root /path/to/RobustVideoMatting --variant mobilenetv3 --device cpu
   ```

2. Instantiate the model without downloading backbone weights unless the user
   explicitly wants that side effect:

   ```python
   from model import MattingNetwork

   model = MattingNetwork(variant="mobilenetv3").eval()
   # or: MattingNetwork(variant="resnet50")
   ```

3. Feed RGB tensors normalized to `0..1` in channel-first format:

   - single frame/batch: `[B, C, H, W]`
   - chunked sequence: `[B, T, C, H, W]`

4. Recycle all four recurrent states in temporal order:

   ```python
   rec = [None] * 4
   fgr, pha, *rec = model(src, *rec, downsample_ratio=0.25)
   ```

5. Validate the output contract. Matting mode returns foreground `fgr`, alpha
   `pha`, and four recurrent states. `segmentation_pass=True` returns
   segmentation logits plus recurrent states, not foreground/alpha.

## Bundled references and scripts

- Read [references/api-reference.md](references/api-reference.md) for verified
  constructor and forward signatures, tensor ranks, output shapes, recurrent
  state details, model variants, and architecture notes.
- Read [references/troubleshooting.md](references/troubleshooting.md) when
  shape errors, invalid variants, device/dtype mismatches, recurrent-state
  misuse, pretrained downloads, or segmentation-pass confusion appear.
- Run [scripts/rvm_model_smoke.py](scripts/rvm_model_smoke.py) for a safe
  synthetic forward pass on CPU or CUDA. It is adapted from the repo's speed
  test but intentionally avoids benchmarks, downloads, and training.

## Decision points

- Prefer `mobilenetv3` for most inference and smoke tests because it is the
  smaller recommended variant. Use `resnet50` when the user explicitly wants
  the larger model with modest quality improvement.
- Keep `refiner="deep_guided_filter"` unless the task specifically asks for the
  faster guided-filter refiner or export behavior.
- Use 5D input chunks (`[B,T,C,H,W]`) to improve parallelism while preserving
  temporal recurrence across chunks. Carry only the returned four state tensors
  into the next chunk.
- Do not use a CPU smoke test as proof of GPU speed, CUDA memory behavior, or
  high-resolution evaluation performance. Route those questions to
  [evaluation-tools](../evaluation-tools/SKILL.md).

## Acceptance check for model API answers

A good answer for this surface names the exact tensor rank/order, explains the
four recurrent states, states whether the call returns fgr/pha or segmentation
logits, includes a small validation snippet or smoke command, and routes any
conversion/training/evaluation work to the owning sub-skill.

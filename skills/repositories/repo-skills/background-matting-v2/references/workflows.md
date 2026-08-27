# Workflows

## Purpose

This file gives the root-level picture of the repo's public workflows. Use the
sub-skills for exact commands and failure handling.

## 1) Inference and demo

Use `sub-skills/inference-and-demo/` when you want to:

- run image or video matting on a source/background pair
- choose `mattingbase` vs `mattingrefine`
- decide on `resnet50`, `resnet101`, or `mobilenetv2`
- decide whether to use `cpu` or `cuda`
- inspect throughput with the speed test
- reason about webcam demo requirements

Typical flow:
1. Confirm `src` and `bgr` have the same shape or same-sized image/video frames.
2. Choose `mattingrefine` for full-resolution output, or `mattingbase` for a
   coarse model.
3. Use `scripts/check_env.py` or the inference sub-skill smoke helper to verify
   import and a tiny forward pass.
4. Run the image or video wrapper with `--dry-run` first if you only want the
   command shape.

## 2) Export and backend compatibility

Use `sub-skills/export-and-backends/` when you want to:

- script a model for TorchScript
- export a model to ONNX
- choose safe patch crop/replace methods for compatibility
- understand what parts of the model are production-oriented vs experimental

Typical flow:
1. Choose the model variant and backend target.
2. Prefer the small backend smoke helper before any weight-bearing export.
3. For TorchScript, confirm the hoisted refine attributes still behave after
   scripting.
4. For ONNX, confirm the runtime can load the exported graph and that outputs
   match expected names and shapes.

## 3) Training and data setup

Use `sub-skills/training/` when you want to:

- configure `data_path.py`
- validate paired foreground / alpha / background directory trees
- run `train_base.py` or `train_refine.py`
- reproduce the evaluation benchmark layout

Typical flow:
1. Validate the dataset layout before starting a long run.
2. Confirm `dataset-name` is one of the supported keys.
3. Confirm the batch size is compatible with the CUDA device count for refine
   training.
4. Use the training wrapper in dry-run mode before launching a real run.

## Shared conventions

- Source and background inputs are normalized RGB tensors in the model API.
- `MattingRefine` requires height and width divisible by 4.
- Image outputs include `com`, `pha`, `fgr`, `err`, and `ref` depending on the
  model type.
- The repo's benchmark MATLAB/Octave script is reference-only; it is not part of
  the bundled runtime helpers.

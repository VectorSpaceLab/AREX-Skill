---
name: training-evaluation
description: "Routes 3DDFA training recipes, loss selection, checkpoint resume,
  dataset layout, and benchmark evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training-evaluation

Use this sub-skill when you need to train 3DDFA, adapt a loss recipe, validate the training data layout, resume from a checkpoint, or interpret AFLW / AFLW2000 benchmark results.

## Use this route for

- `train.py` command setup and the bundled `training/*.sh` recipes.
- Choosing between WPDC, VDC, and PDC.
- Checking filelists, param files, and the expected cropped-image layout.
- Understanding checkpoint naming and resume behavior.
- Running or interpreting `benchmark.py`, `benchmark_aflw.py`, and `benchmark_aflw2000.py`.

## Do not use this route for

- Inference-only or demo flows; use the python-inference route instead.
- Geometry rendering / visualization outputs; use the geometry-rendering route instead.
- ONNX or C++ export; use the cpp-onnx-port route instead.

## Read first

- `references/training-and-losses.md`
- `references/data-layout.md`
- `references/evaluation-benchmarks.md`
- `references/troubleshooting.md`

## Skill-owned script

- `scripts/validate_training_args.py` — safe checker for training command templates, filelists, param paths, and GPU device ids.

## Operating notes

- Native training is CUDA-centric: `train.py` calls `torch.cuda.set_device(...)` and wraps the model with `nn.DataParallel(...).cuda()`.
- The shipped loss modules import in a CPU-only Python environment, but their forward paths still expect CUDA tensors.
- `--resume` restores the model state dict only; optimizer state is not bundled in the saved checkpoints.
- The bundled shell recipes are templates. Adjust `--root`, filelists, param paths, and `--devices-id` to your local layout before running.
- If you already have predicted params, use the benchmark helper flow described in the benchmark reference rather than re-running inference.

## Cross-links

- For training command validation, run the skill-owned script.
- For benchmark data requirements and NME meaning, read the evaluation reference.

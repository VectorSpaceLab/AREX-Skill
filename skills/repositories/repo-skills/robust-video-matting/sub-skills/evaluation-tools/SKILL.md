---
name: evaluation-tools
description: "Use when evaluating RobustVideoMatting alpha/foreground
  predictions, preparing LR or HR metric directories, generating evaluation
  composites, or interpreting speed benchmarks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# RobustVideoMatting Evaluation Tools

Use this sub-skill when the task is about measuring RVM predictions, preparing
prediction/ground-truth trees, understanding LR versus HR metrics, or explaining
published speed numbers.

## Read this when

- The user asks to compute `pha_mad`, `pha_mse`, `pha_grad`, `pha_conn`,
  `pha_dtssd`, `fgr_mad`, or `fgr_mse`.
- The task mentions `evaluate_lr.py`, `evaluate_hr.py`, `videomatte_512x288`,
  `videomatte_1920x1080`, or Excel metric output.
- The user needs to generate synthetic evaluation composites from matte and
  background datasets.
- The user asks why converter FPS differs from the README speed table.

Route other tasks elsewhere:

- Producing predictions from a video or frame directory:
  [inference-workflows](../inference-workflows/SKILL.md).
- Dataset acquisition/training data layouts: [training-data](../training-data/SKILL.md).
- Model forward internals: [model-api](../model-api/SKILL.md).

## Evaluation workflow

1. Ensure predictions and ground truth use the exact same dataset/clip/frame
   tree. The evaluator expects alpha under `pha/` and foreground under `fgr/`
   when foreground metrics are selected.
2. Choose LR or HR flow:
   - LR evaluation is CPU/NumPy/OpenCV oriented and includes `pha_conn`.
   - HR evaluation hardcodes CUDA tensors and Kornia for high-resolution
     gradient metrics.
3. For a safe tiny assertion check, use the bundled JSON evaluator:

   ```bash
   python scripts/rvm_evaluate_lr_tiny.py \
     --pred-dir pred/videomatte_512x288 \
     --true-dir true/videomatte_512x288 \
     --metrics pha_mad pha_mse pha_dtssd fgr_mad fgr_mse
   ```

4. For full repo-style evaluation, mirror the metric names and directory
   constraints in [references/evaluation-reference.md](references/evaluation-reference.md).
5. If the user asks for speed, separate tensor throughput from media IO. The
   README speed table is based on a CUDA tensor loop, not the Python converter's
   full decode/encode pipeline.

## Bundled references and script

- Read [references/evaluation-reference.md](references/evaluation-reference.md)
  for LR/HR metrics, directory schemas, compositing scripts, and speed-test
  caveats.
- Read [references/troubleshooting.md](references/troubleshooting.md) for empty
  result directories, frame mismatches, missing dependencies, HR CUDA-only
  behavior, deprecated NumPy aliases, and foreground-mask issues.
- Run [scripts/rvm_evaluate_lr_tiny.py](scripts/rvm_evaluate_lr_tiny.py) for a
  self-contained CPU JSON summary on small prediction/ground-truth folders. It
  intentionally does not depend on the original checkout.

## Key decisions

- Use LR/tiny evaluation for quick validation of directory matching and metric
  plumbing.
- Use HR evaluation only in a CUDA environment with Kornia and matching
  high-resolution data; it is not a CPU fallback.
- Do not run synthetic composite generation as a default check. Those scripts
  require large external matte/background datasets and can create many files.
- If foreground metrics are requested, require matching `fgr/` frames and a
  non-empty alpha mask.

## Acceptance check for evaluation answers

A good answer states the exact directory shape, names the metrics and runtime
requirements, checks frame-name equality, chooses LR/HR appropriately, and
explains whether any skipped compositing or CUDA benchmark is outside the safe
verification scope.

# Cross-cutting troubleshooting

## Choose the owning route

- TensorFlow, CUDA, compiler, protobuf, Python version, or custom-op loader:
  `../sub-skills/runtime-and-custom-ops/SKILL.md`.
- Missing KITTI frame files, malformed detector boxes, or pickle generation:
  `../sub-skills/kitti-data-preparation/SKILL.md`.
- Hyperparameters, channel/point count, logs, checkpoint restore, or OOM:
  `../sub-skills/training/SKILL.md`.
- Empty/malformed result rows, evaluator binary, split/AP mismatch:
  `../sub-skills/inference-and-evaluation/SKILL.md`.
- External SUN RGB-D assets, MATLAB extraction, 10-class schema, or result
  pickle: `../sub-skills/sunrgbd/SKILL.md`.

## Common stop conditions

Stop rather than guessing when a required dataset license/download is missing,
a source pickle is truncated, a checkpoint does not match its model, or v2
custom operators cannot load. Keep environment repair in a new isolated prefix;
do not upgrade a working host environment in place. A safe preflight validates
inputs but does not prove benchmark accuracy, CUDA execution, or training
convergence.

# Training and Evaluation Troubleshooting

- **CUDA/custom-op import failure**: stop before launching workers; verify torch,
  toolkit, extensions, and `spconv` through `runtime-ops`.
- **NCCL hang**: reduce to one GPU, inspect ranks/device visibility/master port,
  and remove stale launcher assumptions.
- **Out of memory**: reduce samples per GPU, voxel limits/range, workers, or
  model size; do not use gradient accumulation unless the trainer supports it.
- **No output operation**: test requires `--out`, `--json_out`, or `--show`.
- **Output extension error**: pickle output must end in `.pkl` or `.pickle`.
- **Checkpoint class mismatch**: compare checkpoint metadata, dataset classes,
  task ordering, and head outputs before evaluating.
- **Bad/empty metrics**: validate split, annotations, coordinate conversion,
  sweeps, score/NMS settings, and evaluator SDK version.
- **Headless display error**: save outputs or use offscreen settings; route plots
  to `visualization-and-analysis`.

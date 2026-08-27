# Cross-Cutting Troubleshooting

## Use This Router First

- Install/import/CUDA/compiler/submodule issue: go to [../sub-skills/setup-and-backends/references/troubleshooting.md](../sub-skills/setup-and-backends/references/troubleshooting.md).
- Scene layout, COLMAP, depth, or conversion issue: go to [../sub-skills/data-preparation/references/troubleshooting.md](../sub-skills/data-preparation/references/troubleshooting.md).
- `train.py` optimizer, OOM, checkpoint, viewer socket, or feature-flag issue: go to [../sub-skills/training/references/troubleshooting.md](../sub-skills/training/references/troubleshooting.md).
- `render.py`, `metrics.py`, LPIPS, output layout, pretrained source override, or full benchmark issue: go to [../sub-skills/rendering-evaluation/references/troubleshooting.md](../sub-skills/rendering-evaluation/references/troubleshooting.md).
- SIBR build/run/connect/performance issue: go to [../sub-skills/viewers/references/troubleshooting.md](../sub-skills/viewers/references/troubleshooting.md).

## Frequent Global Failures

### CPU-only Environment

A CPU-only environment can validate command builders and folder layouts, but it cannot verify core gaussian-splatting training, rendering, or metrics. Preserve a required CUDA backend block when CUDA is unavailable.

### Non-Recursive Clone

Missing submodules cause extension imports/builds to fail. Initialize recursive submodules before installing extension packages.

### Source Paths in Portable Models

`cfg_args` stores the training source path. When moving or evaluating pretrained models, pass a current `-s/--source_path` override to `render.py`.

### Large or Expensive Operations

Full training, full evaluation, pretrained-model downloads, dataset downloads, COLMAP conversion, and SIBR builds can be expensive or mutating. Do not run them as implicit smoke checks. Use bundled validators and command builders first.

### Local Path Leakage

When producing public instructions or artifacts, avoid embedding private environment prefixes, activation commands, local checkout paths, or cache locations. Use placeholders such as `<checkout>`, `<scene>`, and `<model>`.

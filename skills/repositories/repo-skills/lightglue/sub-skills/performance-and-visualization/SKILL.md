---
name: performance-and-visualization
description: "Benchmark LightGlue latency and throughput, and create or save
  match, keypoint, pruning, and benchmark plots."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Performance and Visualization

Use this sub-skill when the task is about measuring LightGlue speed or making
match visualizations.

## Primary entry points

- [`scripts/benchmark_lightglue.py`](scripts/benchmark_lightglue.py): benchmark
  matcher latency or throughput with safe defaults, optional compile and
  FlashAttention toggles, pruning-threshold overrides, a synthetic fallback
  image pair, and `--save` / `--no-show` support.
- [`references/benchmarking.md`](references/benchmarking.md): benchmark
  workflow, measurement semantics, speed knobs, and weight-download caveats.
- [`references/visualization.md`](references/visualization.md): `viz2d`
  plotting helpers for matches, keypoints, pruning colors, labels, and saved
  plots.
- [`references/troubleshooting.md`](references/troubleshooting.md): common
  device, backend, compile, pruning, and headless display fixes.

## Boundaries

- For matcher constructor choices, confidence settings, and routing around
  LightGlue configuration, use `../matcher-configuration/SKILL.md`.
- For extractor selection and feature-specific setup, use
  `../extractors-and-features/SKILL.md`.
- For a one-off image-pair matching workflow rather than benchmarking or
  plotting, use `../image-pair-matching/SKILL.md`.

## Notes

- The benchmark script times matcher forward passes after feature extraction.
- First-use runs may download pretrained extractor or matcher weights.
- Runtime dependencies assumed here are `torch`, `torchvision`, `numpy`,
  `opencv-python`, `matplotlib`, and `kornia`.

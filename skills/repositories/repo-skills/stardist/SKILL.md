---
name: "stardist"
description: "Self-contained operating guidance for StarDist 0.9.2: CPU-verified
  2D/3D instance segmentation, geometry/evaluation, and optional deployment
  integrations."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# StarDist repository skill

Use this skill when a task needs the Python StarDist package for star-convex 2D polygons, 3D polyhedra, instance segmentation, NMS, matching, model training/inference, or related file integrations. This is an operating router, not a copy of the source repository.

## Install and verify

For a public CPU installation, use an isolated Python environment and install the package with its test helper when needed:

```bash
python -m pip install "stardist[test]"
python skills/disco/stardist/scripts/check_stardist_env.py
```

The compiled CPU extensions are built as part of installation. The checker must report imports for `stardist`, `stardist.models`, `stardist.geometry`, `stardist.matching`, `stardist.data`, `stardist.lib.stardist2d`, and `stardist.lib.stardist3d`. It also prints optional dependency/device diagnostics without making CUDA/OpenCL a baseline requirement. For the exact inspected source snapshot and freshness evidence, read [repo-provenance.md](references/repo-provenance.md).

## First route

- **2D images, `Config2D`, `StarDist2D`, training, normalization, tiling, multiclass:** [2d-workflows](sub-skills/2d-workflows/SKILL.md)
- **3D volumes, `Config3D`, `StarDist3D`, rays, anisotropy, block inference:** [3d-workflows](sub-skills/3d-workflows/SKILL.md)
- **labels, star distances, polygons/polyhedra, NMS, matching, patch sampling, overlays:** [evaluation-geometry](sub-skills/evaluation-geometry/SKILL.md)
- **CLI prediction, local model files, BioImage.IO, ROI/OBJ, QuPath:** [deployment-integration](sub-skills/deployment-integration/SKILL.md)

Read [api-overview.md](references/api-overview.md) for shared conventions and [troubleshooting.md](references/troubleshooting.md) before changing the environment.

## Safe operating sequence

1. Identify StarDist version/API context and whether the task is CPU baseline or an optional integration.
2. Inspect input axes, spatial shape, channel count, label dtype, model source, and expected output before calling the API.
3. Prefer a local model and a small deterministic fixture for offline/reproducible work. Pretrained registries, BioImage.IO resources, OpenCL/gputools, CUDA execution, and QuPath are optional gates.
4. Use the exact 2D/3D sub-skill contract, retain normalization/threshold/grid/ray metadata, and validate output labels.
5. For training/export/GUI work, state side effects and bound the operation before running it.

## Backend boundary

The required baseline is TensorFlow 2.x on CPU plus the compiled StarDist 2D/3D CPU extensions. A CPU import is not evidence of CUDA or OpenCL support. TensorFlow GPU, OpenCL/gputools data generation, BioImage.IO, pretrained downloads, and QuPath are explicitly optional; if they are unavailable, preserve a clear skip/limitation and continue with the CPU path where the contract has a valid substitute.

## Shared output expectations

A prediction is normally `(labels, details)`: labels are integer, spatial-only instance IDs with 0 as background; details contain sparse points/probabilities/distances and optional class information. Keep `axes`, normalization, grid, thresholds, ray configuration, anisotropy/scale, model source, and software version with persisted results. Route metric calculations through evaluation-geometry rather than treating labels as probability maps.

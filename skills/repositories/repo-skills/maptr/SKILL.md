---
name: maptr
description: "Guides agents through MapTR online vectorized HD-map workflows,
  including environment setup, nuScenes and Argoverse2 preparation, model
  configuration, training, evaluation, visualization, benchmarking, and
  compatibility troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MapTR

MapTR is an OpenMMLab-based camera-centric framework for online vectorized
high-definition map construction. Use this skill when a task names MapTR,
MapTRv2-compatible concepts, vectorized HD maps, nuScenes/Argoverse2 map
annotations, MapTR configs, `MapTRHead`, `MapTRPerceptionTransformer`,
Geometric Kernel Attention, or the MapTR `chamfer` evaluator.

This graph is for the `main` checkout represented by the provenance snapshot,
not for the separate `maptrv2` branch. Read [repository provenance](references/repo-provenance.md)
before treating a checkout as current. The generated guidance is self-contained
and distinguishes source-backed procedure from native runtime evidence.

## Route by task

- **Dataset layout, custom annotation preparation, nuScenes CAN bus, AV2 logs,
  or map-vector schemas:** read [data-preparation](sub-skills/data-preparation/SKILL.md).
- **Config selection or edits, model components, BEV encoder variants,
  point-cloud geometry, registry imports, or custom-op compatibility:** read
  [model-configuration](sub-skills/model-configuration/SKILL.md).
- **Training, distributed launch, checkpoint evaluation, chamfer metrics,
  reproducibility, FP16, or memory planning:** read
  [training-evaluation](sub-skills/training-evaluation/SKILL.md).
- **Prediction rendering, GT display formats, video assembly, throughput,
  timing, or log analysis:** read
  [visualization-benchmarking](sub-skills/visualization-benchmarking/SKILL.md).

When a request spans routes, validate data first, then config, then launch;
visualization and benchmarking consume the resulting checkpoint/artifacts.

## Compatibility boundary

The repository documents an older stack: Python 3.8, PyTorch 1.9.1 with CUDA
11.1, `mmcv-full==1.4.0`, `mmdet==2.14.0`, `mmsegmentation==0.14.1`,
`timm`, bundled `mmdetection3d==0.17.2`, `shapely==1.8.5.post1`, `av2`, and a
compiled Geometric Kernel Attention extension. Treat these as a compatibility
target, not a generic modern install recipe. Do not mix modern MMCV/MMDetection
versions into a legacy checkout without checking the compatibility reference.

The full model path needs a CUDA-capable PyTorch runtime, compiled upstream
MMCV/MMDetection3D operators, and the MapTR Geometric Kernel Attention extension.
A CPU import or a visible NVIDIA device does not prove that path. During
construction, static/config/data checks were verified; full model forward,
training, evaluation, dataset conversion, checkpoint inference, and custom-op
execution remain explicitly unverified.

## Minimal safe checks

Use the bundled helpers before expensive actions:

```bash
python <skill-root>/sub-skills/data-preparation/scripts/check_dataset_layout.py --help
python <skill-root>/sub-skills/model-configuration/scripts/check_maptr_config.py --help
python <skill-root>/sub-skills/training-evaluation/scripts/launch_distributed.py --help
python <skill-root>/sub-skills/visualization-benchmarking/scripts/make_video.py --self-check
```

The helpers are path-safe and do not download data or checkpoints. Their
references explain when a target checkout, dataset, framework, GPU, or codec is
still required. Do not treat a dry-run command as successful model execution.

## Operating order

1. Establish the documented dependency/ABI target and run the safe checks.
2. Preflight dataset roots and generated annotation names with the data route.
3. Select one complete model/config family and run the static config checker.
4. Confirm the checkpoint, data, GPU count, custom operators, and output budget.
5. Generate a dry-run command; execute only after reviewing paths and costs.
6. Evaluate with MapTR's vector metric contract, then render or benchmark outputs.
7. Preserve logs, config, checkpoint identity, dataset version, GPU/runtime
   details, and unresolved compatibility failures with the experiment.

For cross-cutting symptoms such as MMCV version assertions, missing compiled
operators, missing data files, invalid config inheritance, or misleading FPS,
read [troubleshooting](references/troubleshooting.md). The route-specific
references contain the detailed command and schema contracts.

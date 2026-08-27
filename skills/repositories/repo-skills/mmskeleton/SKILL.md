---
name: mmskeleton
description: "Guides MMSkeleton skeleton-based action-recognition, skeleton-data
  preparation, config-driven applications, and optional detector-backed pose
  workflows with explicit legacy compatibility and verification gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMSkeleton

Use this repository skill when a task names **MMSkeleton**, `mmskl`, ST-GCN,
skeleton-based action recognition, OpenPose/NTU skeleton layouts, MMSkeleton
JSON annotations, or the repository's cascade-RCNN/HRNet pose pipeline.

This is a router, not a copy of the original source tree. Start with the
smallest route below, then read only the linked references needed for the task.

## Verified scope and hard boundaries

- **Verified core:** ST-GCN graph/model construction, recognition configuration
  guidance, skeleton JSON/data transforms, checkpoint alias interpretation,
  config-driven application structure, and the repository's compiled NMS
  extension. A tiny CUDA ST-GCN forward passed in a CUDA-capable inspection
  environment.
- **Optional and unverified:** MMDetection-backed `pose_demo`,
  `pose_demo_HD`, image pose inference, and video-to-skeleton dataset building.
  These require a detector-compatible `mmcv._ext` build, detector/HRNet
  checkpoints, video dependencies, and GPU resources. Do not infer their
  readiness from the core ST-GCN smoke.
- **Not bundled:** original checkout files, datasets, downloaded checkpoints,
  video assets, or large training outputs. Use local paths supplied by the
  caller and validate them before running an expensive workflow.

## Route by user intent

1. **ST-GCN recognition, graph/model API, pretrained evaluation, training
   config, checkpoint aliases, or `mmskl` flags:** read
   [recognition](sub-skills/recognition/SKILL.md).
2. **Skeleton JSON, category labels, loader, normalization, masks, temporal
   transforms, custom feeder, or data validation:** read
   [data-preparation](sub-skills/data-preparation/SKILL.md) first, then route
   model/layout choices to recognition.
3. **Pose demo, image/video pose inference, or raw video to skeleton JSON:**
   read [pose-estimation](sub-skills/pose-estimation/SKILL.md) and run its
   readiness checker before downloading anything. Return produced JSON to
   data-preparation before recognition.
4. **A new config-driven application:** read the
   [recognition CLI and configuration reference](sub-skills/recognition/references/cli-reference.md)
   and the relevant workflow skill. MMSkeleton dispatches through a config's
   `processor_cfg`; flags are declared by `argparse_cfg` and bound into that
   config.

## Installation and environment gate

The repository is a legacy Python package. Its historical documentation used
Python 3.7 with PyTorch 1.2 and CUDA 9.2/10.0; those exact artifacts may be
unavailable. Use an isolated, compatible Python 3.7 environment and verify the
selected PyTorch CUDA build, compiler/toolkit, MMCV generation, and native
extensions before trusting a workflow. Do not mutate a user's environment.

A public baseline install is explicit and isolated; adapt the CUDA/torch
versions to the supported wheel/channel available on the target host:

```bash
conda create --yes --prefix /path/to/mmskeleton-legacy python=3.7 pip
conda install --yes --prefix /path/to/mmskeleton-legacy -c pytorch pytorch=1.13.1 torchvision=0.14.1 pytorch-cuda=11.7
conda run --prefix /path/to/mmskeleton-legacy python -m pip install mmcv==1.7.2 lazy-import
# Run the editable install from the root of an MMSkeleton checkout.
cd /path/to/MMSkeleton
conda run --prefix /path/to/mmskeleton-legacy env FORCE_CUDA=1 python -m pip install -e . --no-deps
```

The source documentation names an older PyTorch 1.2/CUDA 9.2 or 10.0
combination; use the exact historical pair only when it is still available and
compatible with the host. Align `nvcc` and GCC/G++ before building extensions.
For a bounded package check, run the recognition smoke helper after installing
the package and dependencies:

```bash
python sub-skills/recognition/scripts/run_stgcn_smoke.py --device auto
```

Use `--device cuda` for the required GPU gate. Read
[compatibility and troubleshooting](references/troubleshooting.md) when the
historical dependency set cannot be installed. For pose-specific readiness,
run the no-download checker linked from the pose sub-skill.

## Shared references

- Read [repository provenance](references/repo-provenance.md) before deciding
  whether this graph is stale for a different MMSkeleton commit.
- Read [model and compatibility notes](references/compatibility.md) for the
  verified baseline, historical-version caveat, checkpoint/download boundary,
  and optional detector limitation.
- Read [cross-cutting troubleshooting](references/troubleshooting.md) for
  import, CUDA/compiler, MMCV, checkpoint, config, and safety failures.
- Read [router metadata](references/repo-routing-metadata.json) only when
  integrating this skill into a managed repo-skills router; it is structured
  metadata, not a user workflow.

## Safety and verification discipline

Prefer a tiny synthetic model/data smoke and JSON validation before launching
full training, pretrained evaluation, checkpoint downloads, or video workers.
A full recognition result requires the correct processed dataset, class count,
graph layout, checkpoint, and CUDA runtime; a parser/help check is not an
accuracy result. A raw-video request requires the separate optional detector
gate. Preserve unresolved backend limitations in the task report instead of
silently substituting CPU behavior.

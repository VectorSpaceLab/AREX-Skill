---
name: pose-estimation
description: "Provides optional image and video pose-estimation workflows with
  cascade-RCNN or HTC detection, HRNet keypoints, skeleton-dataset handoff, and
  explicit detector-readiness gates for mmskeleton users."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pose estimation

Use this sub-skill for `pose_demo`, `pose_demo_HD`, image pose inference,
video-to-skeleton dataset building, Cascade-RCNN or HTC plus HRNet configuration,
and handing pose output to recognition. This is an **optional detector-backed
path**, not proof that the verified ST-GCN core can execute a detector.

## Gate first

Run the bundled no-download checker from any working directory when checking an
environment:

```bash
python /path/to/this-skill/scripts/check_pose_readiness.py --device cuda
python /path/to/this-skill/scripts/check_pose_readiness.py --device cuda --require-detector
```

Use the second form only when detector execution is required. It returns
nonzero when the detector stack is absent or incomplete; without
`--require-detector`, the checker is informational and returns zero. The
checker never downloads weights and does not run an image, video, or detector
workflow. See [compatibility](references/compatibility.md) and
[troubleshooting](references/troubleshooting.md).

The current evidence permits the following conservative statement: torch's CUDA
core works in the prepared environment, but the MMDetection workflow is
unverified. Lightweight MMCV lacks `mmcv._ext`, and an attempted
`mmcv-full==1.7.2` source build failed because `thrust/complex.h` was missing.
MMDetection workflows are therefore optional and unresolved. **Do not infer
detector readiness from a successful ST-GCN smoke.**

## Route

- For a single image or frame and a Python result, use the documented
  `init_pose_estimator` / `inference_pose_estimator` APIs; read
  [api-reference](references/api-reference.md).
- For sequential video inference and an optional rendered output video, use
  `pose_demo` (Cascade-RCNN + HRNet) or `pose_demo_HD` (HTC + HRNet); read
  [workflows](references/workflows.md).
- For a directory of videos and recognition-ready JSON files, use the
  `processor.skeleton_dataset.build` configuration flow. `tracker_cfg` must be
  `null`; a non-null tracker raises `NotImplementedError` in the builder.
- Send produced JSON to [data-preparation](../data-preparation/SKILL.md) for
  validation, then send validated skeleton data to
  [recognition](../recognition/SKILL.md). Do not make this sub-skill the JSON
  validator or the ST-GCN recognition guide.

## Read next

- [API and output contract](references/api-reference.md)
- [CLI and dataset workflows](references/workflows.md)
- [dependency, hardware, and checkpoint compatibility](references/compatibility.md)
- [failure handling and unresolved limits](references/troubleshooting.md)

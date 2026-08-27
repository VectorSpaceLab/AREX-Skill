---
name: odometry-slam
description: "This skill guides a Researcher through gradSLAM odometry
  selection, ICP configuration, map fusion, and small deterministic RGB-D SLAM
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Odometry and SLAM

Use this skill when a task must localize RGB-D frames, build a global
`Pointclouds` map, or choose between known poses, point-to-plane ICP, and
GradICP. Start with the input contract in
[the API reference](references/api-reference.md), then select a workflow from
[the workflow guide](references/workflows.md). The bundled smoke programs are
CPU-only, in-memory, and do not download data or open a viewer:

- `python scripts/pointfusion_smoke.py --help`
- `python scripts/icpslam_smoke.py --help`

## Route the odometry method

- Choose `gt` when each frame has trustworthy `poses`. It is the deterministic
  baseline and is the appropriate first check for a new RGB-D/data pipeline.
- Choose `icp` for non-differentiable point-to-plane LM alignment when the
  consecutive clouds have sufficient overlap, usable map normals, and a good
  initial pose.
- Choose `gradicp` when the alignment path must retain the package's
  differentiable GradLM-style update. Treat this as a differentiable odometry
  provider, not as proof that every map-building operation is differentiable.
- `ICPSLAM` and `PointFusion` accept only the exact strings `gt`, `icp`, and
  `gradicp`; reject any other value before constructing a long run.

## Prepare inputs

1. Keep RGB-D tensors in one device and dtype. The normal channels-last form is
   `colors: (B,L,H,W,3)`, `depths: (B,L,H,W,1)`, intrinsics `(B,1,4,4)`, and,
   when available, poses `(B,L,4,4)`. Pass `channels_first=True` only for the
   corresponding `(B,L,C,H,W)` tensors.
2. Use a `RGBDImages` object for frames and a `Pointclouds` object for map or
   live clouds. Point lists are `(N,3)` and normals must have the same shape as
   their point list. Use sequence slices such as `frames[:, t]` for a one-frame
   object.
3. For ICP or GradICP, ensure the map has normals. Invalid depths become zero
   vertices and can produce zero normals or no correspondences; use valid,
   non-degenerate depth geometry and inspect the resulting point counts.
4. Start with `dsratio=1` or `2` on a tiny test, then increase it only after
   correspondence counts and pose output are sensible. `downsample_rgbdimages`
   and the SLAM localization path require a one-frame RGB-D object.

## Run SLAM safely

- `ICPSLAM(odom=..., dsratio=..., numiters=..., damp=..., dist_thresh=...,
  lambda_max=..., B=..., B2=..., nu=..., device=...)` returns
  `(pointclouds, poses)`; poses are `(B,L,4,4)` and the map contains one global
  cloud per batch item.
- `PointFusion` has the same odometry/solver arguments and additionally uses
  `dist_th`, `angle_th` (degrees), and `sigma` for correspondence filtering and
  confidence-weighted fusion. Its map contains normals, colors, and confidence
  features when valid depths are present.
- For `forward(frames)`, give a sequence. For `step`, give a one-frame
  `live_frame`; pass `prev_frame` for `icp`/`gradicp`, and pass `None` on the
  first frame. With `gt`, poses on the live frame are used directly and
  `prev_frame` is not the odometry input.
- Run a `gt` smoke first, then the same fixture with `icp` and `gradicp`. Check
  pose and padded map shapes, finite values, device, and point counts before
  interpreting trajectory quality.

## Differentiability and devices

GradICP keeps tensor operations in the update path and is intended for
*differentiable* odometry. Nearest-neighbor index selection, conditionals,
point-cloud padding, and map fusion still limit smooth end-to-end gradients;
this skill does not claim a full differentiable SLAM graph. ICP uses a
trust-region/LM branch and is primarily an alignment routine. Ground truth
computes `T = inverse(T1) @ T2` from the supplied poses. Keep CPU as the
portable baseline; an accelerated device is additive evidence, not implied by
successful CPU execution.

## External data boundary

TUM, ICL, and ScanNet workflows need a user-provided dataset root and the
adapter's expected files/metadata. They are not replaced by the tiny smoke
fixture. Ask for the dataset layout and pose/depth conventions, validate one
batch into the RGB-D shape contract, and only then hand that batch to
`PointFusion` or `ICPSLAM`. Do not download data, open GUI viewers, or claim
that an external sequence was validated when only a synthetic fixture ran.

## Recovery

For extension failures, invalid odometry choices, missing normals, empty
correspondences, shape/device mismatches, fusion thresholds, and external-data
handoff, use [troubleshooting](references/troubleshooting.md). For exact
signatures, output shapes, solver controls, and fusion helper contracts, use
[the API reference](references/api-reference.md). The scripts are intentionally
small adapters, not replacements for dataset validation or benchmark runs.

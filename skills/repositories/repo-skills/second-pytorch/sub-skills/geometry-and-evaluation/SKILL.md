---
name: geometry-and-evaluation
description: "Use for CPU-safe SECOND box geometry, coordinate conversion,
  encoding and target assignment, IoU/NMS decisions, KITTI or NuScenes
  evaluation, result conversion, and tiny-fixture validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Geometry and evaluation

Use this route when a task mentions lidar or camera boxes, corners, yaw, encode/decode,
anchors, target assignment, IoU, NMS, KITTI labels/AP, NuScenes result JSON, or
coordinate transforms. This is a **static/CPU-safe operating route**. It does not
prove detector execution.

## Operating boundary

- Prefer NumPy-only geometry and fixture checks. Read [api-reference.md](references/api-reference.md)
  for signatures, shapes, and source-faithful dimension order.
- Read [coordinate-systems.md](references/coordinate-systems.md) before converting
  KITTI camera boxes, internal lidar boxes, or NuScenes boxes.
- Read [evaluation.md](references/evaluation.md) before building annotations,
  interpreting AP, or writing NuScenes submissions.
- Run the bundled helper before changing box conventions:

  ```bash
  python skills/disco/second-pytorch/sub-skills/geometry-and-evaluation/scripts/geometry_smoke.py --help
  python skills/disco/second-pytorch/sub-skills/geometry-and-evaluation/scripts/geometry_smoke.py
  ```

  Expected output contains four `[PASS]` checks and `geometry smoke: PASS`; the
  helper imports only NumPy and never imports the detector, spconv, Numba CUDA,
  or Torch.

## Safe workflow

1. Normalize every box array to an explicit shape and convention. Internal lidar
   boxes are normally `[N, 7] = [x, y, z, w, l, h, rz]`; preserve any velocity or
   custom values only after documenting their trailing columns.
2. Check dimensions are positive, row counts agree, calibration matrices are
   homogeneous-compatible, and labels/scores have the same first dimension.
3. For corners, use `center_to_corner_box3d` with lidar `axis=2` and the correct
   origin; use `center_to_corner_box2d` for `[x, y, w, l, rz]`. Never silently
   swap `w,l,h` with KITTI `l,h,w`.
4. For regression, pair each target with its anchor (`[N,7]`), select linear
   dimensions or log dimensions consistently, and compare decoded centers,
   dimensions, and angle modulo the selected period. Vector-angle coding has
   code size 8 rather than 7.
5. For assignment, inspect feature-map order `[D,H,W]`, class-specific anchor
   ranges, thresholds, and label semantics (`1+` positive, `0` negative,
   `-1` ignore). Use a tiny overlap matrix before sampling positives.
6. Treat NMS as a separate backend decision. The axis-aligned `nms_jit`
   algorithm is CPU NumPy/Numba math, but its historical module may import
   legacy spconv transitively; rotated CPU NMS depends on the same helpers. GPU
   NMS and rotated IoU use legacy Numba CUDA/spconv interfaces and are **not verified**.
7. For KITTI, validate annotation keys, class spelling, dimensions, camera/lidar
   convention, and `z_axis`/`z_center` before calling evaluation. For NuScenes,
   validate sample tokens, class mapping, quaternion and `wlh` order, range
   filtering, and required devkit availability before invoking the evaluator.

## API and failure routing

- Use [api-reference.md](references/api-reference.md) for box math, anchors,
  target assignment, similarity, point-in-box, and NMS signatures.
- Use [coordinate-systems.md](references/coordinate-systems.md) for axes,
  origins, angle periods, calibration direction, and visualization conventions.
- Use [evaluation.md](references/evaluation.md) for KITTI schemas, metric output
  shapes, NuScenes JSON fields, and minimal perfect-match fixtures.
- Use [troubleshooting.md](references/troubleshooting.md) when imports, optional
  dependencies, malformed arrays/configs, CLI/API calls, or evaluator output fail.

## Verification status and historical caveats

This checkout has no setup metadata. The model path uses legacy spconv and Numba
APIs; modern spconv 2.x is not proven compatible. The inspection environment had
NumPy, Numba, Torch, spconv, Fire, tensorboardX, nuscenes-devkit, and related
packages, and an A100 CUDA smoke was available, but detector execution was not
accepted as verified. In particular, the installed spconv did not expose the
legacy `non_max_suppression`/`VoxelGeneratorV2` interfaces. Do not claim that GPU
NMS kernels, modern spconv NMS, or the full detector runtime executed successfully.
For new detector work, treat this route as historical guidance and prefer a
maintained SECOND implementation rather than extending the deprecated runtime.

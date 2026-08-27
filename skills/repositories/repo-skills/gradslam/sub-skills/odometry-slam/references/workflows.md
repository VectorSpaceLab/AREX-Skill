# Safe odometry and SLAM workflows

These recipes are deliberately small and use only in-memory tensors. They are
for API and shape checks, not for measuring trajectory quality.

## 1. Make a deterministic RGB-D fixture

Use a channels-last fixture with at least a few pixels of nonzero, non-flat
depth. A mild depth ramp produces usable local geometry and avoids the
single-point problem caused by an overly large downsampling ratio.

```python
B, L, H, W = 1, 2, 8, 8
colors = deterministic_float_tensor(B, L, H, W, 3)
depths = positive_depth_ramp(B, L, H, W).unsqueeze(-1)
K = identity_intrinsics(B, W, H)       # shape (B,1,4,4)
poses = identity_poses(B, L)           # shape (B,L,4,4)
frames = RGBDImages(colors, depths, K, poses)
```

Keep every tensor on CPU for the first run. If the task intentionally tests
pose-free operation, construct `RGBDImages(colors, depths, K)` and add an
identity pose to the first live frame before a non-`gt` `step`.

## 2. Compare all odometry choices

Run the same fixture through `gt`, `icp`, and `gradicp`, changing only
`odom`. Use `dsratio=1` or `2`, `numiters=2` or `3`, and a conservative
`dist_thresh` only when the fixture's scene scale is known. For each run:

1. Construct a fresh `ICPSLAM` or `PointFusion` object and a fresh fixture.
2. Record `poses.shape == (B,L,4,4)` and the map's per-batch point counts.
3. Assert `torch.isfinite(poses).all()` and finite point tensors.
4. Record warnings and failures instead of interpreting a failed solver as a
   valid pose estimate.

The bundled programs implement this comparison with `--odom all`:

```bash
python scripts/pointfusion_smoke.py --odom all
python scripts/icpslam_smoke.py --odom all
```

Use `--odom gt` to isolate container/fusion behavior when the native extension
is unavailable. The programs print one result line per odometry choice with
pose and map shapes; they do not call Open3D or Plotly display functions.

## 3. Step through frames

For manual control, start with `Pointclouds(device="cpu")` and `prev_frame =
None`:

```python
maps = Pointclouds(device="cpu")
prev_frame = None
for t in range(frames.shape[1]):
    live = frames[:, t]
    if t == 0 and live.poses is None:
        live.poses = torch.eye(4).view(1, 1, 4, 4)
    maps, live.poses = slam.step(maps, live, prev_frame)
    prev_frame = None if slam.odom == "gt" else live
```

Use `prev_frame = None` for `gt`, because `ICPSLAM` warns that it is unused.
For ICP/GradICP, preserve the prior frame's pose and keep the map and frame on
the same device. `step` returns the current `(B,1,4,4)` pose.

## 4. Inspect a provider directly

To test correspondence and solver behavior without SLAM map updates, derive
point clouds from one-frame RGB-D objects, apply a known rigid transform to
make a target cloud, and call the provider with the target as map and the
original as frame. Compare the returned `(B,1,4,4)` transform to the known
transform within a tolerance appropriate to point density and iteration count.

The target must supply normals for ICP and GradICP. Use enough non-coplanar or
sloped points for the six-parameter solve. If the target and source are
identical, the expected smoke result is an identity-like transform; that tests
plumbing but not recovery of translation or rotation.

## 5. Check GradICP gradient intent

Use a small point-cloud pair whose source points have `requires_grad=True`.
Call `GradICPOdometryProvider.provide`, form a scalar from the returned matrix,
and inspect `requires_grad` and `source.grad` after backward. A missing or
non-finite gradient is a diagnostic result, not a reason to add `.detach()`.
Nearest-neighbor selection, branch logic, and map indexing can make the
full-SLAM gradient discontinuous or unavailable; report the exact stage that
loses it.

## 6. Tune PointFusion separately from odometry

First verify localization with `ICPSLAM`. Then construct `PointFusion` with
the same odometry settings and change one fusion control at a time:

- Lower `dist_th` to require closer point agreement; increase it only when
  expected overlap is being rejected.
- Lower `angle_th` to require more similar normals; use degrees, not radians.
- Change `sigma` only after correspondence behavior is understood; it controls
  confidence weighting, not camera noise calibration by itself.

Compare initial and updated `num_points_per_pointcloud`, and check that the map
has `has_normals`, `has_colors`, and `has_features` when non-empty.

## 7. Hand off external TUM or ScanNet data

Do not substitute the tiny fixture for a dataset run. Obtain the user's local
TUM/ICL sequence or ScanNet extraction and metadata, then verify:

- the adapter can produce one batch without downloading or opening a viewer;
- colors, depths, intrinsics, and optional poses match the RGB-D shape contract;
- depth units and pose convention are documented for the selected sequence;
- `gt` is used only when poses are present and trusted;
- ICP/GradICP use an overlap-compatible frame spacing and valid normals.

Only after that handoff should a longer `forward` run be attempted. Keep
visualization and benchmark metrics as separate, explicitly approved steps.

---
name: perception-geometry
description: "Route RGB-D projection, heightmap construction, rigid transforms,
  camera calibration data, workspace bounds, and depth-unit diagnostics for
  Visual Pushing and Grasping."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Perception and geometry

Use this route when a task starts with an RGB-D frame and needs camera-space
points, robot-frame points, a top-down heightmap, camera calibration files,
workspace clipping, or the repository's rigid-transform helpers. This skill
is an operating reference, not a replacement for a camera driver, robot
controller, simulator, or learning loop.

## Evidence and compatibility boundary

The contracts below are distilled from the historical source commit
`580e2334beec0d83b49e6ca89d7542b79d1d4350`, especially `utils.py`,
`robot.py`, `real/camera.py`, `calibrate.py`, `main.py`, `trainer.py`,
`logger.py`, and the README. Those filenames are source evidence labels, not
bundled runtime modules. The source is a Python 2/early-Python-3 project with
no package metadata. A bounded current-Python numerical-stack check is only a
compatibility diagnostic and does **not** establish modern full-loop
compatibility.

Let `<skill-root>` mean the directory containing the root `SKILL.md`. The
bundled smoke helper is deliberately standalone and does not import the
historical checkout. Run it before trusting a new fixture:

```bash
python <skill-root>/sub-skills/perception-geometry/scripts/geometry_smoke.py --help
python <skill-root>/sub-skills/perception-geometry/scripts/geometry_smoke.py
```

See [the API contracts](references/api-reference.md), [calibration and data
formats](references/data-and-calibration.md), [failure diagnosis](references/troubleshooting.md),
and the [standalone smoke helper](scripts/geometry_smoke.py).

## Route and execute

1. **Normalize the boundary.** Establish image height `H`, width `W`, RGB
   channel order, intrinsic matrix units, and whether depth is already in
   metres. The source formula has no shape or unit validation.
2. **Apply depth scale exactly once.** The RealSense TCP client first applies
   the per-frame wire scale to `uint16` depth. The operator-supplied application
   then applies the calibration scale from
   `<CALIBRATION_OUTPUT_DIR>/camera_depth_scale.txt`. Do not apply either
   factor a second time; the historical `real/` path is source evidence only.
3. **Project with `get_pointcloud`.** Supply RGB `(H,W,3)`, depth `(H,W)`, and
   a 3x3 pinhole matrix. The result is row-major camera points `(H*W,3)` and
   matching RGB rows `(H*W,3)`.
4. **Transform with the camera pose.** `cam_pose` is a homogeneous 4x4
   camera-to-robot/world pose: `p_robot = R @ p_camera + t`. It is not the
   inverse of the pose expected by `get_heightmap`.
5. **Rasterize with `get_heightmap`.** Bounds are robot-coordinate metres;
   resolution is metres per pixel. The map is indexed `[y,x]`, has shape
   `(round(y_span/res), round(x_span/res))`, and keeps the greatest-z point at
   a colliding pixel because points are sorted by increasing z before
   assignment.
6. **Handle empty cells at the model boundary.** `get_heightmap` uses NaN
   for empty cells in its usual negative-bottom workspace. The main loop
   copies the depth map and replaces NaN with zero before calling `Trainer`.
   Geometry itself must remain in metres and must not perform ImageNet-style
   normalization.

## Exact operational facts

- RGB is RGB, not BGR, at the geometry boundary. Simulation data is flipped
  horizontally and converted to `uint8`; the RealSense client returns
  `uint8` RGB. `get_pointcloud` preserves the three source channel values.
- `get_heightmap` filters x/y lower-inclusive and upper-exclusive, and z
  upper-exclusive. It does not explicitly filter z below the lower workspace
  bound; the post-rasterization subtraction clips values below the bottom to
  zero. Treat this historical behavior as an API quirk, not a general policy.
- `workspace_limits` is a 3x2 array ordered `[x, y, z]`, each row
  `[minimum, maximum]`. Main defaults are simulation
  `[[-0.724,-0.276],[-0.224,0.224],[-0.0001,0.4]]` and real
  `[[0.3,0.748],[-0.224,0.224],[-0.255,-0.1]]` metres. The calibration script
  uses a separate grid `[[0.3,0.748],[0.05,0.4],[-0.2,-0.1]]` and 0.05 m grid
  spacing; do not silently substitute it for the runtime workspace.
- The main default heightmap resolution is `0.002` metres/pixel. For either
  0.448 m by 0.448 m main workspace, the resulting map is 224 by 224.
- `euler2rotm` consumes `[rx,ry,rz]` radians and returns `Rz @ Ry @ Rx`.
  `rotm2euler` returns a length-3 radian array and asserts orthogonality.
  `angle2rotm` returns a 4x4 homogeneous matrix and requires a NumPy axis.

## Scope boundary

For TCP framing, RealSense server setup, robot motion, calibration execution,
or physical/simulator prerequisites, hand off to the repository's real-robot or
simulation route. For model inputs, rotations inside the network, rewards, or
training updates, hand off to training; this route only records the exact
RGB/depth normalization boundary needed to feed that route.

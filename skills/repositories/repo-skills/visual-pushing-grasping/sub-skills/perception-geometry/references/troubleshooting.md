# Geometry troubleshooting

Use these checks without importing the historical package. The source helpers
are permissive and often fail later with an indexing or broadcasting error, so
diagnose the boundary first. The deterministic cases in
[`geometry_smoke.py`](../scripts/geometry_smoke.py) cover a nonidentity pose,
workspace clipping, zero/NaN depth, and transform round trips.

## Shape and dtype failures

- Require RGB `(H,W,3)` and depth `(H,W)` with the same `H,W`; do not pass a
  grayscale image, channel-first tensor, or an `(H,W,1)` depth array.
- Require intrinsics with shape `(3,3)` and finite nonzero `fx,fy`; verify
  `cx,cy` are in the same pixel coordinate convention as the frame.
- Require pose `(4,4)` with finite values and last row near
  `[0,0,0,1]`. The source only consumes the first three rows/columns but
  accepting a malformed homogeneous matrix makes frame mistakes invisible.
- Use numeric arrays. RGB is normally `uint8` in 0..255; depth must be a
  floating metre array by the time it reaches geometry. The source does not
  clip RGB or convert millimetres, and integer division/overflow assumptions
  differ across old and new NumPy.
- For a reproducible error, print `shape`, `dtype`, finite fraction, min/max
  of finite depth, and the four intrinsic values before calling a helper.

## Zero, NaN, and empty cells

`get_pointcloud` does not reject zero depth. It emits zero-valued camera
points; depending on K and workspace, they can be rasterized. NaN depth emits
NaN coordinates and normally fails the finite comparisons in heightmap
filtering. The heightmap initializes depth to zero, subtracts `z_min`, clamps
negative values, and maps the sentinel `-z_min` to NaN. Therefore:

- use `np.isnan(depth_heightmap)` to identify empty cells;
- do not interpret an input zero as a valid surface without a sensor policy;
- do not replace NaN before geometry; replace it only at the documented model
  boundary if feeding `Trainer`;
- reject negative or infinite sensor depths in a caller-side validator even
  though the historical function does not.

A valid point at exactly the same value as the sentinel can also become NaN.
This is a source quirk, especially when `z_min` is zero; do not “fix” it in a
compatibility wrapper without deciding whether a behavior change is allowed.

## Clipping and map collisions

The x/y upper bounds are exclusive, so a point on the far edge is dropped.
The source uses rounded map dimensions and floor indices; non-divisible spans
can produce a valid point index beyond the rounded allocation. Prefer a
resolution that divides both x and y spans, or validate the computed index.
There is no lower-z filter. Points below the bottom are clipped to zero rather
than rejected, while the model later treats zero as empty/padded input. If a
new implementation needs a strict volume, explicitly add `z >= z_min` and
record that it no longer exactly matches the historical helper.

When several points hit one pixel, ascending-z sorting means the last
assignment is the highest z. Sparse point clouds are expected; do not fill
holes by interpolation unless the downstream contract is changed. A shifted
or mirrored map usually indicates swapped x/y bounds, image flip, or inverse
pose, not a model issue.

## Unit and scale errors

The most common symptom of a map that is uniformly too small/large is a depth
scale applied zero or two times. The real camera stream converts uint16 using
its wire scale; the separately reviewed application then applies
`<CALIBRATION_OUTPUT_DIR>/camera_depth_scale.txt`. A calibration scale is not
a millimetre-to-metre conversion. Convert raw sensor units once, then use the
dimensionless fitted multiplier once. The historical `main.py` and `real/`
paths are source evidence only.

Check the saved-image convention before using logger output: camera depth PNG
values represent metres*10,000, while heightmap depth PNG values represent
metres*100,000. Intrinsics are pixel units, workspace/pose are metres, Euler
angles and angle-axis values are radians.

## Nonrigid or invalid calibration

A pose with shear, anisotropic scale, reflection, NaN, or a wrong frame
convention is not a valid `cam_pose`. Check `R.T @ R`, determinant, homogeneous
row, and point-to-point residuals. The checkerboard fit in `calibrate.py` uses
an SVD rigid transform and optimizes only a scalar Z scale. High residuals
across the calibration grid suggest wrong checkerboard offset/orientation,
incorrect depth units, stale intrinsics, missed detections, or a moving
camera. Recollect data and inspect correspondences; do not hide the error by
passing a general affine transform to a function documented as rigid.

## NumPy and historical-runtime caveats

The source predates current numerical libraries. A bounded current-Python
check may exercise the standalone geometry helper, but no modern full-loop
claim is made. Source-only application paths outside these formulas use old
APIs and Python-2 division/shape assumptions. A current NumPy release can
expose those issues even if projection math itself is sound. Preserve the
source contract in compatibility tests, and isolate any modernization (dtype
normalization, explicit integer indices, finite checks) behind a deliberate,
operator-reviewed adapter.

For camera transport or robot motion failures, route to real-robot; for
simulator service failures, route to simulation. This route stops at data and
geometry validation.

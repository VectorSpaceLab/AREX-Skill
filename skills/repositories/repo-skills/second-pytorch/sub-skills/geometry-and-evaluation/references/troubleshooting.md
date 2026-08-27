# Geometry and evaluation troubleshooting

## Install and import

- **Symptom:** importing the full geometry module fails at `spconv.utils`,
  `torchplus`, or a compiled extension. **Cause:** this checkout has no setup
  metadata and its model path assumes legacy dependencies. **Recovery:** run
  `scripts/geometry_smoke.py` first; it is NumPy-only. Restrict static work to
  bundled contracts, and do not “fix” the route by claiming a modern spconv 2.x
  API is compatible.
- **Symptom:** `non_max_suppression`, `rotate_non_max_suppression_cpu`, or
  `VoxelGeneratorV2` is missing. **Cause:** current spconv lacks the old names.
  **Recovery:** use `nms_jit` conceptually for axis-aligned CPU fixtures or a
  separately validated modern implementation; mark legacy rotated/GPU routes
  blocked. Do not run detector execution as a verification substitute.
- **Symptom:** Numba CUDA reports missing driver/NVVM or device selection fails.
  **Recovery:** stop at the CPU/static route, record the missing backend, and
  avoid setting historical CUDA environment variables in generated guidance.
  GPU NMS kernels and rotated IoU are not verified here.

## Optional dependencies

- KITTI array math can be reasoned about with NumPy, but source imports may pull
  Numba, spconv, Torch, or SciPy transitively. Separate pure shape/math checks
  from package import checks.
- NuScenes conversion/evaluation needs the NuScenes devkit and pyquaternion
  (plus its dataset files, calibrated metadata, and evaluation config). If the
  devkit is unavailable, validate JSON shape and token/class consistency only;
  do not report NuScenes metric values.
- OpenCV is needed by visualization helpers. Visualization is optional and must
  not be used as evidence that coordinates are correct; compare corners or
  projected points numerically first.

## Data and config validation

- **Symptom:** `ValueError` or nonsensical corners after conversion. Check every
  row is `[x,y,z,w,l,h,rz]` or explicitly camera `[x,y,z,l,h,w,ry]`; reject
  negative/zero dimensions; check `centers.shape[0] == dims.shape[0] == angles.size`.
- **Symptom:** boxes are vertically shifted. KITTI starts at bottom center while
  internal lidar boxes are center-origin. Apply the explicit z-origin adjustment
  once, not twice; validate with a box whose expected bottom is known.
- **Symptom:** dimensions look plausible but BEV is rotated/swapped. The source
  expects lidar `[w,l]` and camera `[l,h,w]`; KITTI text is `[h,w,l]`. Never
  “repair” this with a yaw change until the dimension order is fixed.
- **Symptom:** assignment has no positives. Inspect anchor shape `[A,7+C]`, GT
  shape `[G,7+C]`, class labels starting at 1, matched/unmatched thresholds,
  and whether `anchors_mask` pruned all anchors. Remember best-anchor forcing
  can create a positive even below threshold.
- **Symptom:** anchor count differs from expectation. Confirm feature order
  `[D,H,W]`, number of sizes, rotations, custom columns, and whether
  `generate_anchors` flattened class-specific maps. Check `code_size` separately
  from anchor dimensionality.

## CLI and API misuse

- **Symptom:** `split`/`reshape` errors in encoders. Inputs are not paired
  2-D arrays with the same first dimension or the angle-vector flag differs
  between encode and decode. Validate expected code size 7/8 (+custom) before
  calling. Avoid zero anchor dimensions because log ratios and divisions become
  invalid.
- **Symptom:** `BevBoxCoder` returns five/six columns but caller expects seven.
  It intentionally slices full boxes to `[x,y,w,l,rz]`; use its `decode` output,
  which inserts fixed z and h, or use `GroundBox3dCoder` for full 3-D residuals.
- **Symptom:** `nms` keeps unexpected boxes. Check whether boxes are xyxy with
  score in column 4, whether `eps` is inclusive, score sort order, threshold
  comparison (`>=` in the CPU JIT), and whether class-wise NMS was intended.
  `soft_nms_jit` mutates input; pass a copy.
- **Symptom:** evaluator says missing key or broadcasts arrays. Use
  `empty_result_anno` for no detections and ensure every annotation dict has
  parallel first dimensions. `get_official_eval_result` expects `bbox`,
  `location`, `dimensions`, `rotation_y`, `alpha`, and `score` in addition to
  class/difficulty fields.

## Workflow-specific failures

- **Round-trip mismatch:** first compare centers and dimensions, then compare
  `limit_period(decoded_rz - source_rz, period=2*pi)`. If dimensions are
  `[l,w,h]` instead of `[w,l,h]`, the round trip may still look numerically
  stable while corners are wrong; assert corner extents and axis labels.
- **Period boundary error:** raw difference near `pi` is not a real heading
  error for a pi-periodic rectangle. Use the same `limit_period` period as the
  training/evaluation convention and report the representative interval.
- **KITTI perfect-match AP is low or zero:** check `name` case (`Car` versus
  custom names), one-to-one frame ordering, `bbox` shape `[N,4]`, `alpha=-10`
  behavior, difficulty filters, `z_axis`/`z_center`, and that detections have
  finite scores. Do not tune NMS until a one-frame schema fixture works.
- **NuScenes JSON rejected:** check every result token exists, each result's
  `sample_token` matches its dictionary key, `translation` is global frame,
  `size` is `wlh`, quaternion has four values in devkit order, velocity has two,
  and detection names/attributes are allowed. Ensure the selected version maps
  to the correct eval set and the per-class range filter did not drop all boxes.
- **NuScenes AP unexpectedly changes with sweeps:** the historical wrapper uses
  NaN velocity when no sweep is available and its README recommends ten sweeps.
  Compare token coverage and velocity presence before attributing changes to
  geometry. A key-frame-only fixture can validate schema but cannot establish
  the historical performance claim.
- **Shape mismatch in synthetic tests:** print `shape`, `dtype`, and the first
  row of every array; reject ragged lists before NumPy conversion. Run the
  bundled helper after each convention edit so malformed shape handling remains
  explicit.

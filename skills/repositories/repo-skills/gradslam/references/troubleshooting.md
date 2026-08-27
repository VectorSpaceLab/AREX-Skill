# Cross-cutting troubleshooting

Use the nearest sub-skill troubleshooting page after these package-level checks.
Keep the original exception, package versions, Torch build, device, tensor
shapes, and caller-owned data paths in the diagnostic record.

## `import gradslam` fails

1. Run `python scripts/check_environment.py --json` using the bundled script.
   It imports dependencies independently, so a failure can be localized before
   GradSLAM's package import completes.
2. Confirm that the interpreter used for the check is the one used by the
   caller. Do not repair a global or shared environment blindly.
3. Verify `torch`, `open3d`, `chamferdist`, `kornia`, `cv2`, `plotly`, and
   `yaml`. GradSLAM imports Open3D at package import time, and odometry can expose
   extension compatibility failures early.
4. Run `python -m pip check`. Resolve missing requirements before interpreting a
   tensor or dataset error.

## `chamferdist` reports `undefined symbol`

This is usually a compiled-extension/Torch ABI mismatch. The extension may have
been built or downloaded against a different Torch than the environment now
imports.

- Record the final Torch version/build first.
- Rebuild `chamferdist==1.0.0` against that exact Torch in an isolated
  environment; disable cached/prebuilt reuse when necessary.
- Re-run its import, then `import gradslam`, then the odometry smoke.
- Do not solve the error by repeatedly upgrading only Torch: every compiled
  dependent extension must match the final ABI.

## Kornia fails on an old Torch API

A historical Torch version may satisfy package metadata while a modern Kornia
release expects newer symbols. Pin a mutually compatible combination or choose
a newer Torch that remains compatible with this package, then rebuild binary
extensions. Treat the package's old lower bound as historical metadata, not a
complete modern solver constraint.

## Open3D or Plotly display fails

Import and object construction do not prove that GUI/browser display is
available. In remote/headless contexts, keep `as_figure=False` where supported,
inspect object/tensor properties, and do not call `.show()` or Open3D drawing.
A missing display server is not evidence that RGB-D geometry failed.

## Device or dtype mismatch

- Keep every constructor tensor on one device and use a consistent floating
  dtype for geometry.
- Confirm the Torch build and `torch.cuda.is_available()` before using `.cuda()`.
- Move complete `RGBDImages`/`Pointclouds` structures using their device methods
  rather than moving selected internal fields independently.
- A CPU pass is the portable baseline; do not label CUDA verified unless the
  same requested path ran in a CUDA-capable environment.

## Shape or frame error crosses sub-skills

Write down `B,L,H,W,C`, channels-first/last, depth units, intrinsics shape,
pose direction, and transform naming before debugging:

- dataset batch and metadata: datasets troubleshooting;
- RGB-D constructor, map caches, ragged/padded clouds: structures
  troubleshooting;
- point/pixel rank, matrix batching, transform direction: geometry
  troubleshooting;
- correspondences, normals, solver/fusion thresholds: odometry-slam
  troubleshooting.

Do not fix a shape error by arbitrary `squeeze()`/`unsqueeze()` operations.
Re-establish the owning API's contract at the boundary.

## External dataset fails

The package does not download or repair TUM, ICL-NUIM, or ScanNet. Run the
bundled dataset layout checker, construct one short sample, and verify depth
scale, intrinsics, pose identity, and finite tensors before SLAM. Layout success
only proves selected names and paths exist; image decode, timestamp quality,
and numeric pose matrices remain caller-owned checks.

## Configuration merge fails

`CfgNode` enforces existing keys and replacement types by default. Build a base
schema, apply broad file/tree merges before list overrides, and freeze last.
Use the configuration troubleshooting reference for unknown keys, renamed or
deprecated keys, local `new_allowed`, and list/tuple coercion. Do not turn off
schema checks globally to hide a misspelled key.

## Odometry or fusion produces empty/invalid output

Start with the known-pose (`gt`) tiny smoke, then ICP, then GradICP. Check
positive depth, map normals, cloud sizes, overlap, finite poses, and device
alignment before tuning solver or fusion thresholds. The differentiable
provider does not make nearest-neighbor selection and all map-fusion control
flow smoothly differentiable.

## Historical warning from `tumutils`

This release can emit a warning around a malformed zero-quaternion branch in
its trajectory helper. Use valid nonzero quaternions and the package's
`pointquaternion_to_homogeneous` path for new inputs. Record the release and
warning; do not edit installed source as an implicit repair.

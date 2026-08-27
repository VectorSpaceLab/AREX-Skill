# Odometry and SLAM troubleshooting

## `chamferdist` import or ABI failure

ICP and GradICP import `chamferdist`'s nearest-neighbor extension. Errors such
as an undefined C++/Torch symbol, an extension load failure, or a crash during
`knn_points` usually mean that the installed extension was built for a
 different PyTorch/Python/ABI combination. Do not debug the solver first.

1. Activate the exact environment that will run gradSLAM.
2. Record `python`, PyTorch, `chamferdist`, and CUDA/CPU variant versions.
3. Import `torch` and `chamferdist` independently, then import the selected
   odometry module.
4. Reinstall or rebuild `chamferdist` against that active PyTorch, without
   mixing wheels from another environment. Keep the environment coherent with
   the package's older dependency metadata rather than allowing a resolver to
   silently replace Torch.
5. Re-run the CPU smoke with `--odom gt`, then `--odom icp` and `--odom
   gradicp`. A ground-truth pass does not certify ICP/GradICP if the extension
   still fails.

An absent CUDA runtime is not an ICP/GradICP import explanation when the
selected environment is CPU-only; report CPU verification and leave CUDA
unverified.

## Invalid odometry selection

`ICPSLAM` and `PointFusion` raise `ValueError` for anything outside `gt`,
`icp`, and `gradicp`. Check spelling and keep CLI choices aligned with those
literal values. The constructors do not accept an arbitrary provider object or
an alias such as `groundtruth`.

## Missing normals or wrong container

`ICPOdometryProvider` and `GradICPOdometryProvider` require the map
`Pointclouds` to have normals. They also require both arguments to be
`Pointclouds`, not raw tensors or `RGBDImages`. Convert one-frame RGB-D data to
point clouds with its vertex/normal maps before calling a provider. Ensure
both batches have the same length.

Ground truth has the opposite contract: it requires two one-frame
`RGBDImages`, each with poses, and does not accept `Pointclouds`.

## Shape and frame errors

Check these invariants before a solver call:

- frame colors `(B,L,H,W,3)` and depths `(B,L,H,W,1)` for channels-last;
- intrinsics `(B,1,4,4)` and poses `(B,L,4,4)`;
- provider point tensors `(1,N,3)` internally, with target points and normals
  having the same `N`;
- low-level `initial_transform` exactly `(4,4)`;
- `pc2im_bnhw` exactly `(P,4)` and `torch.int64` for fusion lookup tables;
- `step` live and previous frames have sequence length one;
- point-cloud and frame batch sizes match.

A common mistake is passing `(B,H,W,3)` to `RGBDImages` or `(B,1,4,4)` as a
low-level solver transform. Fix the shape rather than squeezing arbitrary
dimensions, because batch and sequence axes carry different meanings.

The low-level solver's documented `initial_transform=None` fallback is not
safe in the current implementation: validation reads `.ndim` before the
fallback. Pass `torch.eye(4, dtype=points.dtype, device=points.device)`.

## Empty or unstable correspondences

An empty map is valid only for the first SLAM step. For later ICP/GradICP
localization, inspect `num_points_per_pointcloud`, valid-depth masks, and map
projection. All-zero depth, zero/degenerate normals, no overlapping view, a
large pose jump, or an overly high `dsratio` can leave too few matches. Reduce
the ratio, use closer frames, improve the initial pose, or use `gt` to validate
fusion independently.

`dist_thresh` filters nearest-neighbor matches. `PointFusion.dist_th` filters
map/frame point agreement and `angle_th` filters normal agreement; these are
separate controls. A warning that no active or similar points were found is a
measurement to record, not a successful identity estimate.

Normal maps computed from a flat or tiny depth image can contain zero vectors
at invalid/edge pixels. Use a positive, mildly varying depth fixture and
exclude invalid points rather than fabricating normals after the solver starts.

## Dtype and device mismatches

All constructor inputs must share a device. Keep RGB-D tensors, point-cloud
attributes, solver transforms, and the SLAM device aligned. The provider
creates its initial identity on the map device; use a consistent floating
point dtype. A CPU smoke does not prove CUDA behavior, and `.to("cuda")` must
not be put in a CPU-only default helper.

When comparing results, move detached copies to CPU only for reporting. Do not
call `.cpu()` on the live graph before a gradient check. If a gradient is
missing, inspect the first tensor operation that loses `requires_grad`; do not
assume map fusion is differentiable because GradICP is designed to preserve
tensor gradients.

## PointFusion map failures

For a non-empty map, fusion requires normals, colors, and features (confidence
counts). Use the first empty-map step to initialize those attributes, or add
all three consistently when constructing a test map. `sigma` must be scalar;
`angle_th` is a degree value and is internally converted to a cosine threshold.
Negative or out-of-range thresholds generate warnings and should be corrected,
not ignored.

If point counts increase unexpectedly, check invalid-depth masking and the
correspondence lookup table. Fusion appends valid-depth points that do not
match; it is not guaranteed to keep the same map cardinality.

## External dataset handoff

A dataset adapter failure is not repaired by changing ICP parameters. Ask for
the local root, sequence names, metadata, color/depth file layout, depth
units, and pose availability. Validate one adapter batch first. TUM/ICL and
ScanNet data may have different frame spacing and pose conventions; use `gt`
only when the supplied poses are authoritative. Never report a dataset run
from a synthetic fixture, and never infer that data was downloaded or bundled
by this skill.

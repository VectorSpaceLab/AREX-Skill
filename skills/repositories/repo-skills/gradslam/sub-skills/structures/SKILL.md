---
name: structures
description: "This sub-skill guides construction, conversion, transformation,
  and safe inspection of gradslam RGB-D and batched point-cloud structures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Structures operating guide

Use this sub-skill when a task must build or manipulate `RGBDImages`, build a
`Pointclouds` object, convert RGB-D frames to points, preserve tensor layout,
or prepare a non-interactive Open3D/Plotly representation. Keep the complete
API details in the linked references:

- [API reference](references/api-reference.md) for signatures, properties, and
  mutation semantics.
- [Data formats](references/data-formats.md) for shape, layout, depth, camera,
  and ragged-batch contracts.
- [Workflows](references/workflows.md) for construction, conversion, and
  device-safe recipes.
- [Troubleshooting](references/troubleshooting.md) for failures and adapter
  limits.
- [Tiny smoke helper](scripts/structures_smoke.py) for a deterministic,
  external-data-free check.

## Route the request

1. Identify whether the input is a sequence of RGB-D frames or an existing
   point cloud. Record `B`, `L`, `H`, `W`, representation (`channels_first` or
   channels-last), device, depth units, and whether poses are available.
2. Normalize image tensors before construction. The RGB-D constructors accept
   PyTorch tensors only; NumPy conversion belongs at an input boundary. RGB
   is not automatically divided by 255 and depth is not rescaled.
3. Choose one representation deliberately. Use channels-last for ordinary
   image inspection, Plotly RGB-D animation, and point-cloud conversion. Use
   channels-first only when the consumer explicitly requires it.
4. Keep all constructor tensors on one device. Do not rely on an implicit
   cross-device copy to repair mixed inputs. Verify the selected destination
   after construction.
5. For visual output, prefer `as_figure=False` first so an adapter can be
   checked without opening a browser or GUI. Call `.show()` or Open3D drawing
   only in an explicitly interactive environment.
6. If the request is an RGB-D-to-point-cloud conversion, select a one-frame
   object (`rgbd[:, frame]`) before calling the helper; it requires `L == 1`.
   Choose filtered ragged output or dense padded output deliberately.
7. Follow [workflows](references/workflows.md) for the concrete recipe and
   [troubleshooting](references/troubleshooting.md) for constructor, cache,
   representation, device, conversion, and adapter errors before expanding a
   fixture or invoking external data.

## Build `RGBDImages`

The constructor is:

```python
RGBDImages(rgb_image, depth_image, intrinsics, poses=None,
           channels_first=False, device=None, *, pixel_pos=None)
```

Supply five-dimensional RGB and depth tensors, a `(B, 1, 4, 4)` intrinsics
batch, and optionally `(B, L, 4, 4)` poses. Channels-last means
`rgb=(B,L,H,W,3)` and `depth=(B,L,H,W,1)`; channels-first means
`rgb=(B,L,3,H,W)` and `depth=(B,L,1,H,W)`. The object reports
`shape == (B,L,H,W)`, exposes `cdim` as `4` or `2`, and preserves the chosen
layout. A missing pose is valid: `poses is None`, `has_poses` is false, and
global maps fall back to copies of local maps.

After construction, inspect `rgb_image`, `depth_image`, `intrinsics`, `poses`,
`valid_depth_mask`, and `has_poses` before deriving geometry. Accessing
`vertex_map`, `normal_map`, `global_vertex_map`, or `global_normal_map` computes
and caches the result. Zero or negative depth is masked to zero in vertex maps;
normal maps are likewise zero at missing-depth pixels. Derived maps are in the
same channel layout as the object.

Use `to_channels_last(copy=False)` or `to_channels_first(copy=False)` for an
out-of-place conversion. These return the same object when already in the
requested layout unless `copy=True`; the underscore forms mutate in place.
Index only batch and sequence dimensions. Integer indexing retains singleton
batch/sequence dimensions, which is useful for downstream conversion.

## Build and manipulate `Pointclouds`

Construct from either a list of ragged `(N_b,3)` tensors or an equally padded
`(B,N,3)` tensor. Optional `normals` and `colors` match point shapes; optional
`features` use `(N_b,C)` or `(B,N,C)` and share `C` across the batch. Attributes
must use the same list-versus-tensor representation as `points`. `Pointclouds()`
is a supported empty object; an empty list of points is not.

Use `points_list` and `points_padded` according to the consumer. List-backed
inputs are padded lazily with zero rows, and `nonpad_mask` plus
`num_points_per_pointcloud` identify real rows. The reverse list properties
remove padded rows. `has_normals`, `has_colors`, and `has_features` are the
presence checks; absent attributes remain `None`, not synthesized zeros.

For safe transformations, prefer out-of-place `+`, `-`, `*`, `/`, `rotate`,
`transform`, or `pinhole_projection`. Use the underscore variants only when
mutation is intended. Offset and scale affect points only; rotation and rigid
transformation affect points and normals; colors and features are unchanged.
Rotations accept `(3,3)` or `(B,3,3)`, transformations `(4,4)` or `(B,4,4)`,
and the batch dimension must match. `pinhole_projection` accepts `(4,4)` or
`(B,4,4)` intrinsics and places projected points on the `z=1` plane.

## Convert RGB-D to point clouds

Call `pointclouds_from_rgbdimages(rgbd, global_coordinates=True,
filter_missing_depths=True)` only for an `RGBDImages` object with `L == 1`.
The conversion selects global or local vertex/normal maps, converts to
channels-last, and returns points, normals, and RGB colors. Filtering removes
pixels whose depth is not positive; disabling it preserves a dense flattened
cloud including zero-filled missing-depth rows. If poses are absent, global
coordinates intentionally equal local coordinates.

## Copy, gradients, and devices

`clone()` makes independent tensor storage. `detach()` makes a cloned object
whose internal tensors do not require gradients. `to(device, copy=False)`,
`.cpu()`, and `.cuda()` transfer internal tensors; `copy=True` forces a new
object when supported. Use `torch.device(...)` when comparing devices and
ensure operands of transforms and `append_points` are on the same device.

Property setters preserve the existing batch/point counts and validate the
relevant shape. Padded setters also require the established device and zero
padding; list setters clone values onto the object's device. Setting a list or
padded representation invalidates the alternate representation in the intended
API. Avoid mutating a returned list tensor in place when the padded cache may
already exist; re-check both representations after structural edits.

## Adapters and verification

- `Pointclouds.open3d(index, include_colors=True, max_num_points=None,
  include_normals=False)` returns an Open3D point cloud. Colors are clamped to
  `[0,1]` and values above one are interpreted as 255-scale colors.
- `Pointclouds.plotly(index, include_colors=True, max_num_points=200000,
  as_figure=True, point_size=2)` returns a Plotly figure or `Scatter3d`.
- `RGBDImages.plotly(index, include_depth=True, as_figure=True,
  ms_per_frame=50)` creates RGB/depth animation frames. Convert to
  channels-last first and do not assume this is a GUI-free display operation.
- Adapter subsampling uses random permutations when a maximum is set; seed
  Torch if reproducibility matters.

Run the bundled helper for a tiny CPU fixture, then add focused assertions for
any requested layout, pose, raggedness, missing-attribute, or adapter case.
Do not replace this check with dataset downloads, notebook execution, GUI
visualization, or a CUDA requirement.

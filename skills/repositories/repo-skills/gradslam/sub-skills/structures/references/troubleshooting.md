# Structures troubleshooting

Use the exception type and the first shape/device mismatch to locate the
failure. These checks are local and do not require a dataset, display, network,
or accelerator.

## `RGBDImages` construction errors

- **`TypeError` for an image, camera, pose, or `pixel_pos`:** the constructor
  accepts PyTorch tensors only. Convert NumPy arrays at the input boundary;
  do not pass a Python list or array directly.
- **`rgb_image should have ndim=5` or the corresponding depth/camera/pose
  error:** add explicit batch and sequence dimensions. The required image
  layouts are `(B,L,H,W,3)`/`(B,L,H,W,1)` or
  `(B,L,3,H,W)`/`(B,L,1,H,W)`. Intrinsics are `(B,1,4,4)`, not `(B,4,4)`;
  poses are `(B,L,4,4)`.
- **Wrong channel or shape message:** `channels_first` is a Python boolean and
  selects channel index `2`; otherwise the channel index is `4`. Permute both
  RGB and depth together, and make sure `H` and `W` are in the same positions.
- **`All inputs must be on same device`:** move RGB, depth, intrinsics, poses,
  and any supplied `pixel_pos` to one device before construction. The
  constructor's `device` argument can choose the internal destination only
  after this initial consistency check.
- **Unexpected geometry units:** the constructor does not divide RGB by 255 or
  convert depth units. Normalize color explicitly and scale depth/intrinsics
  before construction if the producer uses incompatible units.

## Derived-map and pose problems

- **All vertices are zero:** depth validity is `depth > 0`; zero and negative
  depth are masked. Check `valid_depth_mask`, depth scale, and intrinsics. A
  singular or malformed camera matrix will fail during inverse computation or
  produce invalid geometry.
- **Global maps differ unexpectedly:** `poses` apply rotation and translation
  to vertices and rotation only to normals. A missing pose (`poses=None`) is a
  deliberate no-pose state; global maps then clone local maps. Identity poses
  have the same coordinates but preserve `has_poses=True`.
- **Maps have stale values after edits:** assigning `depth_image` or
  `intrinsics` invalidates local and global derived-map caches; assigning
  `poses` invalidates global caches. Prefer the public setters and re-read the
  map after mutation. RGB does not participate in geometry derivation.
- **A supplied pixel grid fails:** `pixel_pos` must match the selected RGB
  layout, ending in three coordinates, with the same batch/sequence/spatial
  dimensions and initial device. Omitting it lets the map computation create a
  matching grid.
- **Normal map looks sparse or zero at boundaries:** normals are finite
  differences of neighboring vertex-map entries and are zero where depth is
  invalid. Check the vertex map before diagnosing normals. Normal direction
  follows the implementation's cross-product order; do not assume a universal
  camera-facing sign.

## Indexing and layout conversion

- **Indexing drops a dimension:** integer batch/sequence indices are converted
  to singleton slices by this API. If using an external tensor index or an
  unsupported tuple, use only batch and sequence dimensions and inspect the
  resulting `(B,L,H,W)` shape.
- **Cached maps no longer match image layout:** use
  `to_channels_last(copy=True)` or `to_channels_first(copy=True)` for an
  independent conversion, or the underscore methods when mutation is intended.
  The conversion permutes cached vertex/normal maps as well as RGB/depth, but
  camera and pose matrices do not change layout.
- **Plotly RGB-D rendering is malformed:** convert to channels-last first.
  `RGBDImages.plotly` indexes image frames as image arrays; channels-first data
  is not an adapter input format. Avoid `include_depth=True` for an all-zero
  depth sequence: the depth scaling path takes a logarithm of its maximum and
  can become non-finite.

## `Pointclouds` validation and representation

- **`Expected ... same type as points`:** every present attribute must be a
  list when points are a list, or a tensor when points are a tensor. A list
  item must be two-dimensional. Points/normals/colors end with three channels;
  features end with a shared `C`.
- **Attribute length/shape error:** normals and colors must exactly match each
  point shape. Feature rows must match point rows and feature width must be
  shared across a list batch. Padded attributes must match `(B,N,...)`.
- **Empty input error:** `Pointclouds()` creates an empty object, but
  `Pointclouds(points=[])` is rejected. Empty objects have length zero and
  return `None` for point/attribute representations; indexing them is invalid.
- **Unexpected padded point count:** list-backed point clouds retain
  `num_points_per_pointcloud`; `points_padded` pads to the largest list count.
  Tensor-backed input is considered fully populated and every batch item has
  `N` points. Use `nonpad_mask`, not zero-coordinate tests, for ragged validity.
- **Padded setter rejects a value:** setters require the same device and the
  established batch/count shape. Every row after each stored count must be
  exactly zero, including for normals, colors, or features. Setters clone the
  value and invalidate the opposite representation.
- **Unexpected mutation or aliasing:** `+`, `-`, `*`, `/`, `rotate`,
  `transform`, and `pinhole_projection` clone first. The underscore methods and
  property setters mutate/update the receiver. `__getitem__` selects batch
  items and is not a point-row selector; selected tensors are not promised to
  be cloned.

## Transform, append, and device errors

- **Rotation/transform shape error:** use `(3,3)` or `(B,3,3)` for rotation and
  `(4,4)` or `(B,4,4)` for rigid transforms. A batched matrix must have the
  same `B` as the point-cloud object. Rotation/transform affects normals too;
  offset/scale do not.
- **Runtime broadcasting/device error in arithmetic:** scalar and broadcastable
  tensor operands are accepted, but incompatible shapes or devices are not.
  Put vector operands on the same device and use a shape compatible with
  `(B,N,3)`.
- **`append_points` rejects inputs:** both objects must be `Pointclouds` on the
  same device, with the same batch size and the same attribute presence. Feature
  widths must match. The method concatenates per-batch rows and updates masks;
  it does not merge an attributed cloud with an unattributed cloud.
- **`to` returns the same object:** this is expected with `copy=False` when the
  requested device already matches. Pass `copy=True` for an independent object.
  `.cuda()` is not a CPU fallback and should only be used after checking CUDA.
  The verified inspection environment is CPU-only, so CUDA behavior requires a
  separate compatible runtime.
- **Autograd unexpectedly remains attached:** use `detach()` rather than
  `clone()` when gradients must be removed. Both are independent copies, but
  `clone()` preserves autograd connectivity.

## Conversion and adapter failures

- **`pointclouds_from_rgbdimages` type/sequence error:** pass an
  `RGBDImages`, not a raw depth tensor, and select a one-frame object such as
  `rgbd[:, 0]`. The helper requires `L == 1` and returns a batch of clouds.
- **Filtered cloud has fewer rows:** filtering removes every non-positive-depth
  pixel. This is expected; use `num_points_per_pointcloud` and compare only
  valid pixels. With filtering disabled, the flattened cloud includes zero
  geometry rows and is tensor-backed.
- **Projection consistency check fails:** use the same intrinsics and coordinate
  convention, and compare projected points to the valid pixel grid. Do not
  treat the homogeneous `z=1` output from `pinhole_projection` as original
  metric depth.
- **Open3D or Plotly import/display error:** adapters depend on their optional
  visualization packages and copy tensors to CPU. Request `open3d(...)` or
  `plotly(..., as_figure=False)` only when that package is installed. These
  calls construct in-memory objects; do not call display methods in a headless
  check. `open3d` colors are normalized to `[0,1]`; Plotly colors are emitted
  in 0--255 form.
- **Adapter output is not reproducible:** when `max_num_points` triggers
  subsampling, the implementation uses `torch.randperm`. Seed Torch before
  calling the adapter if selected indices matter. `max_num_points=None` avoids
  this random branch.
- **Open3D color range looks wrong:** values above one are interpreted as
  255-scale for Open3D; values at or below one are treated as normalized.
  Plotly uses the inverse heuristic and emits uint8 colors. Normalize at the
  input boundary for an unambiguous result.

## Safe local diagnosis

Start with the bundled smoke helper, which constructs a 1-frame CPU fixture
without adapters or external files. Then print only shapes, devices, counts,
and `has_*` flags. Add a focused assertion for the failing branch rather than
running dataset downloads, notebooks, GUI display, GPU paths, or the complete
native suite while isolating a structure issue.

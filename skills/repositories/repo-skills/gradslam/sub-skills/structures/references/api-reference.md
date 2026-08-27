# Structures API reference

This reference records the public structure contracts used by the operating
guide. Shapes use `B` for batch, `L` for sequence length, `H/W` for image
height/width, `N_b` for the point count of cloud `b`, and `C` for feature
width.

## `RGBDImages`

Import from `gradslam` or `gradslam.structures.rgbdimages`.

```python
RGBDImages(
    rgb_image: torch.Tensor,
    depth_image: torch.Tensor,
    intrinsics: torch.Tensor,
    poses: Optional[torch.Tensor] = None,
    channels_first: bool = False,
    device: Union[torch.device, str, None] = None,
    *,
    pixel_pos: Optional[torch.Tensor] = None,
)
```

### Constructor checks

- `rgb_image` and `depth_image` must be tensors with `ndim == 5`.
- `intrinsics` must be a tensor with `ndim == 4` and exact shape
  `(B,1,4,4)`.
- `poses`, when present, must be a tensor with exact shape `(B,L,4,4)`.
- `channels_first` must be a Python `bool`.
- Channels-last RGB/depth are `(B,L,H,W,3)` and `(B,L,H,W,1)`.
- Channels-first RGB/depth are `(B,L,3,H,W)` and `(B,L,1,H,W)`.
- `pixel_pos`, when supplied, follows the RGB layout but ends in three
  coordinates: `(B,L,H,W,3)` or `(B,L,3,H,W)`.
- All non-`None` constructor tensors must begin on one device. `device` then
  selects the internal destination device.

### Core properties and methods

| Member | Result or effect |
|---|---|
| `shape` | Tuple `(B,L,H,W)`, independent of channel layout. |
| `channels_first` | `True` for `(B,L,C,H,W)`, otherwise `False`. |
| `cdim` | `2` when channels-first; `4` when channels-last. |
| `rgb_image` | RGB tensor in the chosen layout. |
| `depth_image` | Single-channel depth tensor in the chosen layout. |
| `intrinsics` | `(B,1,4,4)` camera matrices. |
| `poses` | `(B,L,4,4)` camera poses or `None`. |
| `pixel_pos` | Cached/provided homogeneous pixel positions or `None` until vertex-map computation. |
| `valid_depth_mask` | Bool tensor with the depth shape; true where depth is `> 0`. |
| `has_poses` | Boolean pose-presence check. |
| `vertex_map` | Local camera-frame vertices, shape matching RGB except the RGB channel is three. |
| `global_vertex_map` | Pose-transformed vertices; equals local vertices when poses are absent. |
| `normal_map` | Local finite-difference normals, same layout as vertex map. |
| `global_normal_map` | Normals rotated by pose rotation; equals local normals without poses. |
| `len(rgbd)` | Batch size `B`. |
| `rgbd[index]` | Batch/sequence selection; integer indices retain singleton dimensions. |
| `clone()` | New object with cloned internal tensors and cached tensors cloned when present. |
| `detach()` | New object with internal tensors detached from autograd. |
| `to(device, copy=False)` | Device transfer; returns `self` on the requested device unless a copy is requested. |
| `cpu()` / `cuda()` | Convenience device transfers. |
| `to_channels_last(copy=False)` | Out-of-place layout conversion unless already channels-last and no copy is requested. |
| `to_channels_first(copy=False)` | Out-of-place layout conversion unless already channels-first and no copy is requested. |
| `to_channels_last_()` / `to_channels_first_()` | In-place layout conversion. |
| `plotly(index, include_depth=True, as_figure=True, ms_per_frame=50)` | Plotly RGB/depth frames or a figure for one batch sequence. |

The derived-map properties are lazy. The local vertex map builds a pixel grid
`(x,y,1)`, multiplies by the inverse camera intrinsics, and multiplies by the
depth. Missing depth is zeroed. The normal map uses neighboring vertex
finite differences and normalizes nonzero cross products. Global vertices apply
pose rotation and translation; global normals apply pose rotation only.

Assigning `depth_image` or `intrinsics` invalidates all derived map caches;
assigning `poses` invalidates global map caches. RGB assignment does not change
geometry caches because RGB is not used to derive them. Shape validation is
performed by the setters.

## `Pointclouds`

Import from `gradslam` or `gradslam.structures.pointclouds`.

```python
Pointclouds(
    points: Union[List[torch.Tensor], torch.Tensor, None] = None,
    normals: Union[List[torch.Tensor], torch.Tensor, None] = None,
    colors: Union[List[torch.Tensor], torch.Tensor, None] = None,
    features: Union[List[torch.Tensor], torch.Tensor, None] = None,
    device: Union[torch.device, str, None] = None,
)
```

### Representations and checks

- List representation: `points=[tensor(N_b,3), ...]`, one tensor per batch
  item. Every point tensor is two-dimensional and ends in three coordinates.
- Padded representation: `points` is `(B,N,3)`. Every cloud has `N` points
  and `num_points_per_pointcloud` is filled with `N`.
- Normals and colors must match point shapes exactly.
- Features must be `(N_b,C)` or `(B,N,C)`, match the first point dimension,
  and use one shared `C` across a list batch.
- An attribute must use the same container kind as `points` (list with list,
  tensor with tensor). `None` means that attribute is absent.
- `Pointclouds()` creates an empty object. Passing `points=[]` raises a
  validation error.

### Properties

| Member | Result or effect |
|---|---|
| `len(pointclouds)` | Batch size; zero for an empty object. |
| `has_points`, `has_normals`, `has_colors`, `has_features` | Presence booleans. |
| `num_features` | Feature width, or `0` if features are absent. |
| `num_points_per_pointcloud` | One-dimensional device tensor of length `B`. An empty object carries `[0]`. |
| `points_list` / `normals_list` / `colors_list` / `features_list` | Ragged tensors with padding removed; absent attributes return `None`. |
| `points_padded` / `normals_padded` / `colors_padded` | `(B,max(N_b),3)` zero-padded tensors or `None`. |
| `features_padded` | `(B,max(N_b),C)` zero-padded tensor or `None`. |
| `nonpad_mask` | Bool `(B,max(N_b))` identifying real point rows, or `None` when empty. |
| `equisized` | Whether all list clouds have equal point counts; empty is `None`. |

List-to-padded conversion is lazy. Padded-to-list conversion trims each row
using `num_points_per_pointcloud`; do not treat zero-valued coordinates alone
as the validity test. Padded setters require zeros in all padding rows and keep
batch/point counts unchanged. Setters clone their input onto the object's
device and invalidate the alternate representation as intended by the API.

### Operations

| Call | Contract |
|---|---|
| `offset_(offset)` | In-place point translation; accepts tensor, float, or int. |
| `scale_(scale)` | In-place point scaling; accepts tensor, float, or int. |
| `rotate_(rmat, pre_multiplication=True)` | In-place point and normal rotation; `rmat` is `(3,3)` or `(B,3,3)`. |
| `transform_(transform, pre_multiplication=True)` | In-place rigid transform; matrix is `(4,4)` or `(B,4,4)`. |
| `pinhole_projection_(intrinsics)` | In-place projection with `(4,4)` or `(B,4,4)` intrinsics; projected points are homogenized at `z=1`. |
| `rotate`, `transform`, `pinhole_projection` | Clone then apply the corresponding in-place operation. |
| `+`, `-`, `*`, `/` | Clone then offset/scale/divide points; unsupported operand types raise `NotImplementedError`. |
| `@` | Post-multiplication form of a `(3,3)` rotation or `(4,4)` transform, including batch forms. |
| `append_points(other)` | In-place per-batch concatenation; same device, batch size, and attribute presence are required. |
| `__getitem__` | Batch index, slice, list, integer tensor, or bool tensor; selected tensors are not cloned by the selection contract. |
| `clone()` / `detach()` | Independent copy, or independent copy with autograd detached. |
| `to(device, copy=False)` / `cpu()` / `cuda()` | Transfer all representations and cached tensors. |
| `open3d(index, include_colors=True, max_num_points=None, include_normals=False)` | Open3D point cloud adapter. |
| `plotly(index, include_colors=True, max_num_points=200000, as_figure=True, point_size=2)` | Plotly `Figure` or `Scatter3d` adapter. |

Offset and scale operate on points only. Rotation and rigid transforms also
rotate normals. Colors and features are not geometric vectors and are left
unchanged. Batched matrix shapes must match the point-cloud batch.

## RGB-D conversion helper

Import `pointclouds_from_rgbdimages` from
`gradslam.structures.utils`:

```python
pointclouds_from_rgbdimages(
    rgbdimages,
    *,
    global_coordinates: bool = True,
    filter_missing_depths: bool = True,
) -> Pointclouds
```

The input must be an `RGBDImages` object with sequence length exactly one. The
helper selects local or global maps, uses the valid-depth mask when filtering,
and returns points, normal vectors, and RGB colors. Filtering yields a ragged
list with one row per valid pixel; disabling filtering yields a padded tensor
with every pixel flattened, including zero-filled missing-depth rows.

## Structure utilities

`gradslam.datasets.datautils` contains boundary helpers used by structure
workflows: `normalize_image` divides tensor/array image values by `255`,
`channels_first` converts `(*,H,W,C)` to `(*,C,H,W)`, and
`scale_intrinsics` scales focal lengths and principal points for height/width
ratios. It also contains pose/quaternion conversion helpers.

`gradslam.structures.structutils` contains direct-module helpers
`list_to_padded`, `padded_to_list`, `numpy_to_plotly_image`, and
`img_to_b64str`. The list/padded helpers accept only two-dimensional list items
or three-dimensional padded tensors as documented by their validation errors.

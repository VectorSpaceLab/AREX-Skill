# Structures data formats

Use this page as the shape ledger before constructing a structure. All image,
camera, pose, point, and attribute tensors should normally share dtype and
device unless a downstream operation explicitly handles conversion.

## RGB-D batch layout

Let `B` be the batch size, `L` the sequence length, `H/W` the image dimensions.
`RGBDImages.shape` is always `(B,L,H,W)`.

| Item | Channels-last | Channels-first |
|---|---|---|
| RGB image | `(B,L,H,W,3)` | `(B,L,3,H,W)` |
| Depth image | `(B,L,H,W,1)` | `(B,L,1,H,W)` |
| Intrinsics | `(B,1,4,4)` | `(B,1,4,4)` |
| Poses | `(B,L,4,4)` | `(B,L,4,4)` |
| Pixel positions | `(B,L,H,W,3)` | `(B,L,3,H,W)` |
| Local/global vertices | `(B,L,H,W,3)` | `(B,L,3,H,W)` |
| Local/global normals | `(B,L,H,W,3)` | `(B,L,3,H,W)` |
| Valid-depth mask | `(B,L,H,W,1)` | `(B,L,1,H,W)` |

The `channels_first` flag describes RGB, depth, pixel positions, and derived
maps. It does not change camera or pose shapes. The camera matrix is a
homogeneous four-by-four matrix; its top-left three-by-three block is used for
unprojection and its translation/rotation layout is used by global maps.

Depth validity is `depth > 0`. Invalid pixels are retained as zero entries in
vertex and normal maps until `pointclouds_from_rgbdimages` filters them. The
constructor does not rescale image colors or depth values. Use the units
expected by the intrinsics and the producing dataset.

RGB values can be in `[0,1]` or another numeric range for structure storage.
The Plotly/Open3D adapters infer color scale heuristically: values above about
one are treated as 255-scale, then clamped for the adapter. Normalize at the
input boundary when the source range is known.

## Camera and pose conventions

For a pixel `(x,y)`, the internally generated homogeneous pixel row is
`(x,y,1)`. The local vertex map is obtained by applying the inverse camera
intrinsics and multiplying by depth. A pose applies its three-by-three rotation
and then its three-vector translation to local vertices. The same rotation,
without translation, is used for normals.

A missing pose is not an identity pose tensor: it is represented by `None`.
The global-map implementation deliberately falls back to a clone of each
local map in that case. Preserve this distinction when reporting whether
trajectories are available.

## Point-cloud batch layout

A `Pointclouds` object accepts one of two input representations. Do not mix
representations between `points` and an attribute.

| Item | Ragged list | Padded tensor |
|---|---|---|
| Points | list of `(N_b,3)` | `(B,N,3)` |
| Normals | list of `(N_b,3)` | `(B,N,3)` |
| Colors | list of `(N_b,3)` | `(B,N,3)` |
| Features | list of `(N_b,C)` | `(B,N,C)` |
| Counts | inferred per list element | every count is `N` |
| Padding | not stored | zero rows after each count |
| Validity | list length/shape | `nonpad_mask` |

For a ragged batch, `N` means `max(N_b)`. Conversion to padded storage is
lazy. The padded tensors for normals, colors, and features use zero padding
when those attributes are present. An absent attribute returns `None`; it is
not equivalent to an attribute tensor full of zeros.

`features` can have any positive width `C`, but every list element must use the
same width and its first dimension must equal the corresponding point count.
Colors and normals must have exactly three channels and exactly the point
shape. Point-cloud indexing selects batch items only; it does not select point
rows.

## RGB-D to point-cloud shapes

The conversion helper requires `L == 1` but keeps the batch dimension. With
`filter_missing_depths=True`, each output list item has
`(valid_pixels_b,3)` points, normals, and colors. The counts may differ across
batch items. With filtering disabled, points/normals/colors are flattened to
`(B,H*W,3)` and invalid rows remain zero in geometry maps while colors retain
the corresponding RGB values.

`global_coordinates=True` selects pose-transformed maps. It does not invent
poses; absent poses cause the global and local maps to coincide. Set
`global_coordinates=False` when the consumer needs per-camera coordinates.

## Layout conversion rules

`gradslam.datasets.datautils.channels_first` accepts a NumPy array or tensor
with at least three dimensions and permutes only its final image dimensions:
`(*,H,W,C) -> (*,C,H,W)`. `RGBDImages.to_channels_first` and
`to_channels_last` apply the corresponding permutation to stored RGB-D and
cached map tensors while preserving `B/L` and camera/pose dimensions.

For a generic adapter, convert explicitly and inspect the resulting shape:

```python
rgbd = rgbd.to_channels_last(copy=True)
assert rgbd.rgb_image.shape[-1] == 3
assert rgbd.depth_image.shape[-1] == 1
```

Do not pass a channels-first RGB frame directly to an image adapter that
expects `(H,W,C)`. Point-cloud adapters already operate on `(N,3)` rows and do
not need image layout conversion.

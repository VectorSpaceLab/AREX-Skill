# Interactive local-hints data formats

This reference defines the arrays and coordinate conventions used by the local-hints GUI, notebook-style API, and saved result artifacts.

## Core tensor shapes

Let `Xd` be the working size. The repository default is `Xd=256` through the deprecated-but-active `--load_size` parser option and wrapper constructors.

| Name | Shape | Dtype in typical use | Value convention | Producer/consumer |
| --- | --- | --- | --- | --- |
| `img_rgb` | `Xd x Xd x 3` | `uint8` | RGB in `[0, 255]` | Working image after `load_image` resize or caller-provided `set_image`. |
| `img_lab` | `3 x Xd x Xd` | float | Lab; L roughly `[0, 100]`, ab roughly `[-100, 100]` | `_set_img_lab_`. |
| `img_l` | `1 x Xd x Xd` | float | L channel | Colorization wrappers and visualization helpers. |
| `img_ab` | `2 x Xd x Xd` | float | Ground-truth/source ab channels for loaded image | Image state; not the same as user hints. |
| `input_ab` | `2 x Xd x Xd` | float | User hint ab values, unnormalized, usually zero where mask is zero | Caller or GUI; consumed by `net_forward`. |
| `input_mask` | `1 x Xd x Xd` | bool/float | Binary hint mask; one/true where user hints are present | Caller or GUI; consumed by `net_forward`. |
| `input_ab_mc` | `2 x Xd x Xd` | float | `(input_ab - ab_mean) / ab_norm` | Stored by `ColorizeImageBase.net_forward`. |
| `input_mask_mult` | `1 x Xd x Xd` | float | `input_mask * mask_mult` | Stored by `ColorizeImageBase.net_forward`. |
| `output_ab` | `2 x Xd x Xd` | float | Predicted ab channels | Set by colorization wrappers after successful forward. |
| `output_rgb` | `Xd x Xd x 3` | `uint8` | RGB output | Returned by colorization wrappers and `get_img_forward`. |

Wrapper normalization constants:

| Wrapper | `l_mean` | `l_norm` | `ab_mean` | `ab_norm` | `mask_mult` | `maskcent` behavior |
| --- | --- | --- | --- | --- | --- | --- |
| PyTorch local hints | `50` | `1` | `0` | `1` | `1` | Constructor `maskcent=True` sets `mask_cent=.5`; forward subtracts this from the mask tensor. |
| Caffe local hints | `50` | `1` | `0` | `1` | `110` | No PyTorch mask-centering argument. |

Always provide public `input_mask` as binary `0/1` or boolean before wrapper normalization. Do not pre-multiply masks by `110` for Caffe or pre-center masks for PyTorch; the wrappers own those transformations.

## Image resolution conventions

`load_image(input_path)` stores two versions:

1. `img_rgb_fullres`: the source RGB image, optionally downscaled only if its maximum dimension exceeds `Xfullres_max`.
2. `img_rgb`: an `Xd x Xd` working RGB image.

It also stores full-resolution Lab (`img_l_fullres`, `img_ab_fullres`) and working Lab (`img_l`, `img_ab`). Full-resolution output helpers keep the original L channel and upsample working ab predictions or hints:

- `get_img_fullres()` bilinearly upsamples `output_ab` to the full-resolution L shape.
- `get_input_img_fullres()` bilinearly upsamples `input_ab` to the full-resolution L shape.
- `get_img_mask_fullres()` nearest-neighbor upsamples the mask before rendering it.
- `get_sup_fullres()` nearest-neighbor upsamples user mask and ab values for support visualization.

`set_image(input_image)` does not resize `input_image` to `Xd`; use an already resized `Xd x Xd x 3` RGB array unless the task intentionally controls all later shapes.

## Coordinate conventions

Notebook-style code uses `(h, w)` indexing on the `Xd x Xd` working grid:

```python
input_ab[:, h - p:h + p + 1, w - p:w + p + 1] = np.array([a, b])[:, None, None]
mask[:, h - p:h + p + 1, w - p:w + p + 1] = 1
```

The GUI receives Qt positions as `(x, y)` in a square window. `GUIDraw.scale_point` converts window coordinates to working-grid `(x, y)`, and the source then indexes arrays as `[y, x]`. When translating between GUI descriptions and API code, state clearly whether a coordinate is GUI `(x, y)` or array `(h, w)`.

The GUI centers non-square images in the square drawing pad:

- `win_w` and `win_h` are the displayed image width/height, each rounded to a multiple of 4.
- `dw` and `dh` are the horizontal/vertical margins.
- Clicks outside the displayed image rectangle are rejected.

## Patch and point format

A point edit stores:

- The Qt point location.
- The snapped display color used for model input.
- The original user-selected color used for recent-color display.
- A patch width.
- A monotonically increasing edit counter for recent-color ordering.

`PointEdit.updateInput` writes a filled rectangle into three working-grid images:

- `mask`: filled with `255` in an OpenCV `uint8` image, later converted with `mask > 0.0` and transposed to `1 x Xd x Xd`.
- `im`: filled with the snapped RGB color, converted to Lab, then stored as `im_ab0` with shape `2 x Xd x Xd`.
- `vis_im`: filled with the original user RGB color for visualization; not fed directly to the model.

When creating hints programmatically, prefer direct `input_ab` and binary `mask` tensors rather than emulating the GUI's intermediate RGB mask images.

## Lab and gamut values

`data.lab_gamut` uses the CIE Lab color space and clips through RGB when necessary:

- `rgb2lab_1d([r, g, b])` returns one Lab triplet.
- `lab2rgb_1d([L, a, b])` returns one RGB triplet, clipping to displayable range by default.
- `snap_ab(input_l, input_rgb)` preserves a user color's intended ab as much as possible while forcing the selected pixel lightness `input_l` and staying in RGB gamut.
- `abGrid(gamut_size=110, D=1)` covers integer `a,b` coordinates from `-110` to `110`; the GUI uses `gamut_size=160`, while model distributions use the `-110..110` grid at step `10`.

`abGrid.ab2xy(a, b)` maps to widget coordinates as `x = gamut_size + b`, `y = gamut_size + a`. `xy2ab(x, y)` reverses that mapping.

## Distribution and recommendation formats

Distribution wrappers maintain both flat and grid views:

| Name | Shape | Meaning |
| --- | --- | --- |
| `pts_grid` | `529 x 2` | Full `23 x 23` grid of ab points from `-110` to `110` step `10`. |
| `in_hull` | `529` bool | Caffe masks 313 valid in-gamut bins into the full grid; PyTorch wrapper sets all 529 bins true. |
| `dist_ab` | `313 x Xd x Xd` for Caffe, `529 x Xd x Xd` for PyTorch | Distribution produced by the backend-specific model. |
| `dist_ab_full` | `529 x Xd x Xd` | Full-grid distribution after applying `in_hull`. |
| `dist_ab_grid` | `23 x 23 x Xd x Xd` | Grid view for plotting or debugging. |
| `dist_entropy` | `Xd x Xd` | Stored entropy map after `compute_entropy()`. |

`get_ab_reccs(h, w, K=5, N=25000, return_conf=False)` returns either:

- `cluster_centers`: shape `K x 2`, sorted by sampled cluster occupancy, or
- `(cluster_centers, cluster_per)` when `return_conf=True`, where `cluster_per` has shape `K` and sums to approximately `1` across returned clusters.

The helper samples from the distribution at one pixel. It requires a prior distribution `net_forward`; otherwise it prints a warning and returns `0`.

## Saved result directory schema

A GUI save creates a timestamped result directory containing:

```text
im_l.npy
im_ab.npy
im_mask.npy
input_mask.png
ours.png
ours_fullres.png
input_fullres.png
input.png
input_ab.png
```

Array contracts:

- `im_l.npy`: working L channel, `1 x Xd x Xd`.
- `im_ab.npy`: exact user ab hints, `2 x Xd x Xd`.
- `im_mask.npy`: exact user mask, `1 x Xd x Xd`.

Image contracts:

- `input_mask.png`: mask visualization, 0/255 after transpose to image layout.
- `ours.png`: working-resolution model result.
- `ours_fullres.png`: full-resolution output from working ab predictions and full-resolution L.
- `input_fullres.png`: full-resolution user hint visualization.
- `input.png`: working-resolution user hint visualization.
- `input_ab.png`: support visualization using `50 * input_mask` as L and user ab as chroma.

OpenCV writes PNGs in BGR order internally; callers reading with OpenCV should convert to RGB before comparing or displaying with RGB-based libraries.

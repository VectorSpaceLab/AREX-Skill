# Data and format guide

keras-vis 0.5.0 was written for standalone Keras 2.x and supports both backend image data formats. The utility layer tries to let agents reason in one canonical shape order while still using the active Keras backend layout.

## Canonical shape language

Use this vocabulary in instructions and checks:

- Canonical keras-vis utility order: `(samples, channels, image_dims...)`.
- `channels_first` tensor order: `(samples, channels, image_dims...)`.
- `channels_last` tensor order: `(samples, image_dims..., channels)`.
- Display image order for Pillow, plotting, stitching, and most RGB/BGR helpers: `(height, width, channels)`.

`get_img_shape` converts the active tensor layout into canonical utility order. It does not transpose the data; it only reports the shape.

| Active Keras format | Input example | `get_img_shape` result |
|---|---:|---:|
| `channels_first` | `(2, 3, 5, 7)` | `(2, 3, 5, 7)` |
| `channels_last` | `(2, 5, 7, 3)` | `(2, 3, 5, 7)` |
| `channels_first` 3D image | `(2, 3, 4, 5, 6)` | `(2, 3, 4, 5, 6)` |
| `channels_last` 3D image | `(2, 4, 5, 6, 3)` | `(2, 3, 4, 5, 6)` |

For tensors, static Keras shape inspection can include `None`; do not treat `None` as an integer size.

## Safe data-format handling pattern

When diagnostic code needs to switch data formats, preserve the caller's setting:

```python
from keras import backend as K

old_format = K.image_data_format()
try:
    K.set_image_data_format('channels_last')
    # run the targeted shape check
finally:
    K.set_image_data_format(old_format)
```

This matters because Keras backend image format is global process state in the legacy stack.

## `slicer` behavior

Write slices in canonical channels-first order, including a samples position and a channels/filter position:

```python
from vis.utils import utils

# Canonical intent: all samples, one channel/filter, all remaining dimensions.
canonical_slice = utils.slicer[:, filter_idx, ...]
```

The helper returns:

- unchanged slice when `K.image_data_format() == 'channels_first'`;
- the same slice with item 1 moved to the end when `K.image_data_format() == 'channels_last'`.

Examples:

| Canonical slice | Active format | Actual slice |
|---|---|---|
| `[:, 4, :, :]` | `channels_first` | `[:, 4, :, :]` |
| `[:, 4, :, :]` | `channels_last` | `[:, :, :, 4]` |
| `[:, 4, ...]` | `channels_first` | `[:, 4, ...]` |
| `[:, 4, ...]` | `channels_last` | `[:, ..., 4]` |

If an agent omits the sample axis or channel axis, `slicer` will still move the second item; that can silently target the wrong dimension. Always define slices as `(samples, channels, spatial...)`.

## Channels-first tensors versus HWC display images

Not all image utilities obey Keras tensor data format:

- `get_img_shape` and `slicer` are data-format aware.
- `overlay` only checks equal shapes; it does not know which axis is channels.
- `stitch_images`, `draw_text`, and Pillow/scikit-image display workflows expect channels-last HWC images.
- `bgr2rgb` reverses the last axis, so it assumes the color axis is last.
- `load_img` returns an image array from scikit-image, normally channels-last for color images.

Use explicit transposes at the boundary between model tensors and display images. Common conversions:

```python
# One channels-first model tensor sample to HWC display image.
display = sample_chw.transpose(1, 2, 0)

# One HWC display image to channels-first batch input.
batch = display.transpose(2, 0, 1)[None, ...]

# One HWC display image to channels-last batch input.
batch = display[None, ...]
```

## Overlay and heatmap preparation

The low-level `overlay` helper requires same-shaped arrays. It does not resize heatmaps, apply colormaps, infer alpha masks, or validate semantic alignment. Prepare overlays in this order:

1. Produce or receive the map from the visualization workflow.
2. Resize/crop it to the display image height and width if needed.
3. Convert a 2D heatmap to three display channels if blending with RGB/BGR images.
4. Normalize or scale both arrays intentionally.
5. Call `overlay(array1, array2, alpha=...)` with `0 <= alpha <= 1`.

Route decisions about which class/filter/layer a heatmap represents to the visualization sub-skills; this guide only covers array compatibility.

## Label lookup data

`lookup_imagenet_labels` loads `imagenet_class_index.json` from keras-vis package data at runtime. The table has 1000 entries keyed by stringified indices and stores `[wordnet_id, class_name]`. The helper returns only class names and always returns a list.

Use it only for models whose final output indices follow the standard ImageNet ordering. For custom classifiers, use the project's own label mapping instead of this helper.

## Optional image packages

The base keras-vis install depends on scikit-image and matplotlib. Extra image utilities may need optional packages:

- Pillow: required by `draw_text`; also required during `GifGenerator.callback` because GIF frames are annotated with `draw_text`.
- imageio: required when constructing `GifGenerator` writers.

The optional extra declared by the package is named `vis_utils` and includes Pillow plus imageio. Missing optional packages should be handled as diagnosable environment issues, not as visualization algorithm errors.

## Deterministic synthetic checks

For reproducible utility checks, use synthetic arrays instead of sample assets:

```python
import numpy as np
from vis.utils import utils
from vis.visualization import overlay

x = np.array([-2.0, 0.0, 2.0], dtype='float32')
scaled = utils.normalize(x, min_value=-1.0, max_value=1.0)

img = np.zeros((4, 4, 3), dtype='uint8')
heat = np.full((4, 4, 3), 255, dtype='uint8')
blend = overlay(heat, img, alpha=0.25)
```

The bundled `scripts/check_image_utilities.py` runs these kinds of checks and reports the active Keras backend data-format behavior.

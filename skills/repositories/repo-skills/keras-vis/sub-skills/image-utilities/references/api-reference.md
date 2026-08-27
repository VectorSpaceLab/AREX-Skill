# Image utilities API reference

This reference covers keras-vis 0.5.0 image/data helpers that are useful outside the high-level visualization wrappers. The legacy stack uses standalone Keras 2.x backend state; examples should preserve and restore `keras.backend.image_data_format()` when they temporarily change it.

Primary imports:

```python
from vis.utils import utils
from vis.visualization import overlay
```

## Helper summary

| Helper | Import | Signature | Behavior | Important constraints |
|---|---|---|---|---|
| `get_img_shape` | `utils.get_img_shape` | `get_img_shape(img)` | Returns image shape normalized to `(samples, channels, image_dims...)` for numpy arrays or Keras tensors. | Uses static `K.int_shape` for tensors, so dimensions may be `None`. For `channels_last`, moves the last channel axis to position 1. |
| `slicer` | `utils.slicer` | `utils.slicer[:, filter_idx, ...]` | Converts a slice authored in canonical channels-first order into the active backend layout. | Include both sample and channel positions in the slice. In `channels_last`, the second slice item is moved to the end. |
| `overlay` | `overlay` from `vis.visualization` | `overlay(array1, array2, alpha=0.5)` | Alpha-blends two numpy arrays and casts the result to `array1.dtype`. | `alpha` must be in `[0, 1]`; arrays must have identical shapes. This is a low-level array blend, not a Grad-CAM semantic step. |
| `load_img` | `utils.load_img` | `load_img(path, grayscale=False, target_size=None)` | Reads an image with scikit-image and optionally resizes it, preserving value range and casting resized output to `uint8`. | Requires readable local file. `target_size` is passed directly to scikit-image resize as the output shape; verify row/column order for your data. |
| `draw_text` | `utils.draw_text` | `draw_text(img, text, position=(10, 10), font='FreeSans.ttf', font_size=14, color=(0, 0, 0))` | Returns a copy-like numpy array with text drawn through Pillow. Falls back to Pillow default font when the requested system font is unavailable. | Requires Pillow. Expects display-style image arrays that Pillow can convert, typically `uint8` HWC. |
| `stitch_images` | `utils.stitch_images` | `stitch_images(images, margin=5, cols=5)` | Places same-shaped 3D images into a grid with black margins. Returns `None` for an empty input list. | Each image must be shaped `(height, width, channels)`. Mixed shapes or grayscale 2D arrays are not handled. |
| `lookup_imagenet_labels` | `utils.lookup_imagenet_labels` | `lookup_imagenet_labels(indices)` | Returns ImageNet class names for integer or list-like output indices using package data. | Returns names only, not WordNet ids. Invalid indices raise key errors. Needs packaged `imagenet_class_index.json`. |
| `find_layer_idx` | `utils.find_layer_idx` | `find_layer_idx(model, layer_name)` | Returns the integer index of a Keras layer with an exact `layer.name` match. | Raises `ValueError` when no exact name exists. Inspect `model.layers` names before calling. |
| `apply_modifications` | `utils.apply_modifications` | `apply_modifications(model, custom_objects=None)` | Saves and reloads a Keras model so activation edits or similar layer changes rebuild the graph. | Returns a new model; assign it. Requires HDF5 serialization support and `custom_objects` for custom layers/losses. |
| `bgr2rgb` | `utils.bgr2rgb` | `bgr2rgb(img)` | Reverses the last axis with `img[..., ::-1]`. | Correct for channels-last RGB/BGR images. Do not use directly on channels-first tensors unless the last axis is actually color. |
| `normalize` | `utils.normalize` | `normalize(array, min_value=0., max_value=1.)` | Linearly rescales a numpy array into the requested numeric range. | Constant arrays map to `min_value`; NaN/Inf values propagate. |
| `random_array` | `utils.random_array` | `random_array(shape, mean=128., std=20.)` | Creates a random array, normalizes it to roughly zero mean/unit variance, then applies requested mean/std. | Uses global numpy randomness; set `numpy.random.seed` for reproducible diagnostics. |
| `listify` | `utils.listify` | `listify(value)` | Leaves lists unchanged; wraps any non-list as a one-item list. | Tuples and strings are wrapped, not expanded or split. |
| `add_defaults_to_kwargs` | `utils.add_defaults_to_kwargs` | `add_defaults_to_kwargs(defaults, **kwargs)` | Copies defaults and overlays explicit keyword arguments. | Shallow merge only; explicit kwargs win. |

## Data-format helpers

### `get_img_shape`

`get_img_shape` reports shape in one canonical order regardless of backend:

```python
from keras import backend as K
from vis.utils import utils

K.set_image_data_format('channels_first')
utils.get_img_shape(np.zeros((2, 3, 5, 7)))  # (2, 3, 5, 7)

K.set_image_data_format('channels_last')
utils.get_img_shape(np.zeros((2, 5, 7, 3)))   # (2, 3, 5, 7)
```

For N-dimensional images, the same rule applies: `channels_last` moves the final channel axis immediately after samples and preserves the spatial axes after that.

### `slicer`

Author the slice as if the tensor is `(samples, channels, image_dims...)`. The helper returns the correct slice for the active data format.

```python
# Intended canonical slice: all samples, one filter/channel, all spatial positions.
canonical = utils.slicer[:, filter_idx, ...]
value = layer_output[canonical]
```

Under `channels_first`, the slice is unchanged. Under `channels_last`, the channel slice is moved to the final position. This is why keras-vis losses can write one slice for both TensorFlow-style and Theano-style image layouts.

## Image array helpers

### `overlay`

Use `overlay` only after both arrays already have the same shape and compatible scale. A common safe pattern is to normalize or colorize a heatmap to the same HWC shape as the display image, then blend:

```python
blended = overlay(display_image.astype('float32'), heatmap_rgb.astype('float32'), alpha=0.4)
```

The result dtype is cast to the dtype of the first array. If using integer arrays, clipping and scale choices should be handled before blending.

### `stitch_images`

`stitch_images` assumes every image has exactly the same `(height, width, channels)` shape. The output width is `cols * width + (cols - 1) * margin`; the output height is computed from the number of rows required. Margins are black zeros with the first image dtype.

### `bgr2rgb`

`bgr2rgb` flips the last axis. That is appropriate for ordinary display images shaped `(height, width, 3)`. For channels-first model input shaped `(samples, 3, height, width)`, convert channels explicitly with `array[:, ::-1, ...]` instead of `bgr2rgb`.

### `normalize`

`normalize` computes `(array - min) / (max - min + epsilon)` and maps to the requested range. Because an epsilon is added, maximum values may be fractionally below `max_value`; compare with tolerances in tests.

## Loading, labels, and annotations

### `load_img`

`load_img` is a small scikit-image wrapper, not the modern `keras.preprocessing.image.load_img` API. It returns a numpy array. If `target_size` is provided, the resized array is cast to `uint8`; without resizing, dtype follows the scikit-image reader.

### `lookup_imagenet_labels`

The lookup table contains 1000 ImageNet entries indexed by final dense output id. Examples: index `0` maps to `tench`, index `20` maps to `water_ouzel`, and index `999` maps to `toilet_tissue`. Pass a scalar or list; the return value is always a list of names.

### `draw_text`

`draw_text` converts the numpy array through Pillow, draws text, and returns `np.asarray(img)`. If the requested font cannot be found in system fonts, it logs a warning and uses Pillow's default font. For GIF generation through keras-vis callbacks, Pillow is also needed because frames are annotated with `draw_text`.

## Model helpers

### `find_layer_idx`

Use this helper when high-level visualization wrappers need an integer layer index. It compares exact layer names:

```python
layer_idx = utils.find_layer_idx(model, 'predictions')
```

For generated or nested models, layer names may include suffixes such as `_1`; list names first and choose the exact value.

### `apply_modifications`

Keras 2.x does not rebuild the graph merely because code changes a layer attribute such as `layer.activation`. After editing layer attributes, call:

```python
model = utils.apply_modifications(model, custom_objects=custom_objects)
```

The helper serializes and reloads the model, so the returned object must replace the old model reference. Custom layers, lambdas, metrics, or losses may require `custom_objects` or may not be serializable in this legacy HDF5 path.

## Small generic helpers

- `listify` is useful for filter/class indices because keras-vis APIs often accept either a scalar or list. It does not expand tuples.
- `add_defaults_to_kwargs` is used by high-level wrappers to combine default optimizer parameters with caller overrides. It is a shallow dictionary merge.
- `random_array` is the default synthetic seed generator used by optimizer code when no seed input is provided. Seed numpy explicitly for deterministic tests.

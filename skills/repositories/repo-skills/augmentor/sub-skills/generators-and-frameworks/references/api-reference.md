# Generator and framework API reference

## Quick signature map

| API | Signature | Data source | Returns | Required non-framework dependencies |
| --- | --- | --- | --- | --- |
| Directory generator | `Pipeline.keras_generator(batch_size, scaled=True, image_data_format="channels_last")` | `Pipeline.augmentor_images` populated from disk | Infinite generator yielding `(X, y)` | Pillow, NumPy |
| Array generator | `Pipeline.keras_generator_from_array(images, labels, batch_size, scaled=True, image_data_format="channels_last")` | User-supplied NumPy-like arrays and labels | Infinite generator yielding `(X, y)` | Pillow, NumPy |
| Keras preprocessing callable | `Pipeline.keras_preprocess_func()` | One already-scaled image array at a time | Callable returning a PIL image | Pillow, NumPy |
| Torch-style transform | `Pipeline.torch_transform()` | One PIL image at a time | Callable returning a PIL image | Pillow, NumPy |
| DataFrame source pipeline | `DataFramePipeline(source_dataframe, image_col, category_col, output_directory="output", save_format=None)` | pandas DataFrame of image paths and categories | A `Pipeline` subclass | pandas, Pillow, NumPy |

## `Pipeline.keras_generator(...)`

```python
g = p.keras_generator(
    batch_size,
    scaled=True,
    image_data_format="channels_last",
)
X, y = next(g)
```

### Parameters

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `batch_size` | Number of images and labels yielded per `next(...)`. | Use the downstream model's batch size. Must be positive in normal use. |
| `scaled` | Whether to cast image data to `float32` and divide by `255`. | Keep `True` for many neural-network training loops; set `False` for raw pixel inspection or custom normalization. |
| `image_data_format` | Output channel layout. Accepts `"channels_last"` or `"channels_first"`. | Match the downstream framework/model configuration. Other values only produce a warning, not a reliable conversion. |

### Output contract

| Source images | `image_data_format` | `X` shape | `y` shape |
| --- | --- | --- | --- |
| RGB, uniform height/width | `channels_last` | `(batch_size, height, width, 3)` | `(batch_size, num_classes)` for categorical pipeline labels, or list-like for one class |
| RGB, uniform height/width | `channels_first` | `(batch_size, 3, height, width)` | same label behavior |
| Greyscale | `channels_last` | `(batch_size, height, width, 1)` | same label behavior |
| Greyscale | `channels_first` | `(batch_size, 1, height, width)` | same label behavior |

Important behavior:

- The generator yields forever and samples with replacement.
- It executes the current pipeline operations without saving augmented outputs to disk.
- Label values come from the pipeline's scanned classes.
- All images in a batch must be compatible with one NumPy array shape. If source images have mixed dimensions, add a resize/crop operation or normalize inputs before generator use.

## `Pipeline.keras_generator_from_array(...)`

```python
g = p.keras_generator_from_array(
    images,
    labels,
    batch_size,
    scaled=True,
    image_data_format="channels_last",
)
X, y = next(g)
```

### Parameters

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `images` | Array-like image collection. | Use `(n, height, width)` or `(n, height, width, 1)` for greyscale; use `(n, height, width, channels)` for RGB/RGBA-like images. |
| `labels` | Label collection aligned with `images`. | `len(labels)` must equal `len(images)`. Labels are sampled by the same random index as the image. |
| `batch_size` | Number of samples per yielded batch. | The generator samples with replacement, so `batch_size` may exceed `len(images)`. |
| `scaled` | Whether to cast to `float32` and divide by `255`. | Use `False` if a later preprocessing stage performs normalization. |
| `image_data_format` | Output channel layout. | Match the downstream consumer: `channels_last` or `channels_first`. |

### Output contract

| Input shape | `image_data_format` | Output `X` shape |
| --- | --- | --- |
| `(n, height, width)` | `channels_last` | `(batch_size, height, width, 1)` |
| `(n, height, width)` | `channels_first` | `(batch_size, 1, height, width)` |
| `(n, height, width, 1)` | `channels_last` | `(batch_size, height, width, 1)` |
| `(n, height, width, channels)` | `channels_last` | `(batch_size, height, width, channels)` |
| `(n, height, width, channels)` | `channels_first` | `(batch_size, channels, height, width)` |

Important behavior:

- Raises `IndexError("The number of images does not match the number of labels.")` when labels are not aligned.
- Converts each selected array to PIL-compatible shape, applies operations, converts back to NumPy, and then formats channels.
- The code path is independent of Keras/TensorFlow; the name describes a Keras-compatible generator contract.

## `Pipeline.keras_preprocess_func()`

```python
preprocess = p.keras_preprocess_func()
output_pil = preprocess(image_array)
```

Contract:

- Returns a callable.
- Input should be an image array already scaled to `[0, 1]`.
- The callable multiplies by `255`, casts to `uint8`, converts to a PIL image, applies operations according to probability, and returns a PIL image.
- If a downstream framework expects NumPy output, ensure that framework path converts the PIL result appropriately.

## `Pipeline.torch_transform()`

```python
transform = p.torch_transform()
output_pil = transform(input_pil)
```

Contract:

- Returns a callable.
- Input is a PIL image.
- Output is a PIL image.
- Each configured operation is applied according to its probability.
- torch/torchvision are not imported. torchvision is only needed if the user wants `torchvision.transforms.Compose` or tensor conversion.

## `DataFramePipeline(...)`

```python
p = Augmentor.DataFramePipeline(
    source_dataframe=df,
    image_col="path",
    category_col="category",
    output_directory="output",
    save_format=None,
)
```

### Parameters

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `source_dataframe` | pandas DataFrame containing image paths and category values. | Paths should point to readable image files. |
| `image_col` | Column name containing image paths. | Use absolute paths or paths valid from the current process working directory. |
| `category_col` | Column name containing class/category labels. | Values are converted to a pandas categorical series for class labels. |
| `output_directory` | Output directory for generated samples. | Inherited from `Pipeline`; used when saving outputs. |
| `save_format` | Optional save format override. | Same behavior as ordinary `Pipeline` save format handling. |

### Compatibility status

This surface is optional and legacy-sensitive. The scanner calls a pandas categorical method named `get_values()`, which is not present in pandas 1.5.3 or pandas 3.0.5. When this occurs, initialization raises an `AttributeError` before a usable pipeline is populated.

Safe recommendations:

- Prefer ordinary directory-backed `Pipeline` when the DataFrame only maps paths to classes that can be expressed as folders.
- Prefer `DataPipeline` when arrays are already in memory or grouped with masks.
- If the user maintains the package, patch the DataFrame scanner to use a modern categorical accessor and then prove it with a tiny generated-image DataFrame.
- If the user cannot patch, pin pandas only after proving that the exact chosen pandas version provides the expected categorical method.

## Channel-layout decision table

| Downstream expectation | Use | Symptom if wrong |
| --- | --- | --- |
| TensorFlow/Keras default image convention | `image_data_format="channels_last"` | Model may complain about receiving `(batch, channels, height, width)` instead of `(batch, height, width, channels)`. |
| Older Keras or framework config using channel-first tensors | `image_data_format="channels_first"` | Model may see the channel count as a spatial dimension. |
| PIL-only transform path | `torch_transform()` or `keras_preprocess_func()` return path | No batch layout applies until later tensor conversion. |

## Scaling decision table

| User need | Setting | Consequence |
| --- | --- | --- |
| Neural-network input expects floats in `[0, 1]` | `scaled=True` | `X` becomes `float32` and values are divided by `255`. |
| Model or preprocessing layer performs its own normalization | `scaled=False` | `X` remains unnormalized pixel values. |
| Debugging image conversion through PIL | Either, but inspect dtype/range | Convert scaled arrays back with `(X * 255).astype("uint8")` before PIL display. |

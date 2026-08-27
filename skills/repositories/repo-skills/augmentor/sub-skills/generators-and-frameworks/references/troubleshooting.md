# Generator and framework troubleshooting

## Shape mismatch in model input

Symptoms:

- The model reports an unexpected channel dimension.
- A `channels_first` model receives `(batch, height, width, channels)`.
- A `channels_last` model receives `(batch, channels, height, width)`.

Fix:

1. Confirm the downstream model's expected layout.
2. For TensorFlow/Keras default image data format, use:

   ```python
   g = p.keras_generator(batch_size=32, image_data_format="channels_last")
   ```

3. For channel-first configuration, use:

   ```python
   g = p.keras_generator(batch_size=32, image_data_format="channels_first")
   ```

4. Print one batch before training:

   ```python
   X, y = next(g)
   print(X.shape, X.dtype, y.shape)
   ```

If source images have mixed sizes, normalize them first with a resize/crop operation or ensure the dataset is already uniform. A generator batch must become one NumPy array.

## `scaled=True` changed dtype or range

`scaled=True` casts the image batch to `float32` and divides by `255`, producing values in `[0, 1]` for ordinary 8-bit images.

Use `scaled=True` when the model expects normalized float inputs. Use `scaled=False` when a downstream preprocessing layer or custom code performs normalization.

Debug snippet:

```python
X, y = next(g)
print(X.dtype, float(X.min()), float(X.max()))
```

## `keras_generator_from_array` labels do not align

Symptom:

```text
IndexError: The number of images does not match the number of labels.
```

Fix:

```python
assert len(images) == len(labels)
g = p.keras_generator_from_array(images, labels, batch_size=16)
```

The array generator samples an image index and returns the label at the same index. If labels are one-hot arrays, class IDs, strings, or metadata objects, keep the first dimension aligned with `images`.

## User thinks Keras/TensorFlow must be installed for generator APIs

No Keras/TensorFlow install is needed to call:

- `p.keras_generator(...)`
- `p.keras_generator_from_array(...)`
- `p.keras_preprocess_func()`

These surfaces produce Python generators/callables using Augmentor, Pillow, and NumPy. Keras/TensorFlow is needed only if the user's surrounding training loop imports and uses it.

Recommended response:

1. Prove direct output with the bundled smoke helper.
2. Inspect `X.shape`, `X.dtype`, `y.shape`, and scaling.
3. Then connect the generator to the framework training call.

## `torch_transform()` without torch/torchvision

`p.torch_transform()` returns a callable and does not import torch or torchvision.

You can validate it with only PIL and Augmentor:

```python
transform = p.torch_transform()
output_pil = transform(input_pil)
```

torch/torchvision is optional and user-provided for composition and tensor conversion:

```python
transforms = torchvision.transforms.Compose([
    p.torch_transform(),
    torchvision.transforms.ToTensor(),
])
```

If torchvision is unavailable, keep the Augmentor transform as a PIL callable or install the framework dependency in the user's training environment.

## pandas missing for `DataFramePipeline`

Symptom:

```text
ImportError: Pandas is required to use the scan_dataframe function!
```

Fix options:

- Install pandas only if the user truly needs `DataFramePipeline`.
- Prefer ordinary `Pipeline` for directory-backed image folders.
- Prefer `DataPipeline` for in-memory arrays or mask groups.

## pandas `Categorical.get_values` failure

Symptom:

```text
AttributeError: 'Categorical' object has no attribute 'get_values'
```

Cause:

`DataFramePipeline` uses a legacy pandas categorical method that is absent in pandas 1.5.3 and pandas 3.0.5. The failure happens while scanning the DataFrame, before the pipeline can populate image records.

Fix options:

1. Use ordinary `Pipeline` if images can be arranged in folders.
2. Use `DataPipeline` if images are already arrays or grouped with masks.
3. If maintaining the package, edit the DataFrame scanner to use a modern categorical accessor in place of `Categorical.get_values()` and run a tiny DataFrame smoke check.
4. If pinning pandas, prove the exact pinned version first; do not assume all `pandas<2` releases work.

The bundled smoke helper can exercise this path without crashing:

```bash
python scripts/augmentor_generator_smoke.py --check-dataframe
```

Use `--require-dataframe` only when the environment must fail hard if DataFramePipeline is unavailable.

## Preprocessing callable returns PIL, not a batch array

`keras_preprocess_func()` converts one scaled array into a PIL image, applies pipeline operations, and returns the PIL image.

If the surrounding framework expects a NumPy array from the preprocessing function, add an explicit conversion in the integration path or choose `keras_generator(...)` / `keras_generator_from_array(...)` instead.

## Generator appears endless

This is expected. Both Keras-style generator APIs are infinite generators and sample with replacement. Use `next(g)` for one batch, or pass the generator into a training loop that controls `steps_per_epoch`.

## Empty or invalid source images

For `keras_generator`, the source `Pipeline` must have scanned at least one valid image. If no images are found, solve the disk pipeline layout first. Route class-folder scanning, output directory behavior, and basic disk sampling to the pipeline augmentation sub-skill.

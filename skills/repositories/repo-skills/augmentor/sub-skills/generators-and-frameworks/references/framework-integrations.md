# Framework integration recipes

This reference covers Augmentor surfaces that bridge into training frameworks without making those frameworks required Augmentor dependencies.

## Optional dependency boundaries

| Surface | Augmentor dependency | Optional user dependency | Key boundary |
| --- | --- | --- | --- |
| `Pipeline.keras_generator(...)` | Augmentor + Pillow + NumPy | Keras/TensorFlow only if a training loop consumes the generator | Direct `next(generator)` calls do not import Keras or TensorFlow. |
| `Pipeline.keras_generator_from_array(...)` | Augmentor + Pillow + NumPy | Keras/TensorFlow only if a training loop consumes the generator | The array generator is a Python generator over supplied arrays and labels. |
| `Pipeline.keras_preprocess_func()` | Augmentor + Pillow + NumPy | Keras/TensorFlow only for `ImageDataGenerator` or equivalent | The returned callable expects already scaled array input and returns a PIL image after applying operations. |
| `Pipeline.torch_transform()` | Augmentor + Pillow + NumPy | torch/torchvision only for framework `Compose`/tensor conversion | The returned callable accepts and returns a PIL image and can be tested without importing torchvision. |
| `DataFramePipeline(...)` | Augmentor + Pillow + NumPy | pandas | Legacy pandas API usage can fail; see the DataFrame section below. |

## Directory-backed Keras-style generator

Use `keras_generator` when images already live in a directory-backed `Pipeline` and the downstream model can consume `(images, labels)` batches indefinitely.

```python
import Augmentor

p = Augmentor.Pipeline("training_images")
p.rotate(probability=0.7, max_left_rotation=5, max_right_rotation=5)
p.flip_left_right(probability=0.5)

g = p.keras_generator(
    batch_size=32,
    scaled=True,
    image_data_format="channels_last",
)

images, labels = next(g)
```

Operating notes:

- The generator samples with replacement and yields forever.
- `images` is a NumPy array. With RGB images and `channels_last`, expect `(batch_size, height, width, 3)` when all source images have the same size.
- With `channels_first`, expect `(batch_size, 3, height, width)` for RGB images.
- `labels` comes from the pipeline's class scan. A single flat image directory yields one class; class subdirectories yield one-hot categorical labels.
- `scaled=True` returns `float32` values in `[0, 1]`. Use `scaled=False` if the model pipeline expects raw pixel values.
- This call does not import Keras/TensorFlow. Those frameworks are only needed around the consumer training code.

## Array-backed Keras-style generator

Use `keras_generator_from_array` when the images are already in memory.

```python
import numpy as np
import Augmentor

images = np.zeros((100, 28, 28, 1), dtype="uint8")
labels = np.arange(100) % 10

p = Augmentor.Pipeline()
p.rotate(probability=0.3, max_left_rotation=5, max_right_rotation=5)

g = p.keras_generator_from_array(
    images=images,
    labels=labels,
    batch_size=16,
    scaled=True,
    image_data_format="channels_last",
)

batch_images, batch_labels = next(g)
```

Input and output rules:

- `len(images)` must equal `len(labels)`.
- Greyscale input can be `(n, height, width)` or `(n, height, width, 1)`.
- RGB/RGBA-like input should be `(n, height, width, channels)`.
- For `channels_last`, output uses `(batch_size, height, width, channels)`.
- For `channels_first`, output uses `(batch_size, channels, height, width)`.
- The generator samples with replacement from the supplied arrays.
- The generator applies the pipeline's operations through PIL conversion; choose operations compatible with the image mode/channel layout.

## Keras preprocessing callable

Use `keras_preprocess_func()` when the framework already provides batches and you want Augmentor operations as a preprocessing callback.

```python
import Augmentor

p = Augmentor.Pipeline()
p.rotate(probability=0.7, max_left_rotation=10, max_right_rotation=10)
p.zoom(probability=0.5, min_factor=1.1, max_factor=1.5)

preprocess = p.keras_preprocess_func()
```

If you use a framework image generator, pass `preprocess` as that framework's preprocessing function. The callable expects image array values already scaled to `[0, 1]`. Internally, it converts the array with `Image.fromarray(np.uint8(255 * image))`, applies Augmentor operations, and returns a PIL image.

Do not use this callable when the downstream framework expects a NumPy array after preprocessing unless the surrounding framework path converts the PIL result as needed.

## Torch-style transform callable

Use `torch_transform()` when a pipeline should behave like a PIL-image transform.

```python
import Augmentor

p = Augmentor.Pipeline()
p.greyscale(probability=1.0)
p.rotate_random_90(probability=1.0)

augmentor_transform = p.torch_transform()
augmented_pil_image = augmentor_transform(pil_image)
```

For torchvision composition, the user supplies torchvision:

```python
transforms = torchvision.transforms.Compose([
    p.torch_transform(),
    torchvision.transforms.ToTensor(),
])
```

Operating notes:

- `torch_transform()` itself does not import torch or torchvision.
- The returned callable accepts a PIL image, applies each Augmentor operation according to its probability, and returns a PIL image.
- Add tensor conversion after the Augmentor callable when the framework needs tensors.
- Operation details and parameter choices belong in the operation reference sub-skill.

## DataFramePipeline

`DataFramePipeline(source_dataframe, image_col, category_col, output_directory="output", save_format=None)` builds a disk-backed pipeline from a pandas DataFrame that contains image paths and class/category labels.

```python
import pandas as pd
import Augmentor

df = pd.DataFrame({
    "path": ["/data/cat_001.jpg", "/data/dog_001.jpg"],
    "category": ["cat", "dog"],
})

p = Augmentor.DataFramePipeline(
    source_dataframe=df,
    image_col="path",
    category_col="category",
    output_directory="output",
)
```

Compatibility boundary:

- pandas is optional and is imported only for the DataFrame scanner.
- This Augmentor version uses `pd.Categorical(...).get_values()` in its DataFrame scanner.
- That method is absent in pandas 1.5.3 and pandas 3.0.5, so `DataFramePipeline` can raise `AttributeError: 'Categorical' object has no attribute 'get_values'` even when pandas is installed.
- Prefer ordinary `Pipeline` for disk folders or `DataPipeline` for in-memory grouped arrays when possible.
- If maintaining the package, patch the scanner to use a modern categorical value accessor; if operating an existing environment, pin to a truly compatible old pandas version only after proving it with a small smoke check.

## Suggested integration order

1. First prove direct Augmentor behavior with the bundled smoke helper.
2. Confirm generator output shape and dtype before connecting to a model.
3. Connect to Keras/TensorFlow or torch/torchvision only after the direct generator/callable output is correct.
4. Keep `DataFramePipeline` optional and fall back to ordinary `Pipeline` or `DataPipeline` if pandas compatibility fails.

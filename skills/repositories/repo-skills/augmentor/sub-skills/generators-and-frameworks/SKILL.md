---
name: generators-and-frameworks
description: "Use Augmentor generator APIs, array generators, framework
  preprocessing callables, torch-style transforms, and DataFramePipeline
  boundaries without making optional ML frameworks required."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Generators and framework integrations

Use this sub-skill when a task asks for Augmentor data generators, in-memory array batches, Keras/TensorFlow-style training integration, PyTorch/torchvision-style transforms, or DataFrame-backed image sources.

## Route here for

- `Pipeline.keras_generator(batch_size, scaled=True, image_data_format="channels_last")` from a directory-backed pipeline.
- `Pipeline.keras_generator_from_array(images, labels, batch_size, scaled=True, image_data_format="channels_last")` from NumPy-like image arrays.
- `Pipeline.keras_preprocess_func()` for a Keras `ImageDataGenerator` preprocessing callable.
- `Pipeline.torch_transform()` for a callable that can be placed in a torchvision transform composition.
- `DataFramePipeline(source_dataframe, image_col, category_col, output_directory="output", save_format=None)` and its pandas compatibility boundary.

## Route away

- For basic disk-backed `Pipeline(...)`, `sample(...)`, output directories, class-folder scanning, or save formats, use the `pipeline-augmentation` sub-skill.
- For `DataPipeline` in-memory grouped images/masks and mask-safe array augmentation, use the `masks-and-arrays` sub-skill.
- For operation selection, parameter ranges, custom operations, and validation errors, use the `operation-reference` sub-skill.

## Required operating facts

- Direct Augmentor generator methods are plain Python generator/callable surfaces; `keras_generator`, `keras_generator_from_array`, `keras_preprocess_func`, and `torch_transform` do **not** import Keras, TensorFlow, torch, or torchvision by themselves.
- Keras/TensorFlow and torch/torchvision are optional downstream framework dependencies only when the user actually trains a model or composes framework transforms.
- Framework training examples were reference evidence only. Use the distilled recipes in this skill; do not depend on notebooks or external datasets.
- `scaled=True` converts image batches to `float32` and divides pixel values by `255`. `scaled=False` keeps unscaled image array values.
- Choose `image_data_format="channels_last"` for `(batch, height, width, channels)` and `"channels_first"` for `(batch, channels, height, width)`.
- `keras_generator_from_array` requires `len(images) == len(labels)` and raises `IndexError` if they differ.
- `DataFramePipeline` requires pandas, but this repository version calls `Categorical.get_values()`, which is missing in pandas 1.5.3 and 3.0.5. Treat DataFramePipeline as an optional legacy surface unless the user pins/patches it.

## Bundled references and helper

- [Framework integration recipes](references/framework-integrations.md) covers Keras-style generators, preprocessing callbacks, torch-style transforms, and optional dependency boundaries.
- [API reference](references/api-reference.md) lists signatures, shape contracts, label behavior, scaling, and DataFramePipeline semantics.
- [Troubleshooting](references/troubleshooting.md) covers shape mismatches, scaling surprises, missing optional dependencies, DataFramePipeline pandas failures, and labels issues.
- [Generator smoke helper](scripts/augmentor_generator_smoke.py) creates tiny synthetic images and arrays, exercises direct generator calls without Keras/TensorFlow, exercises `torch_transform()` without torchvision, and optionally checks DataFramePipeline.

## Minimal decision checklist

1. Identify the data source: disk pipeline, NumPy arrays, Keras preprocessing array stream, torch-style PIL transform, or pandas DataFrame.
2. Pick the batch layout that matches the downstream model: `channels_last` or `channels_first`.
3. Decide whether the model expects scaled float data (`scaled=True`) or raw pixel values (`scaled=False`).
4. If pandas is requested, warn about the known `Categorical.get_values()` issue and prefer ordinary `Pipeline`/`DataPipeline`, pinning/patching, or maintaining a patched `scan_dataframe`.
5. Run the bundled smoke helper in the target environment before integrating with a training loop.

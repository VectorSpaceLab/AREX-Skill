# Vision and generative troubleshooting

## Read mode is wrong

**Symptom**: Libra cannot find classes, image paths, or train/test folders.

**Fix**:
- Run `scripts/inspect_image_dataset.py` first.
- Pass `read_mode="setwise"`, `"classwise"`, or `"csvwise"` explicitly when automatic detection is ambiguous.
- For CSV-wise layouts, pass `image_column` when multiple string columns resemble paths.

## CSV image column cannot be located

**Symptom**: `Could not locate column containing image information.`

**Fix**:
- Ensure CSV values resolve to real files from the training working directory.
- Pass `image_column="..."` explicitly.
- Prefer filenames or paths relative to the data root.

## Pretrained model rejects the size

**Symptom**: `For pretrained models, both 'height' and 'width' must be 224.`

**Fix**: use `height=224, width=224` or remove ImageNet pretrained weights.

## `custom_arch` with preprocessing fails

**Symptom**: `If 'custom_arch' is not None, 'preprocess' must be set to false.`

**Fix**: preprocess the image folders first, then call `convolutional_query(preprocess=False, custom_arch="...")`.

## TFJS/JAX/TensorFlow import errors

TensorFlowJS is imported at module import time. Use the root compatibility reference for the verified `tensorflow==2.15.1`, `tensorflowjs==4.22.0`, and JAX pin guidance. Do not leave `tensorflowjs` unpinned.

## TensorFlow does not see a GPU

Use:

```python
import tensorflow as tf
print(tf.config.list_physical_devices('GPU'))
```

If the result is empty, run tiny CPU checks only and do not claim GPU verification.

## Feature-map visualization fails

`show_feature_map=True` assumes the trained CNN has convolutional layers and that the test generator has at least one image batch. Turn it off for layout smoke checks.

## GAN writes files unexpectedly

`gan_query` preprocesses into `proc_training_set` and writes generated images under `generated_images` relative to the data path. Work on a copy if the input folder is valuable.

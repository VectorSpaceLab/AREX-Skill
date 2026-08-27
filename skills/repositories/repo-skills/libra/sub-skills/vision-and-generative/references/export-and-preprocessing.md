# Export and preprocessing details

## Read-mode decision table

| Data shape | Suggested `read_mode` | Notes |
|---|---|---|
| `training_set/` and `testing_set/` class folders | `setwise` | Use when splits already exist. |
| root contains one folder per class | `classwise` | Libra creates `proc_training_set` and `proc_testing_set`. |
| CSV maps image paths to labels | `csvwise` | Pass `image_column` if path detection is ambiguous. |
| preprocessed Keras folders already exist and no resizing/splitting is desired | `preprocess=False` | Required for `custom_arch`. |

## Preprocessing side effects
- `new_folders=True` creates `proc_training_set` and `proc_testing_set`.
- `new_folders=False` can replace resized images in place.
- CSV-wise preprocessing creates processed train/test folders near the CSV/data path.
- Median image height/width are used when `height`/`width` are omitted.

## Pretrained constraints
With `pretrained={'weights': 'imagenet'}`, Libra enforces `height == 224` and `width == 224`.

## Custom architecture constraints
`custom_arch` loads a Keras JSON architecture. The source refuses `custom_arch` when `preprocess=True`; prepare Keras train/test folders first and call with `preprocess=False`.

## Export outputs
- `save_as_tfjs=True` writes a `tfjsmodel` directory.
- `save_as_tflite=True` writes `model.tflite`.
- Both are written in the current working directory in the inspected implementation.

Use a temporary working directory if you do not want these files next to user data.

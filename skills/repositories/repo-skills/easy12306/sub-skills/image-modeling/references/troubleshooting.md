# Image Modeling Troubleshooting

## Purpose

Use this when validating or retraining the easy12306 image-tile classifier fails.
The table favors observable symptoms, likely causes, and safe recovery steps
that are self-contained in this generated sub-skill.

## Quick triage

1. Run `python scripts/inspect_image_training_assets.py --help` to confirm the
   bundled checker interface.
2. Run the checker against the user's `.npz`, labels, and optional model files.
3. If the checker passes but training still fails, check the Keras/TensorFlow
   compatibility row below before debugging data.
4. Treat full training as expensive and possibly network-dependent because VGG16
   ImageNet weights may be downloaded.

## Failure modes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` mentioning `keras.preprocessing.image.ImageDataGenerator` | Keras 3 or another incompatible standalone Keras package is installed. | Use a Python 3.11 environment with Keras/TensorFlow 2.15-compatible APIs for the legacy workflow, or port the augmentation call to a modern Keras/preprocessing path before training. Do not treat a Keras 3 import failure as a data error. |
| `captcha.npz` is missing `images` or `labels` | The user supplied the wrong archive or a partially generated dataset. | Re-run or route to data-preparation for dataset construction. For modeling, require a `.npz` with both arrays. |
| Checker reports `images` is not 4D or final channel is not 3 | Dataset contains grayscale images, flattened arrays, full captchas instead of tiles, or an unexpected channel order. | Regenerate or reshape data so image tiles are `(N, H, W, 3)`. Confirm BGR OpenCV ordering before applying the model recipe. |
| Checker reports label length mismatch | Images and labels came from different dataset versions or filtering steps. | Rebuild the paired arrays together; do not train after truncating one side unless the user explicitly approves a reproducible pairing rule. |
| Sparse labels outside `[0, 79]` | Label vocabulary mismatch or one-based indexing. | Inspect the labels file; class ids must be zero-based row indexes into the 80-row vocabulary. Convert only with a documented mapping. |
| Vote-matrix labels have zero or negative row sums | Empty vote rows, corrupt probabilities, or unsupported target encoding. | Repair or drop invalid rows before training. The legacy sample-weight formula divides by `sqrt(row_sum)` and cannot handle non-positive sums. |
| Sample weights include `nan`, `inf`, or extreme values | Vote matrix has invalid numeric values or nearly empty rows. | Use the checker summary to identify suspicious rows; normalize/repair the vote matrix or switch to sparse labels with a deliberate weighting policy. |
| Validation accuracy is nonsensical after training | RGB/BGR preprocessing mismatch, label vocabulary mismatch, or wrong `.npz` split. | Preserve OpenCV BGR order and subtract means `[103.939, 116.779, 123.68]`; verify the 80-row label file used during training and inference is identical. |
| Training tries to access the network | `VGG16(weights="imagenet")` needs ImageNet weights not already cached. | Ask for network permission, provide a local cache/weights plan, or change the recipe to a user-approved initialization strategy. Record the change in the model handoff. |
| Training is too slow or exhausts memory | VGG16 plus 400 epochs and 100 steps per epoch is large for a smoke check. | Do not use full training for verification. Use the bundled checker and, if needed, a user-approved reduced synthetic experiment clearly marked as non-equivalent to full training. |
| Existing `12306.image.model.h5` path fails the checker | File is missing, path points to a directory, or the artifact has not been supplied. | Ask the user to provide the model artifact or train one. The checker verifies existence only unless `--load-model` is requested. |
| `--load-model` fails with Keras errors | Model was saved with a different Keras/TensorFlow version, custom object issue, or incompatible HDF5 stack. | First verify that the file exists without `--load-model`; then load in a compatible Keras/TensorFlow 2.15 environment. If still failing, request the producing environment/version or re-export the model. |
| Prediction class ids do not match Chinese labels | `texts.txt` differs from the vocabulary used to train the model. | Use the exact 80-row label file from training; the image model outputs class ids, not label strings. |

## BGR preprocessing checks

The image classifier expects OpenCV BGR input. If a user supplies images loaded
with PIL or another RGB-first library, convert to BGR or retrain consistently.
The mean subtraction order is:

```python
[103.939, 116.779, 123.68]  # B, G, R
```

A common failure is applying RGB VGG-style means to BGR arrays, which can produce
plausible shapes but poor predictions.

## When to stop and ask the user

Stop before proceeding when:

- full training would require downloading ImageNet weights and network access is
  not already approved;
- external `.npz`, `.h5`, or labels artifacts are absent and cannot be
  synthesized for the user's actual task;
- the user wants to mutate a shared environment to downgrade from Keras 3 to a
  Keras/TensorFlow 2.15-compatible stack;
- labels cannot be reconciled with the 80-row vocabulary.

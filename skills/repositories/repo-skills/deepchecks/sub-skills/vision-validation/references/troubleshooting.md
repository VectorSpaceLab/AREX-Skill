# Vision Troubleshooting

Use this page when VisionData construction or a suite run fails before you get useful results.

## Torch or torchvision is missing

**Symptom**

- Importing `deepchecks.vision` fails immediately.
- The error mentions PyTorch or torchvision.

**Likely cause**

- The vision extra or a compatible torch/torchvision build is not installed.

**Fix**

- Install the vision dependencies before trying to build `VisionData`.
- If you need GPU execution, install a CUDA-enabled torch build separately; this sub-skill itself only assumes CPU-capable validation.

## Image validation errors

**Symptoms**

- `The image inside the iterable must be a 3D array.`
- `The image inside the iterable must have 1 or 3 channels.`
- `Image data should be in uint8 format(integers between 0 and 255)...`

**Likely cause**

- Images are still CHW instead of HWC.
- Images are floating point or normalized.
- The batch contains constant arrays such as all-zero or all-one images.

**Fix**

- Convert each image to HWC.
- Convert or clip values back into uint8 `0..255`.
- Make sure the images are not constant; the bundled smoke script uses small non-constant uint8 fixtures for this reason.

## Loader shuffle warnings

**Symptoms**

- A warning says shuffling is not supported for the received batch loader.
- A TensorFlow warning says the dataset should already be shuffled.

**Likely cause**

- The loader is a custom iterable or TensorFlow dataset.
- `reshuffle_data=True` was used where Deepchecks cannot reshuffle automatically.

**Fix**

- Shuffle upstream before wrapping the loader.
- Set `reshuffle_data=False` for custom iterables and TensorFlow datasets.
- For PyTorch DataLoader objects, prefer the built-in reshuffle support when the loader is recognized.

## One-shot generator lost the first batch

**Symptom**

- A loader seems to work once, then later iterations are missing data.

**Likely cause**

- A one-shot generator object was passed directly into `VisionData`.
- `VisionData` validates the first batch immediately, so the first batch can be consumed during construction.

**Fix**

- Wrap the batches in a re-iterable object whose `__iter__` returns a fresh iterator.
- Use a DataLoader or TensorFlow dataset when possible.

## Classification label or probability mismatch

**Symptoms**

- `Classification label per image must be a number.`
- `Classification prediction per image must be a sequence of floats representing probabilities per class.`
- `Number of entries in proba does not match number of classes in label_map`

**Likely cause**

- Labels are strings or vectors instead of single class ids.
- Predictions are logits or unnormalized scores.
- The `label_map` length does not match the probability vector length.

**Fix**

- Use one class id per sample for labels.
- Convert logits to probabilities and keep the vector length equal to the class count.
- Make sure `label_map` has one entry per predicted class.

## Detection or segmentation shape mismatch

**Symptoms**

- `Object detection label per image must be a sequence of 2D arrays, where each row has 5 columns...`
- `Object detection prediction per image must be a sequence of 2D arrays, where each row has 6 columns...`
- `Semantic segmentation label per image must be a 2D array of shape (H, W)...`
- `Semantic segmentation prediction per image must be a 3D array of shape (C, H, W)...`

**Likely cause**

- The batch still uses model-native formats rather than Deepchecks formats.
- Boxes, masks, or class channels were not reshaped correctly.

**Fix**

- Normalize the output to the shapes listed above before yielding the batch.
- For segmentation, softmax logits across the class/channel axis.
- For detection, keep the confidence score in the fifth column and the class id in the sixth column of each prediction row.

## Custom property output type errors

**Symptom**

- A property list fails validation.

**Likely cause**

- The property dict is missing `name`, `method`, or `output_type`.
- The property uses legacy wording such as `continuous` or `discrete`.

**Fix**

- Use `numerical`, `categorical`, or `class_id` for `output_type`.
- Make sure the method returns one item per input sample.

## Directory helper errors

**Symptoms**

- The class-per-folder helper says the path does not exist or the folder is empty.
- No images are found even though the folder is populated.

**Likely cause**

- The folder layout does not match the expected classification structure.
- The image extension argument does not match the actual file suffix.

**Fix**

- Use `root/class_name/*.jpg` or `root/train/class_name/*.jpg` plus `root/test/class_name/*.jpg`.
- Check the `image_extension` value.

## Optional CUDA

**Symptom**

- GPU hardware is visible, but the current torch build reports CUDA unavailable.

**Likely cause**

- The installed torch build is CPU-only.

**Fix**

- Keep using the CPU path for this sub-skill.
- Only install a CUDA-enabled torch build when you specifically need GPU-backed model execution or GPU-only backend verification.
- Do not treat visible GPUs as a requirement for VisionData validation.

## When to route elsewhere

- Save/show/serialize/export or CI gating → use the sibling `results-and-integrations` skill.
- Tabular `Dataset` debugging → use `tabular-validation`.
- NLP `TextData` debugging → use `nlp-validation`.

## Good first sanity check

If you are unsure whether the data is valid, run the smoke helper first and inspect the printed batch summary before running a suite.

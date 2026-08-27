# Troubleshooting

## Purpose

Use this for predictable preprocessing, sampler, and loader failures.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Some names in your transform were not found` | A tuple-key transform references labels that do not exist in the sample. | Check the dataset keys and rename the transform key to match them exactly. |
| Loader warning about `images_per_batch` | The requested batch size is larger than the dataset. | Let the loader clip it, or choose a smaller batch size. |
| Shape mismatch after `Loader` iteration | Channel expansion or sampler geometry does not match the model input. | Inspect `channels_first`, the sampler axis, and the expected model input shape. |
| `SliceSampler` gives wrong orientation | The axis argument does not match the dimension you intended to slice. | Set the axis explicitly and confirm the output shape from a tiny batch. |
| `PatchSampler` / `BlockSampler` returns empty or broken batches | The crop size or stride is larger than the image extent. | Resample the data first or choose a smaller patch/block. |
| `RandomCrop` behaves unexpectedly on mixed-size inputs | The first image shape drives the crop indices. | Use consistent image sizes before random cropping. |
| `Loader.to_keras()` fails to import TensorFlow | The Keras/TensorFlow stack was not installed. | Install `tensorflow==2.17.0` and `tf-keras==2.17.0`, then rerun the smoke helper. |
| `Loader.to_keras()` fails to infer a signature | The loader could not produce a representative sample. | Verify the dataset path and make sure the loader can emit at least one batch. |

## Recovery steps

1. Start with a deterministic transform such as `Resample` or `RangeNormalize`.
2. Confirm one sample before adding the loader.
3. Add a sampler only after the transformed image shape is stable.
4. Use `channels_first=None` if automatic channel expansion is hiding the real
   data shape.
5. Run the bundled smoke helper when the problem might be packaging-related.

## Good signals

- One sample and one batch both have the shapes you expect.
- Paired input/output transforms stay aligned.
- `Loader.to_keras()` returns a batch that Keras can consume without shape
  surprises.

## Hand off when

- the real problem is model construction or trainer defaults;
- the user wants prediction output reconstruction;
- the issue is actually a dataset-reader problem rather than preprocessing.

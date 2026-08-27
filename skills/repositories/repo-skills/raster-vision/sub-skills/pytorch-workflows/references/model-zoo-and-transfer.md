# Model zoo and transfer

## What the model zoo gives you

- A ready-made `model-bundle.zip` for prediction.
- The trained weights plus the config needed to reconstruct the preprocessing and model shape.
- Example outputs that show how the bundle should behave on sample imagery.
- A lightweight path to fine-tuning because many bundles also expose a `model.pth` file once unzipped.

## Example bundle map

| Bundle key | Task | Model family | Transfer note |
| --- | --- | --- | --- |
| `spacenet-rio-cc` | Chip classification | ResNet 50 | Good starter for classification transfer learning. |
| `spacenet-vegas-buildings-ss` | Semantic segmentation | DeepLabV3 / ResNet50 | Good starter for building segmentation transfer learning. |
| `spacenet-vegas-roads-ss` | Semantic segmentation | DeepLabV3 / ResNet50 | Good starter for road segmentation transfer learning. |
| `isprs-potsdam-ss` | Semantic segmentation | Panoptic FPN / ResNet50 | Good starter for multiband segmentation transfer learning. |
| `cowc-potsdam-od` | Object detection | Faster R-CNN / ResNet18 | Good starter for detection transfer learning with an external-detector example nearby. |
| `xview-od` | Object detection | Faster R-CNN / ResNet50 | Good starter for vehicle detection transfer learning. |

## Prediction flow

1. Use a model bundle from the bundle directory or the model zoo.
2. Run a single-scene prediction against the target image.
3. Inspect the raster output and any vector outputs that the task writes.
4. If the imagery bands or statistics differ from training, override the prediction-side band handling rather than editing the weights.

## Fine-tuning checklist

- Point `ModelConfig.init_weights` at the saved `train/last-model.pth` from a prior run, or at `model.pth` from an unzipped bundle.
- Keep `num_classes` aligned with the downstream class list.
- Keep `img_channels` and `channel_order` aligned with the data source.
- Use `load_strict=False` only when the head shape or task-specific output shape must change.
- If you switch from a built-in backbone to an external module, keep the external repo, entrypoint, and version pinned to the tested combination.
- If the bundle came from a different imagery distribution, expect to retune the sampler and the learning rate before trusting the transfer.

## Cautions

- Bundles are most reliable when the new imagery is close to the training imagery in band order, resolution, and sensor characteristics.
- A model trained for one city often will not transfer well to a very different city without retraining.
- Object-detection external modules must behave like torchvision-style detectors, including `boxes`, `labels`, and `scores` in prediction output.

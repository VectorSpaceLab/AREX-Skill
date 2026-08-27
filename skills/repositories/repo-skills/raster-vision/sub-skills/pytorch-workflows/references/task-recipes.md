# Task recipes

## Data mode cheat sheet

| Situation | Use | Notes |
| --- | --- | --- |
| Scenes already exist and you want Raster Vision to sample chips on the fly | `*GeoDataConfig` | Set `nochip=True`, plus `scene_dataset` and `sampling`. |
| Chips already exist on disk | `*ImageDataConfig` | Use the pre-chipped data layout and skip scene-time sampling. |
| Remote rasters should be streamed | `RasterioSourceConfig(allow_streaming=True)` | Useful for HTTP/S3 reading when local copies are unnecessary. |
| Multiband imagery or extra channels | Set `img_channels`, `channel_order`, and `plot_options.channel_display_groups` together | Keep model inputs, visualization, and stats aligned. |
| Fine-tuning from a saved Raster Vision run | `ModelConfig.init_weights` | Point at `train/last-model.pth` or a bundled `model.pth`. |

## Solver and model checklist

- Keep `backbone` and task family aligned with the example defaults unless you have a reason to change them.
- Use `pretrained=False` for smoke tests or external-module comparisons.
- Use `external_def` only when the example or downstream task needs a model that is not built in.
- Use `external_loss_def` only when the solver should own a custom loss implementation.
- Avoid combining `external_loss_def` with solver options that Raster Vision forbids, such as `class_loss_weights` or `ignore_class_index`.
- Revisit `num_classes`, `img_channels`, `channel_order`, and `load_strict` whenever the class set or band count changes.

## Smoke test: `tiny_spacenet`

- This is the minimal semantic-segmentation sanity check.
- It uses one training scene, one validation scene, `SemanticSegmentationGeoDataConfig`, `Backbone.resnet50`, and a one-epoch `SolverConfig`.
- It is the fastest way to verify that the environment can train, bundle, and predict before moving to larger examples.
- Treat it as the quickstart path when you only need a confidence check rather than a full dataset workflow.

## Chip classification: SpaceNet Rio

- Use `PyTorchChipClassificationConfig`.
- Default the data path to `ClassificationGeoDataConfig` when `nochip=True`.
- Switch to `ClassificationImageDataConfig` when chips were already materialized or when direct scene sampling is not what you want.
- The built-in model path is `ClassificationModelConfig(backbone=Backbone.resnet50)`.
- `external_model=True` switches to the EfficientNet example path.
- `external_loss=True` switches to the focal-loss example path.
- `test=True` reduces the example to a smaller crop and fewer epochs.
- Inspect `train/dataloaders/`, `train/log.csv`, `train/valid_preds.png`, `eval/validation_scenes/eval.json`, and `bundle/model-bundle.zip` after a run.

## Semantic segmentation: SpaceNet Vegas and ISPRS Potsdam

- Use `PyTorchSemanticSegmentationConfig`.
- The SpaceNet Vegas examples show the cleanest `target=buildings|roads` split and do not need a `processed_uri`.
- The ISPRS Potsdam example adds `multiband`, `augment`, `allow_streaming`, and `external_model` options.
- Use `SemanticSegmentationGeoDataConfig` for direct scene reads and `SemanticSegmentationImageDataConfig` when you already have chips.
- Keep `channel_display_groups` in sync with the band order whenever the imagery is not plain RGB.
- When you need polygon outputs as well as raster predictions, use `SemanticSegmentationLabelStoreConfig` with `vector_output`.

## Object detection: COWC Potsdam and xView

- Use `PyTorchObjectDetectionConfig`.
- `ObjectDetectionGeoDataConfig` is the direct-scene path; `ObjectDetectionImageDataConfig` is the chip path.
- `ObjectDetectionWindowSamplingConfig` controls random crop sampling, negative ratio, IoA thresholds, and the number of windows.
- The COWC example shows the external-detector path.
- The xView example shows the built-in Faster R-CNN path with notebook-generated processed labels.
- Use `multiband=True` when the scene data includes the extra IR band and you want to keep all channels.

## After a run

- Check `train/dataloaders/*.png` to confirm the sampled chips or scene crops look right.
- Check `train/log.csv` and TensorBoard output for learning behavior.
- Check `train/valid_preds.png` for qualitative validation output.
- Check `eval/validation_scenes/eval.json` for the metric summary.
- Check `bundle/model-bundle.zip` before predicting on new imagery.
- Check `predict/<scene>/labels.tif` and `predict/vector_outputs/` for the final inference products.

## When the choice is unclear

- Use the bundled command printer to render the known example commands without executing them.
- If the issue is actually CLI syntax or runner behavior, hand off to the `pipeline-cli` sub-skill.
- If the issue is about raster, vector, or scene objects, hand off to `data-and-models`.

# PyTorch Learner and GeoDataset API

This reference covers the library-side dataset and learner layer used for geospatial ML.

## Two main entry points

- **Prechipped data**: use `ImageDataConfig` subclasses.
- **Scene-backed data**: use `GeoDataConfig` subclasses with `SceneConfig` objects and `WindowSamplingConfig`.

## GeoDataset hierarchy

### Base shape

- `GeoDataset` is a PyTorch-compatible dataset that samples directly from a `Scene`.
- `SlidingWindowGeoDataset` reads deterministic windows with `size`, `stride`, and optional padding.
- `RandomWindowGeoDataset` samples windows stochastically with `size_lims` or `h_lims` / `w_lims`.
- `ImageDataset` is the non-geospatial base for file-backed image datasets.

### Task-specific `from_uris` helpers

The task-specific subclasses expose convenient constructors that assemble the scene for you:

- `SemanticSegmentationSlidingWindowGeoDataset.from_uris(...)`
  - `image_uri`
  - `label_raster_uri` or `label_vector_uri`
  - `class_config`
  - `aoi_uri`
  - `label_vector_default_class_id`
  - `image_raster_source_kw`, `label_raster_source_kw`, `label_vector_source_kw`

- `ClassificationSlidingWindowGeoDataset.from_uris(...)`
  - `image_uri`
  - `label_vector_uri`
  - `class_config`
  - `aoi_uri`
  - `label_vector_default_class_id`
  - `image_raster_source_kw`, `label_vector_source_kw`, `label_source_kw`

- `ObjectDetectionSlidingWindowGeoDataset.from_uris(...)`
  - same pattern as classification, plus object-detection sampling options on the random-window variant

### GeoDataset gotchas

- `within_aoi=True` keeps windows fully inside AOIs.
- `return_window=True` adds the sampled `Box` to the returned tuple.
- `RandomWindowGeoDataset` can fail to sample if the window limits are incompatible with the scene extent or AOI.
- `ObjectDetectionRandomWindowGeoDataset` negative sampling requires at least one bbox in the scene/AOI.
- Albumentations-based transforms usually expect `uint8`; use a raster transformer if the imagery needs normalization first.

## DataConfig and GeoDataConfig

### `ImageDataConfig`

Use this for file-structured or zipped prechipped datasets.
Supported layouts include:
- a directory containing `train/`, `valid/`, and optional `test/`
- a zip containing that layout
- a list of zips
- a directory of zips

Task-specific layouts:
- classification: class folders under each split
- semantic segmentation: `img/` and `labels/` under each split
- object detection: COCO-style `labels.json` plus an `img/` directory

### `GeoDataConfig`

Use this for scene-backed training and evaluation.

Key behaviors:
- `scene_dataset` supplies the `SceneConfig` objects.
- `sampling` controls window generation.
- `class_config` can be inferred from `scene_dataset.class_config` when omitted.
- `build(..., for_chipping=True)` keeps chips as raw arrays for chipping workflows.

### Sampling rules

`WindowSamplingConfig` enforces a few important constraints:
- `method=sliding` uses `size` as the default `stride` when none is set.
- `method=random` requires either `size_lims` or both `h_lims` and `w_lims`.
- `size_lims` and `h_lims` / `w_lims` are mutually exclusive.

## Learner lifecycle

### Build and reuse

- `LearnerConfig` builds a task-specific `Learner` subclass.
- `Learner.from_model_bundle(model_bundle_uri, ...)` loads the serialized config and weights from a bundle.
- `Learner.save_model_bundle()` writes weights, config, and custom transform definitions for reuse.
- `Learner.predict_dataset()` iterates over predictions from a PyTorch dataset.

### Prediction helpers

`Learner.predict_dataset()` supports:
- `return_format='z'`, `'yz'`, or `'xyz'`
- `raw_out` for probability vs class output
- `numpy_out=True` for numpy conversion

### Model bundle note

`ScenePredictor` and `Predictor` in the core package work on top of a model bundle. `Learner.from_model_bundle()` is the learner-side API for loading the same bundle for inference or fine-tuning.

## Learner and model config rules

- `run_tensorboard=True` requires `log_tensorboard=True`.
- `class_loss_weights` must match the number of classes.
- `SemanticSegmentationModelConfig` only accepts DeepLabV3 backbones in the resnet50 / resnet101 family.
- `ObjectDetectionModelConfig` only accepts resnet-family backbones.
- Channel expansion for non-3-channel imagery is only supported for resnet backbones in the default model builders.
- `ExternalModuleConfig` must specify exactly one of `uri` or `github_repo`.

## Practical use order

1. Build a `Scene` or a prechipped image dataset.
2. Wrap it in a `GeoDataset` or `ImageDataset`.
3. Configure a `Learner` or `LearnerConfig`.
4. Train or load a bundle.
5. Predict with `predict_dataset()` or a bundle-backed predictor.

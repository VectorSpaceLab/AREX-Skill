---
name: data-and-models
description: "Guides Raster Vision agents through ClassConfig, SceneConfig,
  DatasetConfig, RasterioSourceConfig, GeoJSONVectorSourceConfig,
  RasterizedSourceConfig, label sources, label stores, AOIs, GeoDataset,
  Learner, Predictor, and ScenePredictor APIs for geospatial ML."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---
# data-and-models

Use this sub-skill when the task is about Raster Vision's programmatic geospatial ML data/model layer:
- assembling or validating `ClassConfig`, `SceneConfig`, or `DatasetConfig`
- wiring `RasterioSourceConfig`, `GeoJSONVectorSourceConfig`, `RasterizedSourceConfig`, label sources, label stores, AOIs, or transformers
- using `GeoDataset`, `Learner`, or model-bundle inference APIs directly from Python

## Route away
- Pipeline CLI orchestration, `rastervision run ...`, or command scheduling -> `pipeline-cli`
- example recipes, backend pipeline configs, or task-specific training configs -> `pytorch-workflows`
- S3 / Batch / SageMaker / filesystem runner plumbing -> `cloud-and-filesystems`

## Read first

- [Core data API](references/core-data-api.md)
- [Data formats](references/data-formats.md)
- [PyTorch learner API](references/pytorch-learner-api.md)
- [Troubleshooting](references/troubleshooting.md)

## Runtime helper

Use [scripts/check_scene_config.py](scripts/check_scene_config.py) to lint a `SceneConfig` JSON before deeper debugging.

## What to do
1. Identify whether the user is building scenes/labels directly, preparing learner data, or calling predictor APIs.
2. Validate `SceneConfig` / `ClassConfig` structure before suggesting a full pipeline run.
3. Prefer direct library usage over pipeline CLI when the task stays at the data/model layer.
4. Keep the output self-contained inside this skill tree.

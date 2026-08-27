# Model bundles

A Raster Vision model bundle is the packaged artifact that `predict` and `predict_scene` consume.
It is created by the pipeline `bundle` command.

## What the bundle contains
A standard bundle zip includes:
- model files from the training output
- `pipeline-config.json`
- analyzer outputs, such as stats, when present
- any backend-specific files listed by the backend config

The bundle is written under `bundle_uri` as `model-bundle.zip`.

## Why the bundle matters
The bundle preserves the training-time configuration needed for inference:
- model architecture
- channel order
- raster transformers and stats
- class configuration
- backend-specific metadata

That means prediction can usually run with only:
- a bundle URI
- an image URI or scene config URI
- an output label URI

## Prediction commands
### `predict`
Use when you have one image URI and one output label URI.

Common overrides:
- `--channel-order` when the new image band layout differs from training
- `--scene-group` when the bundle contains stats for multiple scene groups
- `--update-stats` when you want per-image stats instead of bundle stats

### `predict_scene`
Use when you already have a serialized `SceneConfig`.
This is the cleanest option when the scene definition is part of your workflow.

Optional `--predict_options_uri` lets you override sliding-window prediction settings without editing the bundle.

## Bundle and scene file-system rules
The bundle and any referenced inputs must be readable by the Raster Vision file-system layer.
That usually means one of:
- local paths
- HTTP/HTTPS URIs
- S3 URIs
- other file systems registered by Raster Vision plugins

## Common bundle mismatches
### Wrong imagery layout
Symptoms:
- channel-order errors
- strange predictions

Fix:
- override `--channel-order`
- make sure the bundle matches the image sensor and band order

### Missing stats or wrong scene group
Symptoms:
- `StatsTransformer` warnings or failures
- predictions that look inconsistent with training

Fix:
- ensure the bundle contains the right stats
- use `--scene-group` when multiple stats groups are bundled
- use `--update-stats` only when you intentionally want fresh stats for the current image

### Old or incomplete bundle
Symptoms:
- missing `pipeline-config.json`
- missing model files
- deserialization or upgrader errors

Fix:
- regenerate the bundle from the current training output
- make sure `train_uri` still contains the backend's required bundle filenames

### Wrong scene or label store shape
Symptoms:
- `predict_scene` or `predict` fails while building the scene
- label store or raster source fields are missing

Fix:
- verify the serialized `SceneConfig`
- ensure the scene config contains the URIs expected by the bundle

## Training vs inference bundle use
- `source_bundle_uri` feeds training and fine-tuning.
- `bundle_uri` is the inference-time artifact produced by the pipeline.

Do not confuse the two.

## Quick inspection rule
If prediction is failing, first check:
1. `pipeline-config.json` exists in the bundle
2. the bundle points at the right class config
3. the image URI is readable by Raster Vision
4. the channel order matches the target image

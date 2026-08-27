---
name: feature-postprocessing
description: "Guides RoboSat prediction post-processing from probability PNGs to
  masks, parking GeoJSON features, merge/dedupe cleanup, visual comparison, and
  vector artifact validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RoboSat feature post-processing

Use this sub-skill when a task already has RoboSat prediction probability tiles or mask tiles and needs to turn them into inspectable masks, parking-lot vector features, cleaned GeoJSON, or visual QA mosaics.

## Use this for

- Converting binary foreground-probability PNG Slippy Map outputs into palette mask tiles with `rs masks`.
- Extracting parking-lot WGS84 GeoJSON polygons from mask tiles with `rs features --type parking`.
- Merging adjacent predicted polygons with a meter threshold via `rs merge`.
- Deduplicating predictions against existing OSM-derived GeoJSON with an IoU threshold via `rs dedupe`.
- Building side-by-side image / label / mask mosaics with `rs compare`.
- Validating post-processing artifacts using bundled scripts.

## Route elsewhere

- Need to train a model, load checkpoints, export ONNX, run batch prediction, or produce probability PNGs first: use the `model-lifecycle` sub-skill.
- Need to extract OSM features before training, cover tiles, download imagery, rasterize labels, compute class weights, or subset tile sets: use the `data-preparation` sub-skill.
- Need non-parking post-processing handlers: this sub-skill explains the handler contract, but the installed CLI only registers the parking handler by default.

## Fast workflow map

1. Confirm that probability or mask directories are Slippy Map trees such as `18/69108/105091.png`; see [data formats](references/data-formats.md).
2. Convert probabilities to masks:
   `rs masks out/masks probs/run-a [probs/run-b ...] [--weights 0.7 0.3]`.
3. Convert parking masks to GeoJSON:
   `rs features out/masks --type parking --dataset dataset.toml out/features.geojson`.
4. Clean vector output:
   `rs merge out/features.geojson --threshold 3 out/features-merged.geojson`, then optionally `rs dedupe osm.geojson out/features-merged.geojson --threshold 0.5 out/features-new.geojson`.
5. Compare visual quality:
   `rs compare out/compare images labels out/masks [other/masks ...] --minimum 0.01 --maximum 0.95`.
6. Validate artifacts with [`scripts/validate_feature_collection.py`](scripts/validate_feature_collection.py) and smoke-test soft voting with [`scripts/softvote_smoke.py`](scripts/softvote_smoke.py).

Detailed command recipes are in [workflows](references/workflows.md). API behavior is summarized in [API reference](references/api-reference.md). Common failure modes are in [troubleshooting](references/troubleshooting.md).

## Key constraints to remember

- RoboSat probability PNG post-processing is binary: one quantized foreground-probability channel is reconstructed as foreground plus `1 - foreground` background.
- `rs features` is parking-only in the default installed CLI; the dataset config must include the `parking` class and mask class index must match it.
- `ParkingHandler` thresholds are tuned for zoom 18 and will raise on other zoom levels.
- `rs merge --threshold` is measured in meters; `rs dedupe --threshold` is intersection-over-union, not distance or model confidence.
- Post-processing is CPU-oriented. CUDA is not needed for the commands in this sub-skill.

# RoboSat CLI reference

Use the installed `rs` console script or the module form `python -m robosat.tools`. Commands below are grouped by owning sub-skill.

## Data preparation

| Command | Purpose | Inputs | Output | Owner |
| --- | --- | --- | --- | --- |
| `rs extract --type {parking,building,road} [--batch N] map.osm.pbf out.geojson` | Extract OSM geometries into GeoJSON FeatureCollections. | OSM PBF, handler type. | One or more batched GeoJSON files. | `data-preparation` |
| `rs cover --zoom Z features.geojson tiles.csv` | Burn feature geometries into covering Slippy Map tile ids. | GeoJSON FeatureCollection, zoom. | CSV rows in `x,y,z` order. | `data-preparation` |
| `rs download URL [--ext webp] [--rate N] tiles.csv out-dir` | Download imagery for tile ids. | URL template containing `{z}`, `{x}`, `{y}`; optional token; tile CSV. | Slippy Map image tree. | `data-preparation` |
| `rs rasterize features.geojson tiles.csv labels-dir --dataset dataset.toml --zoom Z [--size 512]` | Rasterize polygons into binary palette masks. | GeoJSON, tile CSV, dataset TOML. | Slippy Map PNG label tree. | `data-preparation` |
| `rs weights --dataset dataset.toml` | Compute class weights from `training/labels`. | Dataset TOML with dataset root/classes. | Printed Python list for `[weights].values`. | `data-preparation` |
| `rs subset images-dir tiles.csv out-dir` | Copy only selected tile files from a Slippy Map tree. | Slippy Map tree, CSV tile list. | Filtered Slippy Map tree preserving extensions. | `data-preparation` |

## Model lifecycle

| Command | Purpose | Inputs | Output | Owner |
| --- | --- | --- | --- | --- |
| `rs train --model model.toml --dataset dataset.toml [--checkpoint ckpt.pth] [--resume true] [--workers N]` | Train or resume the U-Net segmentation model. | Model config, dataset config, optional checkpoint. | Checkpoint `.pth`, `log`, `history-*.png`. | `model-lifecycle` |
| `rs export --dataset dataset.toml --checkpoint ckpt.pth [--image_size 512] model.pb` | Export checkpoint to ONNX GraphProto. | Dataset config for class count, checkpoint. | ONNX `.pb`. | `model-lifecycle` |
| `rs predict --model model.toml --dataset dataset.toml --checkpoint ckpt.pth --tile_size 512 [--batch_size N] [--overlap 32] [--workers N] tiles-dir probs-dir` | Predict binary foreground probability PNGs for image tiles. | Model/dataset configs, checkpoint, Slippy Map image tree. | Slippy Map probability PNG tree. | `model-lifecycle` |
| `rs serve --model model.toml --dataset dataset.toml --checkpoint ckpt.pth [--url URL] [--tile_size 512] [--host 127.0.0.1] [--port 5000]` | Serve on-demand mask tiles for visual inspection. | Configs, checkpoint, URL template, `MAPBOX_ACCESS_TOKEN`. | Flask tile service. | `model-lifecycle` |

## Feature post-processing

| Command | Purpose | Inputs | Output | Owner |
| --- | --- | --- | --- | --- |
| `rs masks masks-dir probs-dir [more-probs ...] [--weights w1 w2 ...]` | Convert one or more probability trees into palette mask tiles via soft voting. | Probability PNG Slippy Map trees. | Mask PNG Slippy Map tree. | `feature-postprocessing` |
| `rs features masks-dir --type parking --dataset dataset.toml out.geojson` | Convert parking mask tiles into GeoJSON polygons. | Mask tree, dataset TOML, type. | GeoJSON FeatureCollection. | `feature-postprocessing` |
| `rs merge features.geojson --threshold meters out.geojson` | Merge adjacent polygons after buffering. | GeoJSON FeatureCollection, distance threshold. | Merged GeoJSON FeatureCollection with area property. | `feature-postprocessing` |
| `rs dedupe osm.geojson predicted.geojson --threshold iou out.geojson` | Remove predicted polygons overlapping OSM ground truth above an IoU threshold. | OSM GeoJSON, predicted GeoJSON, IoU threshold. | Deduplicated GeoJSON FeatureCollection. | `feature-postprocessing` |
| `rs compare out-dir images-dir labels-dir masks-dir [more-masks ...] [--minimum p] [--maximum p]` | Build side-by-side image/label/mask mosaics for visual QA. | Image/label/mask Slippy Map trees. | Mosaic image Slippy Map tree. | `feature-postprocessing` |

## Command-building checklist

- Use dataset/model TOML files from [configuration](configuration.md) or generate templates with `scripts/create_config_templates.py`.
- Run the nearest validation script before expensive commands: `validate_slippy_map.py`, `check_training_layout.py`, `unet_cpu_smoke.py`, `softvote_smoke.py`, or `validate_feature_collection.py`.
- Keep network URL tokens and `MAPBOX_ACCESS_TOKEN` out of saved command logs.
- For GPU commands, set `model.common.cuda=true` only after a CUDA torch smoke has passed.

---
name: data-preparation
description: "Guides RoboSat data preparation for Slippy Map imagery, OSM
  features, rasterized masks, tile CSVs, dataset configs, class weights, and
  safe CLI validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Preparation

Use this sub-skill when you need RoboSat dataset inputs, not model training or post-processing.

## Use this for

- extracting OSM features into GeoJSON
- building tile cover CSVs
- downloading imagery into Slippy Map directories
- rasterizing features into masks
- computing class weights from training labels
- validating tile layout and tile-list alignment
- drafting dataset TOML templates

## Route elsewhere

- model lifecycle: training, export, predict, serve, checkpoints, UNet
- feature post-processing: probability-to-mask, features, merge, dedupe, compare

## Quick path

1. Start with the recipes in [workflows](references/workflows.md).
2. Check the data layouts in [data formats](references/data-formats.md).
3. Use the API notes in [API reference](references/api-reference.md) when wiring helpers.
4. Run [validate_slippy_map.py](scripts/validate_slippy_map.py) before weights or rasterize jobs.
5. Use [troubleshooting](references/troubleshooting.md) for install, geometry, sync, or zoom problems.

## Common outputs

- `features.geojson`
- `tiles.csv`
- Slippy Map image and mask trees
- dataset TOML with `[common]` and `[weights]`
- class weights list from `rs weights`

## Safe defaults

- Prefer `rs` or `python -m robosat.tools ...` from an installed environment.
- Keep downloads, tokens, and large datasets outside the skill tree.
- Treat `rs rasterize` as binary-only in this release.

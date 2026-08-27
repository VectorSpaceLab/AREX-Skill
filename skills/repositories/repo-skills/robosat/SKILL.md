---
name: robosat
description: "Guides RoboSat aerial and satellite imagery segmentation workflows
  with Slippy Map data preparation, U-Net model lifecycle, feature
  post-processing, CLI usage, configs, and legacy environment troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RoboSat

Use this repo skill when a task involves RoboSat, the `robosat` Python package, the `rs` CLI, aerial/satellite imagery semantic segmentation, Slippy Map tile trees, OSM-derived feature masks, U-Net checkpoints, probability PNGs, or GeoJSON feature extraction.

RoboSat is a legacy Mapbox package for feature extraction from aerial and satellite imagery. It organizes data as Slippy Map tiles, trains a PyTorch U-Net-style segmentation model, predicts binary foreground probabilities, and post-processes masks into GeoJSON features.

## Start here

1. Read [installation and environment](references/installation-and-environment.md) when installing, importing, checking the CLI, choosing CPU/CUDA, or debugging old dependency stacks.
2. Read [CLI reference](references/cli-reference.md) to route an `rs` command or build a command line.
3. Read [configuration](references/configuration.md) before editing dataset/model TOML files.
4. Use [troubleshooting](references/troubleshooting.md) for cross-cutting install, CRS, tile layout, backend, token, or binary-class issues.
5. Use [repo provenance](references/repo-provenance.md) before refreshing this skill against a newer checkout.

## Route by task

| User task | Read |
| --- | --- |
| Extract OSM buildings/roads/parking, create tile CSVs, download imagery, rasterize labels, validate tile trees, compute class weights, or subset image/label tiles | [data-preparation](sub-skills/data-preparation/SKILL.md) |
| Train or resume U-Net models, export ONNX, run batch prediction, serve mask tiles, inspect losses/metrics/transforms/checkpoints, or decide CPU vs CUDA | [model-lifecycle](sub-skills/model-lifecycle/SKILL.md) |
| Convert probability PNGs to masks, extract parking GeoJSON, merge/dedupe predicted polygons, compare image/label/mask mosaics, or validate vector outputs | [feature-postprocessing](sub-skills/feature-postprocessing/SKILL.md) |

## Minimal environment check

After installing RoboSat in an environment, prefer the installed package entry points rather than a source-checkout wrapper:

```bash
python -c "import robosat; print('robosat import ok')"
rs --help
python -m robosat.tools --help
python scripts/check_robosat_env.py --check-cli
```

The bundled [check_robosat_env.py](scripts/check_robosat_env.py) checks imports, `rtree`/`libspatialindex`, pyproj ESRI CRS lookup, optional torch/CUDA state, and CLI help. Use [create_config_templates.py](scripts/create_config_templates.py) to write CPU-safe dataset/model TOML templates.

## Important constraints

- RoboSat is legacy Python-era software. Python 3.6 plus the documented runtime dependency family is the safest source-install target; Docker CPU/GPU images were the original operational path.
- GPU is optional in this skill. This skill generation verified CPU import, CLI help, and a CPU U-Net smoke only; it does not claim CUDA training/prediction verification.
- The default prediction and post-processing path is binary foreground/background. Several helpers assume two classes and parking-specific post-processing.
- Runtime instructions in this skill are self-contained; do not require the original repository checkout when using the installed package.

## Common pipeline

1. Data preparation: OSM feature extraction -> tile cover CSV -> imagery download -> rasterized masks -> weights.
2. Model lifecycle: training or checkpoint resume -> optional ONNX export -> prediction probability tiles or on-demand serving.
3. Feature post-processing: probability tiles -> mask tiles -> parking GeoJSON -> merge/dedupe -> visual comparison.

Use the sub-skill routes above for concrete commands, APIs, data formats, validation scripts, and troubleshooting.

---
name: media-and-custom-charts
description: "Log SwanLab text, HTML, rich media, 3D objects, molecules, and
  custom pyecharts charts safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Media and custom charts

Use this sub-skill when the request is about SwanLab rich media or chart objects rather than scalar metrics.

## Start here
1. Read [Media reference](references/media-reference.md) for constructor signatures, accepted inputs, output files, and `log_*` wrappers.
2. Read [Custom charts](references/custom-charts.md) for `ECharts`, `swanlab.echarts.Table`, and `swanlab.plot`.
3. Read [Troubleshooting](references/troubleshooting.md) when a file path, dependency, or chart object fails.
4. Run [the lightweight smoke script](scripts/check_lightweight_media.py) for a safe check that skips missing optional media extras.

## What this sub-skill owns
- Text and HTML logging.
- Image, audio, and GIF video logging.
- pyecharts-backed custom charts, text tables, and diagnostic chart helpers.
- 3D object and molecule media objects.
- Distinguishing format errors, path errors, type mismatches, and missing optional dependencies.

## What it does not own
- Scalar metrics, configs, or `define_scalar` → `experiment-tracking`.
- Framework-generated media from callbacks or plugins → `integrations-and-plugins`.
- Login, mode, host, or environment setup → `settings-and-modes`.
- Sync, conversion, or API browsing → the other sub-skills in the parent skill tree.

## Safe defaults
- Treat `swanlab[media]` as optional and skip rich media checks when `numpy`, `Pillow`, `soundfile`, `moviepy`, or `rdkit` are missing.
- Prefer tiny fixtures for smoke checks; these transformers buffer the full payload in memory.
- Remember that `ECharts` accepts any object with `dump_options()`.
- Remember that current `Video` support is GIF-only.
- Prefer `swanlab.Text` and `swanlab.Html` for the lightest successful media smoke.

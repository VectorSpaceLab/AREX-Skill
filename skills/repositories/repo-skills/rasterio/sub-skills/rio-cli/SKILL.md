---
name: rio-cli
description: "Routes Rasterio rio CLI command selection, global options, raster
  metadata, conversion, feature, masking, reprojection, and troubleshooting
  tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Rio CLI

Use this sub-skill when a user wants a `rio` command rather than Python API code, or when they need to debug `rio` option parsing, file output, JSON/GeoJSON output, or command selection.

## Typical requests

- "What `rio` command shows raster metadata?"
- "Clip this raster to bounds on the command line."
- "Use `rio warp` to reproject a file."
- "Why does `rio` say these options cannot be combined?"

## What this sub-skill owns

- Global `rio` options: verbosity, AWS profile/no-sign/requester-pays, version, GDAL version, and show-versions.
- Metadata/inspection commands: `env`, `info`, `bounds`, `insp`, `blocks`, `gcps`, `sample`, and `transform`.
- Create/convert/update commands: `create`, `convert`, `edit-info`, `overview`, and `rm`.
- Feature/mask commands: `mask`, `rasterize`, and `shapes`.
- Multi-raster commands: `merge`, `stack`, and `warp`.
- Expression workflows with `rio calc`.
- Command-specific parse errors and safe command construction.

## What it excludes

- Deep Python API recipes; route to the owning API sub-skill after choosing the equivalent `rio` command.
- Network or credentialed S3 operations unless the user has explicitly configured the relevant environment and optional dependencies.
- Long-running or destructive file operations unless the user has confirmed output paths and overwrite behavior.

## Read first

- [`references/cli-reference.md`](references/cli-reference.md) for command selection, common flags, and output patterns.
- [`references/troubleshooting.md`](references/troubleshooting.md) for Click parse errors, invalid CRS/bounds, overwrite protection, and optional cloud flags.
- [`scripts/rio_smoke.py`](scripts/rio_smoke.py) for a safe local CLI smoke check.

## Workflow shape

1. Determine whether the user needs inspection, transformation, creation, masking/rasterizing, multi-raster composition, or environment diagnostics.
2. Choose the smallest `rio` command that matches that intent.
3. Add global options only when needed; do not use AWS flags without user approval.
4. Quote bounds or GeoJSON input carefully so the shell passes arguments as intended.
5. Validate outputs with `rio info`, `rio bounds`, or the bundled smoke helper.

## Decision points

- Use `rio info` for metadata and scalar extraction.
- Use `rio bounds` for bbox/GeoJSON extents.
- Use `rio transform` for coordinate arrays.
- Use `rio clip` for rectangular/data-window/template clipping, and `rio mask` for GeoJSON feature masks.
- Use `rio warp` for reprojection/resampling/grid changes.
- Use `rio merge` for mosaics and `rio stack` for multiband stacks.
- Use `rio calc` for simple array expressions; route complex NumPy workflows to Python API sub-skills.

## Common mistakes

- Forgetting that many write commands protect existing outputs unless overwrite is explicit.
- Mixing `--bounds`, `--res`, and `--dimensions` without one clear grid-sizing strategy.
- Passing malformed CRS strings such as `EPSG:`.
- Treating shell quoting errors as Rasterio API bugs.
- Using cloud/S3 flags without installing optional dependencies or configuring credentials.

## Good validation path

- `tests/test_rio_main.py::test_version`
- `tests/test_rio_info.py::test_info`
- `tests/test_rio_info.py::test_transform_point`
- `tests/test_rio_clip.py::test_clip_bounds`
- `tests/test_rio_warp.py::test_warp_reproject_dst_crs`
- `tests/test_rio_calc.py` selected safe cases

## What a future agent should be able to do here

A future agent should be able to answer ordinary and borderline `rio` command questions with copyable commands and concrete parse-error recovery, without reopening the original docs.

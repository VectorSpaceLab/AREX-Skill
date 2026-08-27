---
name: rasterio
description: "Routes Rasterio dataset I/O, windowed processing, in-memory files,
  raster/vector feature workflows, reprojection and mosaicking, and rio CLI
  tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Rasterio

Rasterio reads and writes geospatial raster data with a NumPy-friendly API and a `rio` command-line interface.

Start here when a user wants to open a raster, inspect metadata, crop or mask by geometry, reproject into a new CRS, merge overlapping scenes, process a raster in windows, or choose the right `rio` command.

## Install and verify

For a local checkout, install from the repository root:

```bash
python -m pip install -e .
```

For a released environment, install the package directly:

```bash
python -m pip install rasterio
```

Rasterio 1.5.x requires Python 3.12+ and a working GDAL/PROJ-backed build or wheel. Optional extras exist for cloud access, plotting, and IPython-based inspection.

Minimal verification:

```bash
python -I -c "import rasterio; print(rasterio.__version__)"
rio --help
```

For a repo-independent smoke check, use [`scripts/check_install.py`](scripts/check_install.py).

Read [`references/repo-provenance.md`](references/repo-provenance.md) when you need to confirm whether this skill still matches the current checkout.

## How to route a user request

- If the user wants basic read/write, band counts, CRS, transform, or profile copying, start with [`sub-skills/dataset-io-profiles/`](sub-skills/dataset-io-profiles/).
- If the user is asking about `Window`, block reads/writes, `MemoryFile`, ZIP/VSI paths, or custom openers, start with [`sub-skills/windows-memory-vsi/`](sub-skills/windows-memory-vsi/).
- If the user is moving between rasters and geometries, masks, rasterization, or nodata cleanup, start with [`sub-skills/features-masks/`](sub-skills/features-masks/).
- If the user needs CRS transforms, reprojection, `WarpedVRT`, merge, or stack, start with [`sub-skills/reprojection-merge-vrt/`](sub-skills/reprojection-merge-vrt/).
- If the user wants `rio` command syntax, safe flags, or Click-style parse troubleshooting, start with [`sub-skills/rio-cli/`](sub-skills/rio-cli/).

If a request spans several topics, pick the most specific sub-skill first and then follow the cross-links inside that sub-skill.

## Runtime map

### `dataset-io-profiles`
Use this for ordinary raster inspection and creation tasks:
- `rasterio.open`
- `DatasetReader` / `DatasetWriter`
- `profile` / `meta`
- dtypes, nodata, compression, band count, dimensions, and simple round trips

### `windows-memory-vsi`
Use this for data that should be processed in chunks, kept in memory, or opened through archive/path abstractions:
- `Window`
- `block_windows`
- `MemoryFile`
- `ZipMemoryFile`
- `zip://` / `file://` / GDAL VSI path handling

### `features-masks`
Use this for geometry-driven raster/vector conversion and mask cleanup:
- `shapes`
- `rasterize`
- `sieve`
- `geometry_window`
- `mask` / `raster_geometry_mask`
- GDAL valid masks vs NumPy masked arrays

### `reprojection-merge-vrt`
Use this for CRS changes and mosaics:
- `transform` / `transform_geom` / `transform_bounds`
- `calculate_default_transform`
- `reproject`
- `WarpedVRT`
- `merge` / `stack`

### `rio-cli`
Use this for shell workflows:
- `rio info`, `bounds`, `transform`, `clip`, `warp`, `mask`, `rasterize`, `shapes`, `merge`, `stack`, `create`, `convert`, `env`, and `insp`

## Shared references and tools

- [`references/troubleshooting.md`](references/troubleshooting.md) — cross-cutting install/import, driver, and optional-extra failures.
- [`scripts/check_install.py`](scripts/check_install.py) — safe install/import/CLI smoke helper that does not depend on the original checkout.

## Common prerequisites

- Python 3.12 or newer.
- GDAL/PROJ available through a wheel, conda environment, or equivalent local installation.
- Optional extras only when needed:
  - `rasterio[s3]` for cloud/object storage access.
  - `rasterio[plot]` for plotting helpers.
  - `rasterio[ipython]` for `rio insp --ipython`.

## What not to do

- Do not tell users to run or read `examples/`, `tests/`, or `docs/` in the original checkout at runtime.
- Do not claim GPU-specific capability for the selected workflows; the package paths here are CPU/GDAL based.
- Do not rely on the current repository path remaining available after this skill is imported.
- Do not duplicate full API tables in this file; use the nearest reference file instead.

## Refresh signal

If the repo commit, public package version, or CLI/API surface changes, refresh this skill before relying on it.

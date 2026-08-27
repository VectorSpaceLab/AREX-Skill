---
name: dataset-io-profiles
description: "Routes Rasterio dataset opening, reading, writing, profiles,
  creation options, nodata, and simple round-trip workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Dataset I/O and Profiles

Use this sub-skill when a user wants to open a raster, inspect metadata, write a new dataset, clone a profile, or troubleshoot `rasterio.open` in read/write modes.

## Typical requests

- "How do I read the bands from a GeoTIFF?"
- "How do I create a new raster with the same profile?"
- "Why does writing fail because `dtype`, `count`, or `driver` is missing?"
- "How do I set nodata or compression options when creating a file?"

## What this sub-skill owns

- `rasterio.open` in read and write modes.
- `DatasetReader` and `DatasetWriter` basics.
- `profile`, `meta`, `dtypes`, `count`, `shape`, `bounds`, `crs`, `transform`, and nodata handling.
- GeoTIFF creation options and `default_gtiff_profile`.
- Safe copy/decimate workflows that stay within the package API.

## What it excludes

- Window/block iteration and in-memory/VSI path details, which live in `windows-memory-vsi`.
- Geometry masks, shapes, rasterization, and nodata-mask repair, which live in `features-masks`.
- Reprojection, WarpedVRT, merge, and stack workflows, which live in `reprojection-merge-vrt`.
- `rio` command selection, which lives in `rio-cli`.

## Read first

- [`references/api-reference.md`](references/api-reference.md) for the verified `rasterio.open` signature and the creation kwargs most often used here.
- [`references/workflows.md`](references/workflows.md) for the common open/read/write and profile-copying recipes.
- [`references/troubleshooting.md`](references/troubleshooting.md) for missing driver, dtype, nodata, and import/build failures.
- [`scripts/check_install.py`](../../scripts/check_install.py) for a repo-independent smoke check.

## Helper scripts

- [`scripts/make_total_band.py`](scripts/make_total_band.py) — average selected bands and write a one-band output.
- [`scripts/decimate_copy.py`](scripts/decimate_copy.py) — shrink an output grid while keeping the source metadata pattern.

## Workflow shape

1. Inspect the source raster with `rasterio.open`.
2. Copy `src.profile` or `src.meta` before changing output settings.
3. Update only the fields that truly change: driver, count, dtype, compression, nodata, width, height, and transform.
4. Write the output in a second `rasterio.open(..., "w", **profile)` block.
5. Re-open the output and confirm shape, dtype, CRS, and nodata.

## Decision points

- If the band count changes, update `count` and usually `dtype`.
- If the pixel grid changes, update `width`, `height`, and often `transform`.
- If the file format changes, update `driver` and any format-specific creation options.
- If nodata changes, confirm that the chosen dtype can represent it.
- If you want a one-band summary from an RGB image, use the averaging helper instead of writing ad hoc profile logic.

## Common mistakes

- Trying to write without `dtype` or `count`.
- Forgetting to update `width` and `height` when the destination raster shape changes.
- Reusing a source profile without changing the driver when the output format differs.
- Passing a nodata value that does not fit the chosen dtype.
- Telling the user to edit the original repo example instead of using the bundled helper.

## Good validation path

- `tests/test_read.py::ReaderContextTest::test_context`
- `tests/test_write.py::test_no_crs`
- `tests/test_write.py::test_wplus_transform`
- `tests/test_write.py::test_write_masked_nodata`
- `tests/test_write.py::test_write__autodetect_driver`

## What a future agent should be able to do here

A future agent should be able to answer ordinary open/read/write/profile questions using this sub-skill plus the bundled references and scripts, without reopening the original checkout.

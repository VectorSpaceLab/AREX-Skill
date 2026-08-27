---
name: windows-memory-vsi
description: "Routes Rasterio windowed I/O, block processing, in-memory files,
  archive/VSI paths, and custom opener workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Windows, Memory Files, and VSI Paths

Use this sub-skill when a user wants to read or write rasters in windows, process blocks concurrently, keep rasters in memory, or open `zip://` / `file://` / GDAL VSI paths.

## Typical requests

- "How do I read only a window of a raster?"
- "How do I use `MemoryFile` instead of a temporary file?"
- "How do I open a raster inside a zip file?"
- "How do I process blocks concurrently?"

## What this sub-skill owns

- `Window`, `Window.from_slices`, `from_bounds`, `window_index`, `get_data_window`, and block-aligned window helpers.
- `MemoryFile`, `ZipMemoryFile`, and safe local byte-stream workflows.
- `zip://`, `zip+file://`, `file://`, and the `rasterio._path`/GDAL VSI path conventions.
- Custom opener use cases and the practical limits around sidecar files.
- Safe windowed concurrency patterns.

## What it excludes

- Dataset profile and basic write-time metadata choices, which live in `dataset-io-profiles`.
- Geometry masks/rasterization, which live in `features-masks`.
- Reprojection, WarpedVRT, and merge/stack workflows, which live in `reprojection-merge-vrt`.
- `rio` CLI flag selection, which lives in `rio-cli`.

## Read first

- [`references/api-reference.md`](references/api-reference.md) for the verified `Window` and `MemoryFile` signatures.
- [`references/workflows.md`](references/workflows.md) for the common windowed read/write, MemoryFile, and VSI recipes.
- [`references/troubleshooting.md`](references/troubleshooting.md) for invalid windows, closed MemoryFiles, and opener/VSI limitations.
- [`scripts/check_install.py`](../../scripts/check_install.py) for a repo-independent smoke check.

## Helper scripts

- [`scripts/windowed_copy.py`](scripts/windowed_copy.py) — safe block-processing helper adapted from the thread-pool example.
- [`scripts/memoryfile_smoke.py`](scripts/memoryfile_smoke.py) — open a local file in memory and print a compact summary.
- [`scripts/vsi_smoke.py`](scripts/vsi_smoke.py) — open a `zip://` / `file://` URI and print the dataset summary.

## Workflow shape

1. Decide whether the task is pixel-based or world-coordinate-based.
2. Use `Window` and `block_windows` when the task is about chunks of pixels.
3. Use `get_data_window` when you need the tight valid-data extent of a masked raster.
4. Use `MemoryFile` when the input is bytes or when a temporary file would be awkward.
5. Use `zip://` or `file://` URIs when the dataset is already packaged locally.
6. Fall back to a real filesystem path when a custom opener would hide required sidecar files.

## Decision points

- `Window.from_slices` is the right tool when the user already has Python-style row/column slices.
- `from_bounds` is the right tool when the user already has spatial bounds and the transform is known.
- `MemoryFile` is ideal for bytes in RAM, but a closed MemoryFile cannot be reused.
- `ZipMemoryFile` is useful for archive members, but not every sidecar-dependent workflow fits through it.
- The concurrent helper should start conservative and lock reads/writes separately.

## Common mistakes

- Confusing row/column order with x/y order.
- Treating a closed `MemoryFile` like an open file object.
- Assuming a custom opener will expose sidecar mask or metadata files.
- Using a window that extends beyond the dataset bounds without checking the expected behavior.

## Good validation path

- `tests/test_windows.py::test_read_with_window_class`
- `tests/test_windows.py::test_window_from_bounds`
- `tests/test_windows.py::test_round_window_to_full_blocks`
- `tests/test_windows.py::test_data_window_full_2d`
- `tests/test_memoryfile.py::test_initial_bytes`
- `tests/test_memoryfile.py::test_zip_file_object_read`
- `tests/test_path.py::test_read_vfs_zip`

## What a future agent should be able to do here

A future agent should be able to answer common windowed-IO or in-memory-file tasks using this sub-skill plus the bundled files, without reopening the original repo.

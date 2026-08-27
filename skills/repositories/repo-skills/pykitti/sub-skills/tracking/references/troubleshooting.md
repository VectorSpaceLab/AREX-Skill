# Tracking troubleshooting

For package-wide installation, import, and environment diagnosis also read the
[shared root troubleshooting guide](../../../references/troubleshooting.md).
Route raw-drive failures to [raw-data](../../raw-data/SKILL.md) and odometry
sequence failures to [odometry](../../odometry/SKILL.md).

## Import and dependency failures

`setup.py` declares NumPy, matplotlib, Pillow, and pandas but does not declare
OpenCV. Nevertheless `pykitti/__init__.py` imports `tracking`, and
`tracking.py` imports `cv2` eagerly. Therefore even a raw or odometry workflow
can fail at `import pykitti` with `ModuleNotFoundError: cv2`. Install a
compatible CPU/headless OpenCV distribution in the same environment, then
probe:

```bash
python -c "import cv2, pykitti; print(cv2.__version__)"
```

Do not work around this by adding a source checkout to `PYTHONPATH`; diagnose
the active environment and package installation instead. The label utility
also imports through the package namespace, so it encounters the same eager
OpenCV dependency.

## File path and token-count failures

`KittiTrackingLabels(path, ...)` raises `ValueError` when the path does not
exist. A present file can still fail when its rows have inconsistent token
counts or when pandas cannot assign the inferred column prefix. Check that:

- each nonblank label row has 17 tokens: frame + 16 fields through `roty`;
- each nonblank detection row has 18 tokens: frame + the optional `score`;
- all rows use one schema and ordinary single-space-separated values;
- frame tokens are non-negative integers and rows are frame-sorted;
- numeric fields are parseable and `class` is spelled consistently.

The source treats the first token as the index. It does not expose a frame
column or insert missing payload columns.

## Empty or filtered inputs

The default `remove_dontcare=True` drops exact `DontCare` rows before ID
normalization. If every row is `DontCare`, the constructor tries `max()` on an
empty ID array and fails. Handle an empty/all-ignored file before constructing
or pass `remove_dontcare=False` when those rows are intentionally needed.

Missing `id` or `class` columns fail during filtering/normalization. Missing
columns used by `bbox`, `cls`, or `occlusion` fail only when that property is
accessed. The constructor does not provide a schema validator; perform one in
the calling workflow.

## IDs, splitting, and frame indexes

IDs are always remapped to zero-based contiguous values in first-seen order;
this is not a way to preserve source track IDs. `split_on_reappear=True` gives
a later segment a new normalized ID after a frame gap greater than one. Sort
rows by frame and avoid duplicate identity rows within one frame before using
this option. If a source identity must remain unified across an absence, pass
`split_on_reappear=False` and retain the absence explicitly in downstream
logic.

`presence` uses a matrix with rows `0 .. max(index)`, not
`0 .. len(labels)-1`. A nonzero starting index therefore creates leading false
rows and can disagree with `len(labels)`, which is
`last_index - first_index + 1`. Reindex a prepared DataFrame to a zero-based
frame convention when dense arrays are required.

## Ragged output and missing-index behavior

`to_array_list` initializes empty slots for missing frame indexes and ends with
`np.asarray`. In current NumPy, any empty slot or variable object count can
produce a ragged-list `ValueError` rather than a useful object array. An
explicit `length` sets the number of slots but does not pad rows. Validate
index continuity and per-frame counts before calling it, or catch the error and
perform padding in caller-owned code.

`by_id=True` requires a DataFrame `id` column. The special case where `id` is
the only column disables sorting/removal. Passing a Series, as the source's
`KittiTrackingLabels.id` property does, raises `AttributeError` because Series
has no `.columns`.

## Current pandas compatibility

`KittiTrackingLabels.num_objects` is not a supported modern-pandas guarantee.
The implementation calls `Series.append` and then `as_matrix`, both removed in
modern pandas. In the verified pandas 3 environment, access fails at
`append`; do not paper over this by claiming that object counts are available.
The deterministic smoke script deliberately exercises supported label outputs
without requiring this legacy property.

## Incomplete `tracking` loader symptoms

The constructor `tracking(base_path, sequence, **kwargs)` is not equivalent to
the raw or odometry loaders:

- it eagerly imports OpenCV through the module import;
- it discovers only `image_02`, `image_03`, and `velodyne` globs and prints a
  `files` line;
- it never initializes `timestamps`, so `len(dataset)` raises
  `AttributeError`;
- with `frames` set, it references nonexistent `cam0_files` and `cam1_files`;
- `gray`/`get_gray` refer to those absent camera streams;
- it does not parse labels, calibration, timestamps, or tracking metadata.

Do not silently substitute it for `KittiTrackingLabels`. If a caller needs
sensor loading, route to a sibling loader and validate its actual KITTI layout.

## Safety boundary

Do not run the repository downloader from a Researcher workflow: it performs
network downloads, external archive extraction, directory changes, and cleanup
of detector label whitespace. Acquire data under an approved process and pass
only local, validated files to the label parser. The bundled fixture script is
local, deterministic, headless, and network-free.

# Preparation workflows

## A. Plan a new preprocessing run

1. **Inventory before execution.** Resolve `DATA_PATH` to the dataset root expected
   by the selected loader. Count candidate subject/trial files and inspect one
   frame source plus one label source. Do not start with `DO_PREPROCESS: true` on
   an unverified tree.
2. **Choose an isolation boundary.** Use a new cache directory per dataset,
   transform, crop/resize policy, and split. Keep `DataFileLists` inside or beside
   that cache, and avoid writing into raw data. Existing outputs are not proof of
   compatibility: a cache made with a different face backend or `DATA_TYPE` can
   have the same-looking names.
3. **Set labels and synchronization.** Prefer ground-truth labels where their
   sampling and morphology are appropriate. Enable `USE_PSUEDO_PPG_LABEL` only as
   an intentional weak-supervision choice. Loaders such as PURE, UBFC-Phys,
   MMPD, BP4D+, iBVP, PhysDrive, LADH, SUMS, and COHFACE explicitly resample or
   synchronize labels; still check the resulting frame/label length.
4. **Probe crop behavior.** Start with `HC`, a low worker count, and a few videos.
   Check for no-face fallback, multiple faces, motion-induced box drift, and
   whether the chosen large box includes excessive background. Use dynamic
   detection for substantial motion; use a median box only when a stable common
   region is desired. For Y5F, stage package resources and verify device/memory
   before processing.
5. **Build and audit.** Run the configured preprocessing once, then inspect the
   generated CSV and a few input/label pairs. Run:

   ```bash
   python scripts/validate_preprocessed_data.py \
       --file-list path/to/list.csv --data-format NDHWC
   ```

   The script never writes. For standard cache files, expected input rank is 4,
   label rank is 1, and their first dimensions match. Use `--data-format NDCHW`
   only for arrays that are already channel-first; source cache files are normally
   channel-last on disk.
6. **Freeze the cache.** Set `DO_PREPROCESS: false` after successful generation.
   Retain the exact config and resource-resolution decision outside the runtime
   skill. Before reuse on another machine, check whether CSV paths are absolute or
   relative and rewrite them deliberately rather than trusting a working directory.

## B. Use a custom file list

Create a CSV with exactly an `input_files` column. Populate it with paths to
existing `*_input*.npy` files and ensure each path's sibling label exists. Point
`DATA.<split>.FILE_LIST_PATH` directly at that CSV and set `DO_PREPROCESS: false`;
the config code rejects a user-specified CSV while preprocessing is enabled. The
loader sorts entries, derives labels by name substitution, and may apply
loader-specific filters afterward. Validate every path before launching a model.
A custom list is a selection mechanism, not a repair mechanism: it does not
resample, crop, normalize, or synthesize missing labels.

## C. Recover a missing/retroactive list

When preprocessing is disabled and the cache exists but the list is missing, the
base loader calls `get_raw_data`, applies the requested split, extracts each raw
record's `index`, and globs `<index>_input*.npy` in the cache. This requires the raw
layout to remain discoverable and cache names to preserve the loader's source ids.
It can fail for a relocated cache, altered naming, or a loader whose id is not
unique. Prefer a checked-in/custom CSV when portability matters. BigSmall uses its
own retroactive routine and optionally filters by the selected fold before globbing
`*.pickle` inputs.

## D. Subject-safe splits

For PURE, MMPD, BP4D+, iBVP, PhysDrive, LADH, SUMS, and BigSmall, the source groups
records by subject before applying `BEGIN`/`END` where implemented. UBFC-rPPG,
UBFC-Phys, and SCAMPS use record-order slicing, so do not infer subject isolation
from a fractional split. Use explicit custom file lists for reproducible cross-
validation when order or subject membership needs to be controlled.

For BP4D BigSmall, select one of the six supplied fold CSVs:
`Split{1,2,3}_{Train,Test}_Subjects.csv`. They have a `subjects` column containing
IDs such as `F001`/`M001`. The loader compares the first four characters of its
trial id against that column and only supports AU-bearing trials (`T1`, `T6`, `T7`,
`T8`). Keep the fold CSV out of the generic NPY validator because BigSmall inputs
are pickle dictionaries and labels are 49-column arrays.

## E. Motion-augmented input

Generate motion-augmented data with the external MA-rPPG Video Toolbox using an
original dataset and driving videos according to that project's documented
workflow. This repository does not generate, download, or validate the external
augmentation. Set `DATA_AUG` to include `Motion` for loaders with a Motion branch:
UBFC-rPPG, PURE, iBVP, and PhysDrive explicitly read NPY frames; other loaders may
not accept it even if a config key is added. Check the expected NPY value range:
`read_npy_video` accepts integer frames in `[0,255]` or floating frames in
`[0,1]`, and keeps the first three channels. Labels remain aligned to the loaded
frame count and are then resampled/processed as usual.

## F. Add a dataset loader

Start from `BaseLoader` and implement `get_raw_data`, `split_raw_data`, a
preprocessing worker, and static `read_video`/`read_wave` methods. Reuse common
`__len__`, `__getitem__`, `save`, and `load` behavior unless the dataset's format
requires a documented exception. Ensure the worker returns frames as
`(T,H,W,C)`, labels as a one-dimensional signal of matching length, and a stable
source id. Add a loader registry/config entry in the product code only after a
small fixture proves layout discovery, label alignment, cache naming, and reload.
Keep trainer/model changes outside this workflow.

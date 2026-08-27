---
name: preprocessing
description: "Guides braindecode preprocessing pipelines for MNE and
  array-backed electrophysiology datasets, including typed operations, window
  ordering, and serialized execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Preprocessing

Use this route for filtering, resampling, scaling, channel selection, montage
operations, cropping, preprocessing class composition, or `preprocess` execution
on raw, epoch, concat, or window datasets.

## Workflow

1. Record the input object type, channel order/types, sampling frequency, units,
   preload state, and whether the operation mutates the object.
2. Build a short ordered list of `Preprocessor` objects. Use typed classes such
   as `Pick`, `Resample`, `Filter`, `Scale`, `Crop`, and montage operations when
   they make units and validation explicit; use a callable for custom array
   operations only when `apply_on_array` is correct.
3. Apply continuous/raw operations before windowing when they require temporal
   context. Apply window-level normalization after window creation when it must
   not mix recordings.
4. Recalculate sample-based window parameters after resampling. Start with
   `n_jobs=1`; increase parallelism only after a one-recording result is correct.
5. Use `save_dir`/`overwrite` only with a deliberate cache key containing the
   preprocessing configuration.

Read [API reference](references/api-reference.md), [workflow guidance](references/workflows.md),
and [troubleshooting](references/troubleshooting.md). Run the local synthetic
[preprocessing smoke helper](scripts/smoke_preprocess.py); it performs no data
fetch, Hub operation, or model training. EEGPrep is an optional integration,
not a baseline requirement.

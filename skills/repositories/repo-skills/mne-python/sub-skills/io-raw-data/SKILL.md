---
name: io-raw-data
description: "Read, create, inspect, annotate, concatenate, save, and export
  MNE-Python Raw/Info data containers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# IO and Raw Data

Use this sub-skill when the task starts from neurophysiology files or NumPy arrays and needs an MNE-Python `Raw`/`BaseRaw` object, `Info` metadata, channel picks/types, raw-level annotations, concatenation, preloading, FIF save, or external export.

## Route by task

- **Read a file**: choose `mne.io.read_raw()` for simple suffix-based dispatch, or a format-specific `read_raw_*` function when the format has sidecars, ambiguous suffixes, optional keyword choices, or better error messages. See [file-formats](references/file-formats.md) and [reader workflow](references/workflows.md#choose-a-reader).
- **Create synthetic data**: use `mne.create_info()` plus `mne.io.RawArray(data, info)` with data shaped `(n_channels, n_times)` and MNE SI units. See [RawArray workflow](references/workflows.md#build-a-rawarray-from-numpy-data) and the bundled helper [create_synthetic_raw.py](scripts/create_synthetic_raw.py).
- **Inspect or subset a Raw object**: use `raw.info`, `raw.ch_names`, `raw.n_times`, `raw.times`, `raw.get_data()`, `raw.pick()`, `raw.drop_channels()`, `raw.reorder_channels()`, `raw.rename_channels()`, and `raw.set_channel_types()`. See [API reference](references/api-reference.md#core-objects-and-methods).
- **Manage memory**: default readers keep data on disk; use `preload=True`, `preload="path.dat"`, or `raw.load_data(memmap="path.dat")` only when operations require writable in-memory data. Crop and pick before preloading when possible. See [preload workflow](references/workflows.md#manage-preload-and-memory).
- **Annotate raw spans**: create `mne.Annotations`, call `raw.set_annotations()`, and remember that descriptions beginning with `BAD` are respected by many later processing functions. See [annotations workflow](references/workflows.md#add-raw-level-annotations).
- **Concatenate or save/export**: use `mne.io.concatenate_raws()` or `raw.append()` only for compatible recordings; save MNE-native work with `raw.save(...raw.fif)`, and use `raw.export()` for BrainVision, EDF, or EEGLAB only when optional exporters are installed. See [save/export workflow](references/workflows.md#save-and-export-boundaries).

## Boundaries

Route these tasks elsewhere in the MNE-Python skill graph:

- Events, `Epochs`, `Evoked`, filtering, artifact rejection, ICA/SSP, and cleaning decisions → `preprocessing-epochs-evoked`.
- Raw plotting, browser backends, topomaps, figures, and reports → `visualization-reporting`.
- Source estimates, BEM, forward/inverse, morphing, and labels → `source-modeling-inverse`.
- CLI commands, dataset download/cache helpers, configuration, logging, and `sys_info` → `cli-datasets-config`.

## Operating rules

- Prefer verified public APIs in [API reference](references/api-reference.md); do not instantiate `BaseRaw` directly except for type checks.
- Treat `Raw` methods as mostly in-place. Use `raw.copy()` before experimental channel picking, cropping, type changes, annotation replacement, concatenation, or filtering.
- Do not make generated guidance depend on original repository files, examples, tests, or local environments. Source evidence was distilled into this subtree; use bundled references and scripts only at runtime.
- For reader failures, first identify the file family, sidecars, optional dependencies, preload choice, units, channel names/types, and whether generic dispatch masked a more specific reader error. See [troubleshooting](references/troubleshooting.md).

# Visualization workflows

The runtime replacements are static and local. They intentionally do not ship
Jupyter notebooks, figures, or sample outputs.

## Saved prediction pickle

Set the experiment's test output directory before running a test. The saved
pickle has this schema:

```text
{
  "predictions": {trial_id: {chunk_id: tensor_or_array, ...}, ...},
  "labels":      {trial_id: {chunk_id: tensor_or_array, ...}, ...},
  "label_type":  "DiffNormalized" | "Raw" | "Standardized",
  "fs":          positive number
}
```

The trainer normally writes files named `<model-or-checkpoint>_outputs.pickle`
under `LOG.PATH/<test experiment>/saved_test_outputs`. A trial's chunks are
sorted by chunk key and concatenated. This is why the visualization helper can
plot a selected trial without knowing the model class. It accepts NumPy arrays,
Python sequences, and tensor-like values that expose `detach`, `cpu`, and
`numpy`; it does not import PyTorch.

Run:

```bash
python scripts/plot_saved_predictions.py --input result.pickle \
  --output figures/trial0.png --trial 0 --chunk-size 180 --chunk 0
```

`--trial` accepts a zero-based numeric index or an exact trial key. Use
`--list-trials` to inspect ids without creating an output file. `--chunk-size
-1` plots the complete selected trial; otherwise `--chunk` is zero-based. The
x-axis is seconds derived from the pickle's `fs`. By default the helper applies
the notebook-compatible signal transform: cumulative sum for
`DiffNormalized`, smooth detrending, and a 0.75--2.5 Hz first-order bandpass.
Use `--raw` to inspect the stored values without that transform. A constant
signal is plotted and warned about; an empty signal is rejected; a transformed
signal shorter than nine samples is rejected with a suggestion to use `--raw`.

The helper uses Matplotlib's `Agg` backend, creates parent directories, and
refuses to overwrite an existing file unless `--force` is present. PNG, SVG,
and PDF are suitable output formats. The plot labels prediction in red and
label in black and includes trial id, label type, and sampling rate in the
subtitle so a plot is not detached from its preprocessing context.

## Preprocessed arrays

Preprocessing cache directories conventionally contain paired files whose names
contain `input` and `label` plus a numeric chunk suffix, such as
`subject_input0.npy` and `subject_label0.npy`. The static replacement accepts
one pair explicitly:

```bash
python scripts/plot_preprocessed_arrays.py \
  --input cache/subject_input0.npy --label cache/subject_label0.npy \
  --output figures/cache_chunk.png --frame 0 --fs 30
```

Input arrays must be frame-first and have a last dimension of 3 or 6. For six
channels, the first three are the diff-normalized view and the last three are
RGB; the helper places them side by side. Three channels are shown directly.
The selected frame is checked against the frame count. The label plot contains
a time trace and a periodogram with its frequency axis limited to 0--5 Hz.
The source notebook chooses `diff_flag` by whether the dataset path contains
`DiffNormalized`, uses `fs=30`, detrending lambda 100, and the 0.75--2.5 Hz
bandpass. The CLI makes this explicit with `--diff-flag` or `--no-diff-flag`
instead of inferring semantics from an arbitrary path. Use `--no-filter` when
inspecting a short or unusual cache signal.

The cache schema itself belongs to [data-preparation](../../data-preparation/SKILL.md);
this document only explains how to inspect an already selected pair.

## Output and training plots

The toolbox also writes training/validation loss and learning-rate plots under
the experiment log when `PLOT_LOSSES_AND_LR=True`. This sub-skill does not
recreate those trainer plots. Keep their original experiment directory intact
and use the saved prediction helper for signal-level inspection. Bland--Altman
plot paths and names are specified in [evaluation-api.md](evaluation-api.md).

## What a useful inspection records

Record input pickle path, trial id, chunk range, `fs`, `label_type`, raw vs
processed choice, filter band, and output path. Compare waveform shape before
interpreting HR metrics. A visually good trace does not establish temporal HR
accuracy, and a high Pearson coefficient can coexist with a scale or phase
error; use the metric path for those claims.

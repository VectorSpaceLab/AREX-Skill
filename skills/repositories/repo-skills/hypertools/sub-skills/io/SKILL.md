---
name: io
description: "Resolve data sources, load and save HyperTools data, and open
  numeric LSL streams."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# IO

Use this route for `hyp.load`, `hyp.save`, `hypertools.io.sources`,
`hyp.io.lsl_stream`, and the streaming helpers that turn resolved input into a
form the visualization layer can consume.

## Use this sub-skill when the user wants to
- Load built-in datasets, local files, remote URLs, Hugging Face ids, Google
  Sheets/Drive links, Dropbox links, FiveThirtyEight datasets, or Kaggle
  datasets.
- Save arrays, DataFrames, lists of arrays, fitted models, and other
  serializable results to disk.
- Check how a string resolves to a dataset source, or why a source failed.
- Open a live numeric LSL stream for later plotting.
- Inspect or normalize stream rows with `hypertools.io.streaming.is_stream`
  and `row_to_vector`.

## Route elsewhere when the task is really about
- Plotting, animating, or exporting a figure/movie from loaded or streaming
  data: use `../visualization/`.
- Choosing, tuning, or reusing `reduce`/`align`/`normalize`/`ndims` stages
  after a load: use `../pipeline/`.
- Any model-selection or plotting-style work that does not start with source
  resolution or file/stream I/O.

## Read first
- `references/io-reference.md` for source precedence, file formats, trust
  rules, remote handling, and LSL semantics.
- `references/troubleshooting.md` for missing extras, unsupported extensions,
  pickle trust, and LSL/network failures.
- `scripts/smoke_io.py` to run a tiny local round-trip check; add
  `--lsl-local-smoke` when `pylsl` is installed and you want a real local
  outlet/inlet check.

## Fast routing guide
- Decide whether a string is a built-in name, local path, explicit prefix, or
  URL before doing anything else.
- If a remote payload is pickle-backed, require an explicit trust decision.
- If the extension is not a supported data format, expect pickle fallback
  unless the bytes clearly match a known binary format.
- If the input is an LSL outlet or stream generator, keep it numeric and hand
  the rendering step to the visualization route.
- If a raw string might be data or just text, use
  `hypertools.io.sources.is_loadable_string` before routing it.
- If `hyp.load(..., reduce=..., ndims=..., align=..., normalize=...)` is used
  on ordinary data, the pipeline owns those stage choices; streaming datasets
  reject those kwargs at load time.

## Success signals
- `hyp.load(...)` returns raw data, a DataFrame/array/list/dict, or a
  streaming `IterableDataset`.
- `hyp.save(...)` creates the requested file and round-trips through
  `hyp.load(...)`.
- `hyp.io.lsl_stream(...)` returns a generator of numeric vectors.
- The smoke script prints a round-trip success message and, when requested, a
  local LSL success message.

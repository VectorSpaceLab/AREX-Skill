# IO reference

This sub-skill covers source resolution, save/load format choice, trust
policy, remote data caveats, and numeric LSL stream resolution. If the task is
about plotting or visualizing the returned data, continue in `../visualization/`.
If the task is about choosing or reusing reduction/alignment stages after a
load, continue in `../pipeline/`.

## Verified signatures

- `hyp.load(dataset, reduce=None, ndims=None, align=None, normalize=None, *, legacy=False, split=None, streaming=False, trust=False)`
- `hyp.save(obj, fname, protocol=None)`
- `hyp.io.lsl_stream(name=None, type=None, timeout=10.0, **resolve_kwargs)`
- `hypertools.io.sources.is_loadable_string(s)` — cheap no-network check for
  whether a string looks like a data source.
- `hypertools.io.streaming.is_stream(x)`
- `hypertools.io.streaming.row_to_vector(row)`
- `hypertools.io.streaming.plot_stream(...)` — internal stream renderer used by
  `hyp.plot`; use the visualization route for rendering tasks.

## `hyp.load` in practice

Use `hypertools.io.sources.is_loadable_string(s)` as the cheap prefilter when
arbitrary user text might be a source string rather than plain text.

### Source precedence

A string is resolved in this order:

1. Built-in example dataset name.
2. Scikit-learn bundled dataset name (`iris`, `digits`, `wine`,
   `breast_cancer`, `diabetes`, `linnerud`).
3. Seaborn dataset name.
4. Explicit FiveThirtyEight prefix: `fivethirtyeight/<slug>`.
5. Explicit Kaggle prefix: `kaggle/<owner>/<dataset>`.
6. Local file path.
7. Hugging Face dataset id such as `scikit-learn/iris`.
8. Google Sheets URL.
9. Google Drive URL or bare file id.
10. Dropbox URL or shared-link path.
11. Any other URL, with or without `https://`.

Important precedence notes:

- Built-in example names win even if a scikit-learn or seaborn dataset uses the
  same name.
- Scikit-learn wins over seaborn for overlapping names like `iris`.
- Explicit `fivethirtyeight/` and `kaggle/` prefixes shadow same-named local
  paths; use `./` or an explicit file extension to force local-file lookup.
- Lists and tuples of strings are resolved element-wise and return a list of
  datasets.

### Built-in datasets

Built-ins are integrity-checked downloads, cached under `~/hypertools_data`,
and returned as raw data rather than `DataGeometry` objects.

Representative groups:

- Numeric example sets: `weights`, `weights_sample`, `weights_avg`, `spiral`.
- Text and corpus sets: `wiki`, `nips`, `sotus`.
- Shapes zoo: `bunny`, `cube`, `dragon`, `sphere`, `teapot`, `vase`,
  `biplane`.
- Multi-shape example: `datasaurus`.
- Pipeline pickles: `wiki_model`, `nips_model`, `sotus_model`.

Built-in data files are re-hosted in non-executable formats where possible; the
model artifacts remain pickle-backed but are hash-verified before unpickling.

### Load-time analysis kwargs

`reduce`, `ndims`, `align`, and `normalize` are forwarded into the analysis
pipeline for ordinary data. If the source is streaming, those kwargs are
rejected at load time. For stage selection, tuning, or reuse, route to
`../pipeline/`.

### Legacy mode

`legacy=True` is only for pre-1.0 deepdish/HDF5 `.geo` files. The loader returns
raw data, not `DataGeometry`, and the legacy path requires the separate
`deepdish` package in a `numpy<2` environment.

## File formats

### `hyp.save`

`hyp.save` chooses the output format from the filename extension:

| Extension | Saved as | Notes |
| --- | --- | --- |
| `.csv`, `.txt` | Delimited text | DataFrame-like input is written with `to_csv`. |
| `.tsv` | Tab-delimited text | Uses tab separators. |
| `.npy` | NumPy array | `np.save` of `np.asarray(obj)`. |
| `.npz` | NumPy archive | Lists/tuples become `arr_0`, `arr_1`, ...; dicts become keyed arrays. |
| `.json` | JSON table | Uses `DataFrame.to_json`. |
| `.parquet` | Parquet table | Column names are stringified on save; the runtime needs a parquet engine such as `pyarrow` or `fastparquet`. |
| `.mat` | MATLAB file | Arrays land in `data`; dicts become variables. |
| `.xlsx` | Excel workbook | Uses `openpyxl`. |
| anything else | Pickle | Includes `.pkl`, `.pickle`, `.p`, `.geo`, unknown extensions, and extensionless paths. |

Save behavior that matters in practice:

- `protocol=` is only valid for pickle output.
- Writes are atomic: a failed save does not clobber an existing file.
- Existing file mode is preserved; new files use the process umask.
- `~` and `$ENV_VARS` are expanded before writing.
- Non-DataFrame inputs aimed at text/table formats are converted through a
  DataFrame view first.
- `HyperAnimation` objects should be exported with `hyp.plot(..., save_path=...)`
  rather than `hyp.save(...)`.

### `hyp.load`

Local file loading accepts `.pkl`, `.pickle`, `.p`, `.geo`, `.npy`, `.npz`,
`.csv`, `.tsv`, `.txt`, `.json`, `.parquet`, `.mat`, `.xlsx`, `.xls`, and gzip
variants. If the bytes clearly match a recognized binary format, the loader may
still accept a file whose extension is otherwise unsupported; otherwise it
fails with a format-specific `HypertoolsIOError`.

A few useful load-side distinctions:

- Local pickle files are treated as trusted.
- Remote pickle files require `trust=True`.
- Remote `.npy` / `.npz` object arrays also require `trust=True`.
- Local `.npz` loads return a list of arrays, not a dict.
- A single-array `.npz` or `.mat` file may load back as an array rather than a
  container.
- Legacy `.geo` files saved by hypertools<0.8 are only handled through
  `legacy=True`.

## Trust and security

- Treat pickle as code execution, not as a data format.
- `trust=False` is the default for remote sources because a warning is not a
  security boundary.
- Pass `trust=True` only after verifying a remote source you control or trust.
- Prefer `.csv`, `.npz`, `.parquet`, or `.npy` for data exchange when possible.
- Parquet support also depends on an installed parquet engine (commonly `pyarrow`).
- Built-in example datasets are downloaded from fixed hosts and hash-verified;
  they do not require `trust=True`.

## Remote and network handling

### Google Drive, Sheets, and Dropbox

- Google Sheets URLs are rewritten to CSV export URLs.
- Google Drive large-file interstitials are followed automatically.
- Dropbox links are normalized to direct-download form (`dl=1`).

### FiveThirtyEight and Kaggle

- FiveThirtyEight datasets are listed via the GitHub contents API and fetched
  from raw GitHub or authenticated API endpoints when a token is present.
- Kaggle datasets use `kagglehub.dataset_download` and require the Kaggle extra.
- A malformed explicit prefix fails immediately instead of falling through to
  later resolvers.

### Transient network signals

Common transient markers in a failed load message include DNS failures, read
timeouts, 502/503/504 responses, connection resets, and rate-limit pages. These
usually mean retry later, not that the source name is wrong.

`hyp.load` returns a `HypertoolsIOError` with a `Tried, in order:` digest when
all resolvers fail. That digest is the primary clue for diagnosing a bad source
name versus a temporary outage.

## Streaming helpers and LSL

### `hypertools.io.streaming`

- `is_stream(x)` recognizes iterators/generators and Hugging Face
  `IterableDataset` objects.
- `row_to_vector(row)` converts a numeric sample or dict row to a 1-D float
  vector.
- `plot_stream(...)` is the internal renderer used by `hyp.plot` for stream
  inputs; keep rendering/animation work in the visualization route.

### `hyp.io.lsl_stream`

- `name=` wins over `type=`.
- Only numeric channel formats are supported.
- `timeout` bounds both initial resolution and mid-stream silence.
- Multiple matches produce a warning that names the chosen stream.
- `minimum=2` can be forwarded in `resolve_kwargs` when the caller wants
  stronger ambiguity detection.
- The result is an infinite generator of numeric vectors and is ready for the
  visualization route.

### Minimal usage pattern

```python
import hypertools as hyp

stream = hyp.io.lsl_stream(type='EEG', timeout=5.0)
# plotting belongs in ../visualization/; the stream itself is the IO result
```

## Validation commands

Use the bundled smoke helper for a quick local sanity check:

```bash
python scripts/smoke_io.py
python scripts/smoke_io.py --lsl-local-smoke
```

Expected outcome:

- The first command prints a local round-trip success line.
- The second command either prints a local LSL success line or a clear skip
  message if `pylsl` is absent.

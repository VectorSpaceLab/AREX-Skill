# IO troubleshooting

Use this page when `hyp.load`, `hyp.save`, or `hyp.io.lsl_stream` fails with an
import error, a trust error, a path/format error, or a network/LSL timeout.

## Missing extras and optional dependencies

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` mentioning `hypertools[text]` or `datasets` | Hugging Face dataset ids or `streaming=True` need the datasets stack | Install `pip install hypertools[text]` or `pip install datasets`. |
| `ImportError` mentioning `hypertools[io]` or `openpyxl` | `.xlsx` support is optional | Install `pip install hypertools[io]` or `pip install openpyxl`. |
| `ImportError` or `ValueError` from `to_parquet` / `read_parquet` | No parquet engine is installed | Install a parquet backend such as `pip install pyarrow`. |
| `ImportError: xlrd is required to load legacy .xls files` | You tried to read a legacy Excel file | Install `pip install xlrd` or convert the file to `.xlsx`. |
| `ImportError` mentioning `hypertools[kaggle]` or `kagglehub` | Kaggle dataset resolution is optional | Install `pip install hypertools[kaggle]`. |
| `ImportError` mentioning `hypertools[lsl]` or `pylsl` | LSL support is optional | Install `pip install hypertools[lsl]`. If the import still fails, check that the wheel/platform can access a native `liblsl` build. |

## Trust and pickle

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `HypertoolsTrustError: refusing to unpickle data fetched from a remote source` | Remote pickle was blocked on purpose | Pass `trust=True` only after verifying the source, or re-export the data in a non-executable format such as `.csv`, `.npz`, or `.parquet`. |
| `HypertoolsTrustError` about `allow_pickle=False` on a remote `.npy/.npz` | The remote array contains pickled objects | Re-save it in a non-object array format, or pass `trust=True` after source verification. |
| `This looks like a legacy (<1.0) deepdish/HDF5-format dataset` | You tried to read an old `.geo` file | Open it in a separate `numpy<2` environment with `deepdish`, then re-save it in a modern format. |
| `could not pickle ... object` | The object is not pickle-safe | Remove open file handles, lambdas, locally defined functions, or live animation callbacks; use `save_path=` for animations. |

## Path and format problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `cannot save to ... the parent directory ... does not exist` | The target folder has not been created | Create the directory first, then rerun `hyp.save`. |
| `cannot save to ... it is an existing directory` | You passed a directory instead of a file path | Pass a full file path such as `results.pkl`. |
| `hypertools.save: fname must be a string or path-like object` | The `obj`/`fname` arguments were swapped | Call `hyp.save(obj, fname)` in that order. |
| `unsupported file extension` | The file name does not end in a supported data extension | Rename the file to `.csv`, `.tsv`, `.txt`, `.npy`, `.npz`, `.json`, `.parquet`, `.mat`, `.xlsx`, or a pickle extension. |
| `reduce/ndims/align/normalize cannot be applied to a streaming dataset at load time` | You passed analysis kwargs to a stream source | Remove those kwargs from `hyp.load`; the returned stream goes to the visualization route, while stage selection belongs in `../pipeline/`. |
| `is empty (0 bytes)` | The source file is empty or a previous write failed midway | Recreate the file or rerun the producing step. |
| `could not create the example-dataset cache directory` or `hypertools cannot cache example datasets there` | The built-in cache path exists but is not a writable directory | Rename or delete the conflicting path (the cache lives under `~/hypertools_data`), then retry. |

## Remote and transient network failures

| Symptom fragment | Likely cause | Recovery |
| --- | --- | --- |
| `Tried, in order:` plus `ReadTimeout`, `NameResolutionError`, `Failed to resolve`, or `503`/`502`/`504` | Temporary network or host outage | Retry later, check local DNS/network, or test again outside the outage window. |
| `returned an HTML page instead of data` | A remote host served a permission page or rate-limit page instead of the file | Verify sharing/permissions, wait for the rate limit to reset, or retry from a different network. |
| `GitHub API ... failed with HTTP 403` and `rate limit` | Unauthenticated FiveThirtyEight listing hit GitHub's quota | Wait, or set `GITHUB_TOKEN` / `GH_TOKEN`. |
| `could not download '...dataset' via kagglehub` | Kaggle download failed or the dataset id is wrong | Verify the `kaggle/<owner>/<dataset>` spelling and the Kaggle extra. |

## LSL-specific failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `no LSL stream found` | No outlet is running, or `name=` / `type=` does not match | Start the outlet, verify the stream metadata, and increase `timeout` if discovery is slow. |
| `using the first one` warning | More than one stream matched | Pin the stream with `name=` or pass `minimum=2` in `resolve_kwargs` if you want the ambiguity to be explicit. |
| `has string-typed channels` or `Markers`-style rejection | The outlet is a marker/string stream, not numeric | Publish numeric channels for HyperTools, or convert the marker stream before plotting. |
| `stopped delivering samples` | The source disconnected or went silent after initial resolution | Restart the source, verify the network path, or raise `timeout` if the device is slow. |
| `timeout= must be a positive number of seconds` | Bad argument type or value | Pass a positive number and use strings for `name=` / `type=`. |

## Useful commands

```bash
python scripts/smoke_io.py
python scripts/smoke_io.py --lsl-local-smoke
pip install hypertools[io]
pip install hypertools[lsl]
pip install hypertools[text]
pip install hypertools[kaggle]
```

## When to escalate to another route

- If the issue is about choosing `reduce`/`align`/`normalize` or reusing a
  fitted pipeline, move to `../pipeline/`.
- If the issue is about drawing or saving a figure/movie, move to
  `../visualization/`.

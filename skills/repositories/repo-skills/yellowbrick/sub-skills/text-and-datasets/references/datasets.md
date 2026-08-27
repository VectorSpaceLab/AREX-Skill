# Yellowbrick datasets and corpus loading

Yellowbrick provides example datasets for documentation, examples, tests, and
quick visual diagnostics. The public API is in `yellowbrick.datasets`. Most
loaders return `X, y` by default; the hobbies text loader returns a `Corpus`
object. Dataset files live in a local cache and are downloaded only when a
loader or downloader decides the requested dataset directory is missing.

Use this reference before giving code that calls `load_*`, before explaining
`return_dataset=True`, and before advising users who are offline or changing
`YELLOWBRICK_DATA`.

## Loader catalog and task fit

| Loader | Data object | Verified shape or size | Typical task fit | Special notes |
|---|---|---:|---|---|
| `load_bikeshare(data_home=None, return_dataset=False)` | `Dataset` | `X=(17379, 12)`, `y=(17379,)` | regression | Bike-sharing demand data with integer/real-valued attributes. |
| `load_concrete(data_home=None, return_dataset=False)` | `Dataset` | `X=(1030, 8)`, `y=(1030,)` | regression | Compact numeric regression dataset. |
| `load_credit(data_home=None, return_dataset=False)` | `Dataset` | `X=(30000, 23)`, `y=(30000,)` | binary classification, clustering | Larger dataset; sample for fast demos or CI. |
| `load_energy(data_home=None, return_dataset=False)` | `Dataset` | `X=(768, 8)`, `y=(768,)` | regression, multi-output source examples | The source data contains heating/cooling targets; the default loader returns the documented primary target. |
| `load_game(data_home=None, return_dataset=False)` | `Dataset` | `X=(67557, 42)`, `y=(67557,)` | multiclass classification | Connect-4 categorical features usually need one-hot encoding or a preprocessing pipeline. |
| `load_hobbies(data_home=None)` | `Corpus` | `448` documents, `5` labels | text analysis, text classification, text clustering | Returns a `Corpus` object, not `X, y`, and does not accept `return_dataset=True`. |
| `load_mushroom(data_home=None, return_dataset=False)` | `Dataset` | `X=(8123, 3)`, `y=(8123,)` | binary classification, clustering | Categorical mushroom attributes usually need encoding. |
| `load_occupancy(data_home=None, return_dataset=False)` | `Dataset` | `X=(20560, 5)`, `y=(20560,)` | binary classification | Multivariate time-series-style occupancy measurements. |
| `load_spam(data_home=None, return_dataset=False)` | `Dataset` | `X=(4600, 57)`, `y=(4600,)` | binary classification, threshold analysis | Useful for discrimination-threshold and imbalance examples. |
| `load_walking(data_home=None, return_dataset=False)` | `Dataset` | `X=(149332, 4)`, `y=(149332,)` | clustering, time-series-style diagnostics, multilabel examples | Large row count; sample before expensive visualizers. |
| `load_nfl(data_home=None, return_dataset=False)` | `Dataset` | `X=(494, 23)`, `y=(494,)` | clustering | Football receiver clustering examples. |

The manifest-backed dataset names are: `bikeshare`, `concrete`, `credit`,
`energy`, `game`, `hobbies`, `mushroom`, `occupancy`, `spam`, `walking`, and
`nfl`.

## Tabular loader return rules

Calling a tabular loader without `return_dataset=True` returns two values:

```python
from yellowbrick.datasets import load_concrete

X, y = load_concrete()
```

Return type depends on whether `pandas` is importable in the current Python
environment:

- with `pandas`: `X` is a `pandas.DataFrame` and `y` is a `pandas.Series`;
- without `pandas`: `X` and `y` are `numpy.ndarray` objects.

This pandas/numpy switch is expected behavior. Do not report numpy output as a
loader failure when `pandas` is absent.

Pass `return_dataset=True` to a tabular loader when the user needs metadata,
cache contents, an explicit numpy conversion, or a full DataFrame:

```python
dataset = load_concrete(return_dataset=True)
X_np, y_np = dataset.to_numpy()
```

A `Dataset` object exposes:

- `to_data()` → `X, y` using pandas if available, otherwise numpy;
- `to_numpy()` → explicit numpy arrays from the cached `.npz` file;
- `to_pandas()` → explicit pandas `DataFrame`/`Series`, raising a dataset error
  if `pandas` is unavailable;
- `to_dataframe()` → the full cached CSV table as a pandas `DataFrame`;
- `contents()` → names of files in the cached dataset directory;
- `README`, `meta`, and `citation` → packaged provenance and metadata when the
  downloaded dataset includes those files.

`to_pandas()` and `to_dataframe()` require `pandas`. If the user wants code that
works in a minimum environment, prefer default `X, y` or `to_numpy()`.

## Corpus loader return rules

`load_hobbies(data_home=None)` returns a `Corpus` object directly:

```python
from yellowbrick.datasets import load_hobbies

corpus = load_hobbies()
docs = corpus.data
target = corpus.target
labels = corpus.labels
```

A `Corpus` exposes:

- `root` → local corpus root directory;
- `labels` → category directory names;
- `files` → paths for every document file;
- `data` → all document text loaded into memory as a list of strings;
- `target` → the label/category for each document;
- `contents()`, `README`, `meta`, and `citation` → cache contents and provenance
  metadata when present.

Use `corpus.files` for streaming or file-by-file workflows. Use `corpus.data`
and `corpus.target` when a scikit-learn vectorizer or Yellowbrick text
visualizer expects an in-memory corpus.

## Hobbies corpus layout

The hobbies corpus is a label-directory tree. Directory names are class labels;
text files inside each directory are documents.

```text
hobbies/
├── README.md
├── books/
│   ├── <document>.txt
│   └── <document>.txt
├── cinema/
├── cooking/
├── gaming/
└── sports/
```

The verified corpus size is five labels and 448 documents. Do not expect
`load_hobbies()` to return a feature matrix; vectorize `corpus.data` first when
using `FreqDistVisualizer`, `TSNEVisualizer`, or `UMAPVisualizer`.

## Cache location and `YELLOWBRICK_DATA`

Yellowbrick resolves the data cache in this order:

1. `data_home=` argument passed to a loader or helper;
2. `YELLOWBRICK_DATA` environment variable;
3. the package's default fixture/data directory.

The resolver expands `~` and environment variables. The public `get_data_home()`
helper creates the directory if it does not already exist. The bundled cache
inspector in this sub-skill intentionally resolves the same default location
without downloading, deleting, or creating dataset contents.

Each dataset normally has:

- an archive at `<data_home>/<name>.zip`;
- an extracted directory at `<data_home>/<name>/`;
- tabular files such as `<name>.csv.gz`, `<name>.npz`, `README.md`, and
  `meta.json` for `Dataset` loaders;
- corpus label directories and `.txt` documents for the hobbies `Corpus`.

## Download and offline behavior

Loader constructors check only whether the dataset directory exists. If the
requested directory is missing, the loader calls Yellowbrick's downloader. That
means:

- there is no `no_download` flag on `load_*` functions;
- calling `load_concrete()` or `load_hobbies()` while offline can still attempt
  network access if the selected cache is empty;
- a directory that exists but is incomplete may prevent download and then fail
  later when `.csv.gz`, `.npz`, `meta.json`, or corpus files are missing.

For no-network operation, first inspect or pre-populate the cache:

```bash
python skills/disco/yellowbrick/sub-skills/text-and-datasets/scripts/check_dataset_cache.py --data-home /path/to/cache --dataset concrete
```

The inspector is read-only: it never calls a loader, never downloads, and never
removes files. Treat a missing dataset directory as "the loader would try to
download" rather than as proof that the dataset does not exist upstream.

## Downloader CLI

The downloader module is run as:

```bash
python -m yellowbrick.download [--cleanup] [--no-download] [--overwrite] [data_home]
```

Verified flags:

- `--cleanup` / `-c`: remove existing cached datasets before any download step;
- `--no-download`: skip downloads, commonly paired with `--cleanup` when a user
  intentionally wants to clear local cached data;
- `--overwrite` / `-f`: replace existing archives/data during download;
- positional `data_home`: cache directory to operate on; otherwise the module
  follows `YELLOWBRICK_DATA` or the package default.

Only recommend downloader commands when the user explicitly wants network or
cleanup behavior. For agent-side validation and offline triage, use the bundled
cache inspector instead.

## Signature behavior

Manifest entries include a SHA-256 signature for each dataset archive. During a
real download, Yellowbrick hashes the downloaded archive and raises an error if
the signature does not match. The cache inspector reports archive signature state
without downloading:

- `signature-ok`: archive exists and matches the manifest signature;
- `signature-mismatch`: archive exists but does not match the expected hash;
- `missing`: archive is not present in the inspected cache;
- `error:<type>`: the archive exists but could not be read.

A signature mismatch is not fixed by changing model code. The user must choose a
trusted cache, remove/replace the bad archive, or rerun the downloader in an
environment where network access is intended.

## Loader-to-sub-skill routing after data is loaded

- After tabular classification data is loaded, route model diagnostics to
  classifier visualizers.
- After tabular regression data is loaded, route residual/prediction diagnostics
  to regressor visualizers.
- After clustering-oriented data is loaded, route elbow/silhouette/CV/model
  selection tasks to cluster/model-selection.
- After the hobbies corpus is loaded, stay in this sub-skill for text-specific
  visualizers; route downstream classifier/regressor/cluster work only after the
  corpus is vectorized and the user asks for model diagnostics.

# Dataset data formats and preprocessing contracts

Read this file before constructing a dataset object. The contracts below are
distilled from AIX360 0.3.0's dataset modules, package data notes, and tutorial
usage. They describe what the class consumes and returns; they do not authorize
redistribution of third-party data.

## Local tabular datasets

| Class | Local input | Preprocessing/output contract |
|---|---|---|
| `HELOCDataset` | `heloc_dataset.csv` under `dirpath`; raw target column `RiskPerformance` | `dataframe()` returns a copy of the raw frame with `RiskPerformance` last. `data()` is the callback result. `default_preprocessing` maps `-7/-8/-9` to `0`, removes rows whose feature values are all zero after that mapping, label-encodes `Good`/`Bad`, and returns a numeric `ndarray` with the encoded target last. `nan_preprocessing` retains missing sentinels as `NaN` after filtering and returns a frame with an encoded target. `split()` returns `(data, x_train, x_test, y_train_b, y_test_b)` using stratification and `random_state=0` by default. |
| `COMPASDataset` | `compas.csv` under `dirpath`; raw columns include `days_b_screening_arrest`, `is_recid`, `c_charge_degree`, `score_text`, `c_jail_in`, and `c_jail_out` | The default callback drops invalid screening/recidivism/charge/risk rows, parses jail dates, clips negative `time_served` to zero, and returns columns `Sex`, `Age_Cat`, `Race`, `C_Charge_Degree`, `Priors_Count`, `Time_Served`, `Status`. Use a callable callback; the class does not synthesize a target for you. |
| `AdultDataset` (direct module import) | `adult.csv` under `dirpath`, read as whitespace-delimited and headerless | The default callback expects the raw positional Adult/Census layout, removes two redundant positions, drops missing `?,` rows, strips trailing commas, encodes `<=50K`/`>50K` to `0/1`, casts numeric fields to integers, and returns a cleaned `DataFrame`. This class is not exported by `aix360.datasets` in this release. |
| `MEPSDataset` | `h181.csv` under `dirpath` | The default callback filters to `RACEV2X` values `1/2` and non-Hispanic `HISPANX == 2`, renames fields to `RACE3`, `GENDER`, `REGION`, `INCOME_M`, `HEALTHEXP`, and `PERSONWT`, removes invalid negative values, keeps the documented demographic/health/economic columns, and returns a `DataFrame`. Read the MEPS codebook before interpreting codes. |
| `TEDDataset` | `Retention.csv` or another CSV under `dirpath` | `load_file(fileName)` treats all columns except the last two as `X`, requires columns named `Y` and `E`, and returns `(X, Y, E)` as pandas objects. `Y` is intended to be binary; `E` is intended to be a dense integer explanation id range. |

For HELOC and COMPAS, `custom_preprocessing=None` leaves no processed data
attribute; use the default or an explicit callback. Preserve a copy of raw
labels before applying an in-place dataframe operation. For MEPS, validate the
actual dtypes of code columns after parsing because the source callback mixes
string filters with numeric replacement maps.

## Local image and text layouts

- `MNISTDataset(dirpath=...)` requires four gzip files: `train-images-idx3-
  ubyte.gz`, `t10k-images-idx3-ubyte.gz`, `train-labels-idx1-ubyte.gz`, and
  `t10k-labels-idx1-ubyte.gz`. It reads 60,000 training images and 10,000 test
  images, scales pixels to `float32` in `[-0.5, 0.5]`, reshapes images to
  `(n, 28, 28, 1)`, one-hot encodes labels to `(n, 10)`, and splits the first
  5,000 training rows into validation data. Missing files trigger download.
- `FMnistDataset` uses a torchvision `FashionMNIST` cache rooted at
  `dirpath`, with `ToTensor()`, a random training subset of `subset_size`
  (default 50,000), and loaders. `next_batch()` and `next_test_batch()` yield
  image arrays reshaped to `(batch, 28, 28, 1)` plus integer labels. Pixels are
  in `[0, 1]`; metadata reports `data_dims=[28,28,1]` and `range=[0.0,1.0]`.
  The implementation uses `download=True` and requires `torch` and
  `torchvision`; it is not an offline constructor unless the cache is complete.
- `CIFARDataset(dirpath=...)` consumes or creates six processed JSON files:
  `cifar-10-train1-image.json`, `cifar-10-train2-image.json`,
  `cifar-10-test-image.json`, and the corresponding `*-label.json` files.
  Images are `uint8`-like arrays shaped `(n,32,32,3)`; labels are dense
  one-hot arrays shaped `(n,10)`. The training partition is 30,000 plus
  20,000 rows and test is 10,000. If the first processed image file is absent,
  the constructor downloads and verifies a pinned CIFAR archive, unpacks it,
  writes JSON, and removes temporary extracted data.
- `CelebADataset(dirpath=...)` is local-only at the API level. For an id `k`,
  `get_img(k)` reads `k_img.npy`; `get_latent(k)` reads `k_latent.npy` and casts
  to `float32`. The image and latent files must be paired and generated data
  must match the consuming explainer's expected scale.
- `eSNLIDataset()` reads a JSONL file named `docs.jsonl` from its fixed package
  data location. `get_example(example_id)` scans records until a matching
  `docid` and returns that record as a dictionary; a missing id raises
  `RuntimeError`. The constructor has no local-path argument, so use a prepared
  package-data location or a separate adapter rather than assuming `dirpath`
  works.

## Time-series and survey layouts

- `FordDataset(url=None, category_a=True)` expects whitespace-delimited
  `FordA_TRAIN.txt` and `FordA_TEST.txt` in its fixed data directory. Each row
  has a label followed by 500 values. `load_data()` returns
  `(x_train, x_test, y_train, y_test)`, with `x_*` shaped `(n,500,1)` and labels
  converted from `-1` to `0`. The class downloads a ZIP when its train file is
  missing; the current implementation's fixed filenames should be checked
  carefully before selecting category B.
- `SunspotDataset(url=None)` reads a cached CSV and returns `(df, schema)`.
  The dataframe columns are `month` and `sunspots`; the schema names the
  timestamp `month`, target `sunspots`, frequency `M`, and no external
  regressors. The constructor downloads the source CSV if the cache is absent.
- `ClimateDataset(url=None)` reads `jena_climate_2009_2016.csv` from its fixed
  package data directory. It selects seven features, normalizes using training
  means and standard deviations, samples every six ten-minute records, and
  creates 120-step windows with a 12-hour forecast offset. `load_data()` returns
  a dictionary with `df`, selected column/name lists, `sequence_length=120`,
  `x_test`, `y_test`, and optional `x_train`, `y_train`. It needs TensorFlow's
  `timeseries_dataset_from_array`; the constructor downloads a ZIP if absent.
- `CDCDataset(dirpath=...)` expects NHANES questionnaire XPT files in the
  chosen directory and converts them into `csv/*.csv`. `get_csv_file(name)`
  returns a pandas frame; `get_csv_file_names()` returns the generated CSV
  names. The constructor downloads every missing XPT and imports `xport`, so
  a no-network run must validate files without constructing the class.

The packaged data tree contains the TED `Retention.csv` fixture, but the
benchmark directories are otherwise not a guarantee that data has been
shipped. Treat an empty package data directory as a missing-data condition, not
as a reason to invoke a hidden download.

## Acquisition and licensing boundary

Public sources have different terms and access paths: FICO HELOC may require a
community form; MEPS has an AHRQ data-use agreement; CDC/NHANES, UCI Adult,
CIFAR-10, MNIST, Fashion-MNIST, CelebA, e-SNLI, UCR Ford, climate, and sunspot
sources each have their own attribution or usage conditions. Confirm the
current source terms and retain provenance separately. This skill intentionally
bundles no downloader and does not reproduce restricted datasets.

# Data-loading reference

This reference captures the Surprise data APIs needed to load ratings, inspect `Trainset` objects, and diagnose local data layout issues without reopening the source repository.

## Core objects

- `Reader`: parser configuration for file-based ratings and the holder of `rating_scale` for all dataset constructors.
- `Dataset`: factory namespace. Do not instantiate directly; use the class methods below.
- `DatasetAutoFolds`: returned by `load_builtin`, `load_from_file`, and `load_from_df`; exposes `raw_ratings` and `build_full_trainset()`.
- `DatasetUserFolds`: returned by `load_from_folds`; stores predefined fold file pairs and is consumed by `PredefinedKFold`.
- `Trainset`: integer-id training representation produced from raw ratings.

## Reader rules

Constructor:

```python
from surprise import Reader

reader = Reader(
    name=None,
    line_format="user item rating timestamp",
    sep="\t",
    rating_scale=(1, 5),
    skip_lines=0,
)
```

Rules:

- `name` may be `"ml-100k"`, `"ml-1m"`, or `"jester"`. When `name` is provided, built-in reader parameters are used and other parser arguments are ignored.
- `line_format` is always a space-separated list of field names. Valid tokens are `user`, `item`, `rating`, and optional `timestamp`. It must include `user`, `item`, and `rating` exactly once.
- `sep` is the actual delimiter used to split each input line. Use `None` for whitespace splitting, `"\t"` for tab-separated MovieLens-100k style data, and `"::"` for MovieLens-1M style data.
- `skip_lines` drops leading lines when reading files; use it for headers. It does not affect dataframe loading.
- `parse_line()` strips parsed fields and casts ratings with `float(rating)`. A malformed line or bad `line_format`/`sep` raises `ValueError`; a nonnumeric rating also fails during float conversion.
- Reader parsing is simple delimiter splitting, not a full CSV parser. Pre-clean quoted/escaped CSVs before giving them to Surprise.

## Dataset constructors

### Built-in datasets

```python
from surprise import Dataset

data = Dataset.load_builtin("ml-100k", prompt=True)
```

Accepted names and parser defaults:

| Name | Expected cached ratings file under the data folder | Reader parameters |
| --- | --- | --- |
| `ml-100k` | `ml-100k/ml-100k/u.data` | `line_format="user item rating timestamp"`, `sep="\t"`, `rating_scale=(1, 5)` |
| `ml-1m` | `ml-1m/ml-1m/ratings.dat` | `line_format="user item rating timestamp"`, `sep="::"`, `rating_scale=(1, 5)` |
| `jester` | `jester/jester_ratings.dat` | `line_format="user item rating"`, `sep=None`, `rating_scale=(-10, 10)` |

Cache behavior:

- `get_dataset_dir()` returns the folder used for built-in downloads and creates it if needed.
- The default folder is `~/.surprise_data/`.
- Set `SURPRISE_DATA_FOLDER` to choose another folder. Set it before importing Surprise in a process if built-in dataset paths must use the custom location.
- If the cached ratings file is absent, `load_builtin(..., prompt=True)` asks before downloading. In non-interactive contexts this can block; use local files/dataframes/folds or pre-stage the cache instead. `prompt=False` skips the question and proceeds with download.
- Built-in loading is not a safe offline smoke unless the cache is already present.

### Single custom file

Layout example:

```text
user_id;item_id;rating;timestamp
u1;i1;4;1111111111
u1;i2;0;1111111112
u2;i1;2.5;1111111113
```

Code:

```python
from surprise import Dataset, Reader

reader = Reader(
    line_format="user item rating timestamp",
    sep=";",
    rating_scale=(0, 5),
    skip_lines=1,
)
data = Dataset.load_from_file("ratings.csv", reader=reader)
trainset = data.build_full_trainset()
```

Notes:

- `load_from_file()` reads immediately and stores `data.raw_ratings` as `(raw_user, raw_item, rating_float, timestamp_or_None)`.
- `~` in paths is expanded. A missing file raises the normal file-open error.
- `DatasetAutoFolds.build_full_trainset()` constructs one `Trainset` from every raw rating in the file.

### Pandas dataframe

```python
from surprise import Dataset, Reader

reader = Reader(rating_scale=(-10, 10))
data = Dataset.load_from_df(df[["user_id", "item_id", "rating"]], reader)
trainset = data.build_full_trainset()
```

Rules:

- Pandas is required by your code path, not by the `Reader` itself.
- Surprise ignores dataframe column names. The selected dataframe must have exactly the semantic order user raw id, item raw id, rating.
- For dataframe loading, only `rating_scale` is needed on the reader; `line_format`, `sep`, and `skip_lines` are irrelevant.
- Raw id Python types are preserved from the dataframe where possible. If a raw user id is the integer `9`, `trainset.to_inner_uid(9)` is the safe lookup; the string `"9"` is a different raw id unless your dataframe used strings.

### Predefined folds

Folder layout example:

```text
folds/
  fold1.train
  fold1.test
  fold2.train
  fold2.test
```

Code:

```python
from surprise import Dataset, Reader
from surprise.model_selection import PredefinedKFold

reader = Reader(line_format="user item rating timestamp", sep="\t", rating_scale=(1, 5))
folds_files = [
    ("folds/fold1.train", "folds/fold1.test"),
    ("folds/fold2.train", "folds/fold2.test"),
]
data = Dataset.load_from_folds(folds_files, reader=reader)

for trainset, testset in PredefinedKFold().split(data):
    assert trainset.n_ratings > 0
    assert all(len(row) == 3 for row in testset)  # raw uid, raw iid, true rating
```

Rules:

- `folds_files` must be an iterable of `(train_file, test_file)` tuples. Even for one train/test pair, pass a list with one tuple.
- Every path is checked when calling `load_from_folds()`. A missing path raises `ValueError` before iteration.
- The train file becomes a `Trainset`; the test file becomes a raw-id testset list with timestamps discarded.
- Use `PredefinedKFold` only to materialize these fold pairs here. Metric orchestration and repeated CV choices belong to the evaluation/search sub-skill.

## Trainset inspection and id conversion

A `Trainset` is not raw input data. It maps raw user/item ids to dense integer inner ids and stores ratings in two dictionaries:

- `trainset.ur[inner_uid] -> [(inner_iid, rating), ...]`
- `trainset.ir[inner_iid] -> [(inner_uid, rating), ...]`

Useful attributes:

- `n_users`, `n_items`, `n_ratings`
- `rating_scale`
- `global_mean`

Useful methods:

| Method | Input id type | Output / behavior |
| --- | --- | --- |
| `to_inner_uid(raw_uid)` | raw user id | Inner user id, or `ValueError` if absent from this trainset. |
| `to_inner_iid(raw_iid)` | raw item id | Inner item id, or `ValueError` if absent from this trainset. |
| `to_raw_uid(inner_uid)` | inner user id | Raw user id, or `ValueError` if the inner id is invalid. |
| `to_raw_iid(inner_iid)` | inner item id | Raw item id, or `ValueError` if the inner id is invalid. |
| `knows_user(inner_uid)` | inner user id | `True` if that inner user is represented in `ur`. |
| `knows_item(inner_iid)` | inner item id | `True` if that inner item is represented in `ir`. |
| `all_users()` / `all_items()` | none | Ranges of inner ids. |
| `all_ratings()` | none | Generator of `(inner_uid, inner_iid, rating)`. |
| `build_testset()` | none | Raw-id `(uid, iid, rating)` triples for all observed ratings in the trainset. |
| `build_anti_testset(fill=None)` | optional fill rating | Raw-id triples for known user/item pairs absent from the trainset; `fill=None` uses `global_mean`. |

Raw-vs-inner rules:

- Raw ids are the ids in the ratings file or dataframe.
- File-loaded raw ids are strings, even when they look numeric.
- Dataframe-loaded raw ids keep the dataframe values; numeric and string ids are distinct.
- Inner ids are dense integers created separately for each `Trainset`. Do not persist or compare inner ids across different splits.
- Public prediction/testset APIs generally expect raw ids. `Trainset` internals and `knows_*` methods expect inner ids.

## Zero and negative ratings

Surprise stores ratings in `ur`/`ir` list structures, so zero ratings are not treated as missing values by the data layer. The reader casts ratings to floats and does not remap zero or negative values. For data such as Jester, use a reader with `rating_scale=(-10, 10)` and verify with `all_ratings()` that values such as `0`, `-5`, and `-10` are preserved.

`build_anti_testset(fill=...)` may use fills such as `0`, `-1`, or any float; with `fill=None`, it uses `trainset.global_mean`.

## Validation anchors for future verification

- Native candidates: `tests/test_reader.py`, `tests/test_dataset.py`, and `tests/test_zero_ratings.py`.
- Bundled smoke scripts in `scripts/` cover local file loading, dataframe loading, predefined folds, malformed separators, dataframe ordering mistakes, nonexistent folds, id conversion, and zero-rating preservation.

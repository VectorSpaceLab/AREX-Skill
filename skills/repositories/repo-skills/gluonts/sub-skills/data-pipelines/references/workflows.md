# Data-pipeline workflows

These recipes are checkout-independent and assume `gluonts` is installed in the active Python environment.

## PandasDataset recipes

### Single time series from a dataframe

```python
import numpy as np
import pandas as pd
from gluonts.dataset.pandas import PandasDataset

idx = pd.period_range("2024-01-01", periods=24, freq="D")
df = pd.DataFrame(
    {
        "target": np.arange(24, dtype="float32"),
        "known_cov": np.linspace(0.0, 1.0, 24, dtype="float32"),
    },
    index=idx,
)

dataset = PandasDataset(df, target="target", feat_dynamic_real=["known_cov"])
entry = next(iter(dataset))
assert entry["start"] == idx[0]
assert entry["target"].shape == (24,)
assert entry["feat_dynamic_real"].shape == (1, 24)
```

Use a `PeriodIndex` when possible. If the dataframe has a `DatetimeIndex`, pass `freq` when pandas cannot infer frequency reliably:

```python
dataset = PandasDataset(df_with_datetime_index, target="target", freq="H")
```

### Multiple series

Use a dictionary when item ids matter:

```python
frames = {
    "store-a": pd.DataFrame({"target": [1, 2, 3]}, index=pd.period_range("2024-01-01", periods=3, freq="D")),
    "store-b": pd.DataFrame({"target": [4, 5, 6]}, index=pd.period_range("2024-01-01", periods=3, freq="D")),
}
static = pd.DataFrame(
    {"region": pd.Series(["north", "south"], dtype="category"), "scale": [1.0, 2.0]},
    index=["store-a", "store-b"],
)

dataset = PandasDataset(frames, target="target", static_features=static)
entries = list(dataset)
assert {entry["item_id"] for entry in entries} == {"store-a", "store-b"}
```

Use a list or list of `(item_id, dataframe)` pairs when order must be explicit.

## Long dataframe recipe

Use this when a single table contains several items:

```python
import pandas as pd
from gluonts.dataset.pandas import PandasDataset

rows = pd.DataFrame(
    {
        "timestamp": list(pd.date_range("2024-01-01", periods=4, freq="D")) * 2,
        "item_id": ["a"] * 4 + ["b"] * 4,
        "target": [1, 2, 3, 4, 10, 11, 12, 13],
        "price": [0.1, 0.2, 0.3, 0.4] * 2,
        "segment": pd.Series(["x"] * 4 + ["y"] * 4, dtype="category"),
    }
)

dataset = PandasDataset.from_long_dataframe(
    rows,
    item_id="item_id",
    timestamp="timestamp",
    target="target",
    freq="D",
    feat_dynamic_real=["price"],
    static_feature_columns=["segment"],
)
```

Validation checklist before passing a long dataframe to GluonTS:

1. Each item has exactly one observation per period after sorting, or gaps have been resampled/filled intentionally.
2. Static columns are constant per item; changing covariates belong in `feat_dynamic_real` or `past_feat_dynamic_real`.
3. Categorical static columns use pandas `category` dtype, not object/string dtype.
4. `timestamp` and `freq` describe the same granularity.
5. For very large tables, account for the grouping/caching work performed during construction.

## ListDataset quick recipe

```python
from gluonts.dataset.common import ListDataset

records = [
    {"start": "2024-01-01", "target": [1.0, 2.0, 3.0], "feat_static_cat": [0]},
    {"start": "2024-01-01", "target": [4.0, 5.0, 6.0], "feat_static_cat": [1]},
]

dataset = ListDataset(records, freq="D")
assert dataset[0]["start"].freqstr == "D"
```

For multivariate targets shaped `(target_dim, T)`, set `one_dim_target=False`:

```python
records = [{"start": "2024-01-01", "target": [[1, 2, 3], [10, 20, 30]]}]
dataset = ListDataset(records, freq="D", one_dim_target=False)
```

## File-backed datasets

### JSON Lines

```python
from pathlib import Path
from gluonts.dataset.common import FileDataset
from gluonts.dataset.jsonl import JsonLinesWriter

entries = [
    {"start": "2024-01-01", "target": [1.0, 2.0, 3.0]},
    {"start": "2024-01-02", "target": [4.0, 5.0, 6.0]},
]
out_dir = Path("dataset-jsonl")
out_dir.mkdir(exist_ok=True)
JsonLinesWriter(use_gzip=False).write_to_file(entries, out_dir / "data.jsonl")

dataset = FileDataset(out_dir, freq="D")
assert len(list(dataset)) == 2
```

Use `.json.gz` or `.jsonl.gz` when compressed JSON Lines are desired. Keep one complete JSON object per line.

### Optional Arrow or Parquet

Guard Arrow paths because `pyarrow` is optional:

```python
try:
    from gluonts.dataset.arrow import ParquetWriter
except ImportError:
    ParquetWriter = None

if ParquetWriter is not None:
    ParquetWriter(metadata={"freq": "D"}).write_to_file(entries, Path("data.parquet"))
```

`FileDataset` can infer Arrow/Parquet files only when the optional Arrow module is importable. For portability, JSON Lines is the safer exchange format.

## Splitting datasets

Import:

```python
from gluonts.dataset.split import split
```

`split(dataset, offset=...)` and `split(dataset, date=...)` return `(training_dataset, test_template)`. Provide exactly one of `offset` or `date`.

### Offset split

Offsets slice each entry by integer position:

- `offset=20`: first 20 observations are training history.
- `offset=-prediction_length`: all but the trailing prediction horizon are training history.
- For several trailing non-overlapping windows, choose an earlier split, e.g. `offset=-(prediction_length * windows)`.

```python
prediction_length = 7
training_data, test_template = split(dataset, offset=-prediction_length)
test_data = test_template.generate_instances(prediction_length=prediction_length)

for input_entry, label_entry in test_data:
    assert label_entry["target"].shape[-1] == prediction_length
    assert label_entry["start"] == input_entry["start"] + input_entry["target"].shape[-1]
```

### Date split

Use a `pandas.Period` with the same frequency as the entries:

```python
import pandas as pd

training_data, test_template = split(
    dataset,
    date=pd.Period("2024-02-01", freq="D"),
)
```

Date-based training includes observations up to and including the provided period. The first label starts immediately after the generated input history.

### TestTemplate.generate_instances

```python
test_data = test_template.generate_instances(
    prediction_length=prediction_length,
    windows=3,
    distance=prediction_length,  # default; non-overlapping windows
    max_history=90,              # optional input-context cap
)
```

Behavior to rely on:

- The returned `TestData` is iterable over `(input_entry, label_entry)` pairs.
- `test_data.input` iterates only model inputs; `test_data.label` iterates labels.
- `len(test_data) == len(dataset) * windows`.
- If `distance` is omitted, windows are spaced by `prediction_length` and do not overlap.
- Smaller `distance` creates overlapping forecast windows; larger `distance` skips ahead.
- `max_history` truncates only the input history, preserving the label horizon.
- Known dynamic features (`feat_dynamic_real`/`feat_dynamic_cat`) are extended on input entries through `prediction_length`; past-only dynamic features are not extended beyond the input slice.

## Zebras workflow notes

Use `gluonts.zebras` only when a pipeline explicitly wants GluonTS time-frame objects rather than model-ready `Dataset` entries:

```python
from gluonts import zebras as zb

ts = zb.time_series([1.0, 2.0, 3.0], start="2024-01-01", freq="D")
frame = zb.time_frame({"target": ts.values}, start="2024-01-01", freq="D")
pairs = list(frame.rolsplit(index=-1, future_length=1, n=1))
```

`zebras.schema.Schema` can validate dictionaries into `TimeFrame` or `SplitFrame` objects with required/static/time-series fields. For standard GluonTS estimators and evaluators, convert or construct ordinary `Dataset` entries instead.

## Run the bundled smoke test

From the generated skill root or any copied runtime tree:

```bash
python sub-skills/data-pipelines/scripts/dataset_split_smoke.py
```

Expected output is a single success line that reports the number of entries, prediction length, training target length, and label start. Use `--help` to inspect the deterministic options.

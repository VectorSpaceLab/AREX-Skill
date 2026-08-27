# Dataset Utilities

## Public APIs

```python
sns.load_dataset(name, cache=True, data_home=None, **kws)
sns.get_dataset_names()
sns.get_data_home(data_home=None)
```

## Behavior

- `load_dataset` loads CSV files from the online seaborn-data repository and optionally caches them.
- `get_dataset_names` reads the online dataset name list and requires network.
- `get_data_home` returns and creates a cache directory; `SEABORN_DATA` overrides the default when `data_home` is not passed.
- Extra keyword arguments to `load_dataset` pass through to `pandas.read_csv`.
- Some example datasets receive categorical preprocessing after loading.

## Use Cases

Use dataset utilities for documentation examples, reproducible bug reports, or quick teaching demos. Do not route a user's local data through `load_dataset`; pass their DataFrame directly to plotting functions.

## Offline Alternatives

For reusable scripts and tests, generate small synthetic DataFrames with NumPy/pandas or read a local CSV. This avoids network flakiness and makes examples self-contained.

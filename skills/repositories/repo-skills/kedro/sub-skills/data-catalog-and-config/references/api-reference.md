# API Reference

This reference covers Kedro 1.4.0 catalog and configuration APIs for agents working without reopening the source repository.

## Core Catalog APIs

```python
from kedro.io import DataCatalog, MemoryDataset

catalog = DataCatalog(datasets={"example": MemoryDataset(data=[1, 2, 3])})
assert "example" in catalog
catalog.save("example", [4, 5])
value = catalog.load("example")
```

- `DataCatalog(datasets=None, config_resolver=None, load_versions=None, save_version=None)` stores concrete datasets and lazy datasets resolved from configuration.
- `DataCatalog.from_config(catalog, credentials=None, load_versions=None, save_version=None)` is the normal factory for `catalog.yml` dictionaries.
- `DataCatalog.from_config()` accepts a catalog mapping of dataset names to configuration dictionaries and an optional credentials mapping; it returns a catalog whose configured datasets are lazily materialized on first access.
- `catalog[dataset_name]` returns a dataset or raises `DatasetNotFoundError`; `catalog.get(dataset_name)` returns `None` if no explicit, dataset-pattern, or catch-all match exists.
- `catalog.get(dataset_name, fallback_to_runtime_pattern=True)` can use the runtime fallback pattern to create a `MemoryDataset`; regular project runs usually enable runtime fallbacks for intermediate datasets automatically.
- `catalog.load(name, version=None)` loads a registered dataset; the `version` argument applies only to versioned datasets.
- `catalog.save(name, data)` saves through the configured dataset and rejects `None` through the dataset wrapper.
- `catalog.exists(name)` returns the dataset `exists()` result or `False` if the dataset is not present.
- `catalog.release(name)` clears cached data for a dataset that implements release behavior.
- `catalog.confirm(name)` calls the dataset's `confirm()` method when available and raises `DatasetError` otherwise.
- `catalog.keys()`, `values()`, `items()`, `len(catalog)`, and iteration work for registered dataset names; `DataCatalog` is not a full mutable dictionary and does not support every dictionary method.
- `catalog.filter(name_regex=None, type_regex=None, by_type=None)` returns dataset names matching a name regex, type-string regex, exact dataset class, or list of dataset classes.
- `catalog.get_type(name)` returns the fully qualified dataset type without materializing a matching lazy/factory dataset when possible.
- `catalog.to_config()` serializes non-memory datasets back into `(catalog_config, credentials, load_versions, save_version)` when constructor arguments are static and serializable.

## Dataset Configuration Resolution

```python
config = {
    "companies": {
        "type": "pandas.CSVDataset",
        "filepath": "data/01_raw/companies.csv",
        "credentials": "dev_s3",
        "save_args": {"index": False},
    }
}
credentials = {"dev_s3": {"key": "...", "secret": "..."}}
catalog = DataCatalog.from_config(config, credentials=credentials)
print(catalog.keys())
```

- Every concrete catalog entry must be a dictionary with a `type` key unless it is a private interpolation helper key beginning with `_` in config-loader output.
- Dataset type resolution tries `kedro.io.<type>`, then `kedro_datasets.<type>`, then the fully qualified path supplied in `type`.
- Short core types such as `MemoryDataset` resolve from `kedro.io`; common persisted types such as `pandas.CSVDataset` require the separate `kedro-datasets` package and any storage-specific dependencies.
- `kedro-datasets` 2.x and later spell dataset class names with lowercase `s` in `Dataset`, for example `CSVDataset`, not the stale `CSVDataSet` spelling.
- A `type` value that starts or ends with `.` is invalid; use an importable fully qualified class path for custom datasets.
- The resolved class must subclass `kedro.io.AbstractDataset`, otherwise Kedro raises `DatasetError`.
- Constructor arguments in YAML must match the dataset class constructor; unexpected keys raise `DatasetError` with a message naming the target constructor.
- Credentials are resolved recursively: whenever a key named `credentials` has a string value, Kedro replaces it with `credentials[string_value]` from the credentials mapping.
- Missing credential references raise a clear error like `Unable to find credentials '<name>'`; do not print the credentials mapping while debugging.

## Dataset Base Classes

```python
from pathlib import Path, PurePosixPath
from typing import Any
from kedro.io import AbstractDataset, DatasetError

class TextDataset(AbstractDataset[str, str]):
    def __init__(self, filepath: str, metadata: dict[str, Any] | None = None):
        self._filepath = PurePosixPath(filepath)
        self.metadata = metadata

    def load(self) -> str:
        return Path(self._filepath.as_posix()).read_text(encoding="utf-8")

    def save(self, data: str) -> None:
        Path(self._filepath.as_posix()).write_text(data, encoding="utf-8")

    def _exists(self) -> bool:
        return Path(self._filepath.as_posix()).exists()

    def _describe(self) -> dict[str, Any]:
        return {"filepath": self._filepath.as_posix()}
```

- Extend `AbstractDataset[InputType, OutputType]` for a custom dataset and implement `load()`, `save()`, `_exists()`, and `_describe()` or the corresponding `_load()` and `_save()` forms used by the wrapper.
- Dataset `load()` and `save()` are wrapped to add logging and convert most underlying failures into `DatasetError`.
- Saving `None` is not allowed and raises `DatasetError`.
- Set `_EPHEMERAL = True` for non-persistent datasets.
- Set `_SINGLE_PROCESS = True` for custom datasets that cannot be pickled or used safely with multiprocessing; `CachedDataset` does this.
- Keep arbitrary `metadata` on datasets only for user/plugin consumption; Kedro ignores it for I/O behavior.

## Memory, Cached, And Shared-Memory Datasets

- `MemoryDataset(data=<sentinel>, copy_mode=None, metadata=None)` stores a Python object in memory and is non-persistent.
- `MemoryDataset.load()` raises `DatasetError` if no data has been saved yet.
- `MemoryDataset` infers copy mode: pandas DataFrames and NumPy arrays usually use `copy`, Ibis-like frames use `assign`, and other objects use `deepcopy`; explicit copy modes are `deepcopy`, `copy`, and `assign`.
- Raw data assigned with `catalog["name"] = some_object` is automatically wrapped in a `MemoryDataset`.
- `CachedDataset(dataset, version=None, copy_mode=None, metadata=None)` wraps a real dataset and an in-memory cache; in YAML, put `versioned: true` on the `CachedDataset` wrapper, not inside the nested `dataset` config.
- `CachedDataset` has `_SINGLE_PROCESS = True`; avoid it with `ParallelRunner` and prefer `ThreadRunner` or `SequentialRunner` when cache behavior is needed.
- `SharedMemoryDataset(manager=None)` is used by shared-memory catalog behavior for multiprocessing; non-serializable data saved into it raises a serialization-focused `DatasetError`.

## Versioning APIs

```python
from kedro.io import DataCatalog, Version
from kedro_datasets.pandas import CSVDataset

dataset = CSVDataset(
    filepath="data/01_raw/input.csv",
    version=Version(load=None, save=None),
)
catalog = DataCatalog({"input": dataset})
```

- `AbstractVersionedDataset(filepath, version, exists_function=None, glob_function=None)` is the base for versioned implementations.
- The public `Version(load, save)` tuple controls load and save versions; `None` load means latest available, and `None` save means generate a timestamp.
- In YAML, enable versioning with `versioned: true`; Kedro converts this into a `Version(load_version, save_version)` passed to the dataset constructor.
- `DataCatalog.from_config(..., load_versions={"dataset": "exact-version"}, save_version="run-save-version")` pins load versions and the global save version for versioned datasets.
- `load_versions` keys must refer to explicit datasets or matching dataset patterns; unknown keys raise `DatasetNotFoundError`.
- All versioned datasets in one catalog must use the same save version; conflicting save versions raise `VersionAlreadyExistsError`.
- Version strings must be a single non-empty path component and cannot include path separators or be `.` or `..`.
- HTTP and HTTPS protocols do not support versioning; remove `versioned: true` for those datasets.
- Saving to an already existing versioned path raises `DatasetError`; use a fresh save version instead of overwriting.
- Mismatched explicit load and save versions can produce warnings and confusing pipeline behavior because downstream nodes may load a different version than the one just saved.

## Catalog Factory APIs

```python
from kedro.io import DataCatalog

catalog = DataCatalog.from_config({
    "{dataset_name}#csv": {
        "type": "pandas.CSVDataset",
        "filepath": "data/01_raw/{dataset_name}.csv",
    }
})
print(catalog.config_resolver.list_patterns())
print(catalog.config_resolver.resolve_pattern("companies#csv"))
```

- `CatalogConfigResolver(config=None, credentials=None, default_runtime_patterns=None)` extracts explicit dataset entries, dataset patterns, a single optional user catch-all pattern, and default runtime patterns.
- A pattern is any catalog key containing `{`; quote patterns in YAML because braces can confuse YAML parsing.
- Every placeholder used in the pattern body must also appear in the pattern name; otherwise Kedro raises `DatasetError` about incorrect dataset configuration.
- Patterns are matched by decreasing specificity, then decreasing placeholder count, then alphabetically.
- A single catch-all pattern with no literal characters is allowed; multiple catch-all patterns raise `DatasetError`.
- The default runtime pattern for `DataCatalog` is `{default}: {type: kedro.io.MemoryDataset}`; the default runtime pattern for `SharedMemoryDataCatalog` uses `kedro.io.SharedMemoryDataset`.
- `catalog.config_resolver.resolve_pattern(name)` returns the resolved config for a name that matches a dataset pattern, catch-all pattern, or runtime pattern.
- `catalog.config_resolver.list_patterns()` lists user patterns plus runtime patterns in priority order.

## OmegaConfigLoader API

```python
from kedro.config import MissingConfigException, OmegaConfigLoader

conf_loader = OmegaConfigLoader(
    conf_source="conf",
    env="local",
    runtime_params={"folder": "data/02_intermediate"},
    base_env="base",
    default_run_env="local",
)

try:
    catalog_config = conf_loader["catalog"]
except MissingConfigException:
    catalog_config = {}
```

- `OmegaConfigLoader(conf_source, env=None, runtime_params=None, *, config_patterns=None, base_env=None, default_run_env=None, custom_resolvers=None, merge_strategy=None, ignore_hidden=True)` loads YAML, YML, and JSON files using OmegaConf.
- Default config keys and patterns are `catalog`, `parameters`, `credentials`, and `globals`.
- Defaults are `catalog: ["catalog*", "catalog*/**", "**/catalog*"]`, `parameters: ["parameters*", "parameters*/**", "**/parameters*"]`, `credentials: ["credentials*", "credentials*/**", "**/credentials*"]`, and `globals: ["globals.yml"]`.
- In a project, settings usually provide `base_env="base"` and `default_run_env="local"`; when used directly with no env arguments, the loader can read config files directly from `conf_source`.
- `conf_loader[key]` raises `KeyError` for unknown config keys and `MissingConfigException` if no matching files exist for known non-`globals` keys.
- Duplicate top-level keys across files in the same environment raise `ValueError`; for `parameters`, nested duplicate keys are checked with dotted paths.
- Base and selected runtime environment are merged with `merge_strategy.get(key, "destructive")`.
- Accepted merge strategies are `destructive` and `soft`; unsupported strategy names raise `ValueError`.
- `destructive` replaces an entire top-level key from base with the env value; `soft` recursively merges nested dictionaries while env values win on collisions.
- Hidden files and directories are ignored by default; pass `ignore_hidden=False` when intentionally loading hidden config files.

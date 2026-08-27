# Configuration And Catalogs

Use this reference for self-contained Kedro catalog/configuration workflows: `catalog.yml`, `credentials.yml`, `parameters.yml`, `globals.yml`, factory patterns, runtime parameters, and environment merge behavior.

## Catalog YAML Basics

A typical catalog entry maps a dataset name to a dataset configuration. Persisted dataset implementations such as `pandas.CSVDataset` come from `kedro-datasets`, not core Kedro.

```yaml
# conf/base/catalog.yml
companies:
  type: pandas.CSVDataset
  filepath: data/01_raw/companies.csv
  load_args:
    sep: ","
  save_args:
    index: false
```

Rules to apply:

- Use dataset names that match pipeline node inputs and outputs; catalog entries are keyed by those names.
- Use `type` for an importable dataset class: short core names like `MemoryDataset`, `kedro.io.MemoryDataset`, `pandas.CSVDataset`, or a fully qualified custom dataset path.
- Use `filepath` and constructor-specific keys exactly as required by that dataset implementation.
- Use `load_args` and `save_args` for library-specific read/write options.
- Use `fs_args` for filesystem open/options such as `open_args_load` and `open_args_save`.
- Use `metadata` only for humans or plugins; Kedro does not change I/O behavior based on metadata.
- Keep temporary or intermediate outputs absent from `catalog.yml` when a `MemoryDataset` runtime fallback is sufficient.

## Credentials

```yaml
# conf/base/catalog.yml
raw_customers:
  type: pandas.CSVDataset
  filepath: s3://example-bucket/data/customers.csv
  credentials: dev_s3

# conf/local/credentials.yml
dev_s3:
  key: ${oc.env:AWS_ACCESS_KEY_ID}
  secret: ${oc.env:AWS_SECRET_ACCESS_KEY}
```

- Store secret values in `credentials.yml` or environment variables, not in `catalog.yml`.
- Kedro loads files whose names start with `credentials` or that live under directories whose names start with `credentials`.
- `DataCatalog.from_config(catalog, credentials)` recursively replaces string values under a `credentials` key with the referenced credentials object.
- `OmegaConfigLoader` enables the `oc.env` resolver only while loading `credentials`; by default, `${oc.env:...}` in `catalog` or `parameters` raises `UnsupportedInterpolationType`.
- Missing credential files can be handled as an empty credentials mapping when the workflow supports anonymous/local datasets.
- Never echo `credentials` mappings into logs, final answers, or validation reports; print only credential reference names if needed.

## Parameters

```yaml
# conf/base/parameters.yml
model_options:
  test_size: 0.2
  random_state: 3
```

```python
from kedro.pipeline import node

node(
    func=train_model,
    inputs=["model_input_table", "params:model_options"],
    outputs="model",
)
```

- Kedro loads parameter files whose names start with `parameters` or that live under directories whose names start with `parameters`.
- Use `params:name` in node inputs for a single parameter or top-level parameter group.
- Use `parameters` as a node input only when the node intentionally needs the full parameter dictionary.
- Kedro exposes parameters to the catalog as `MemoryDataset`s during project context construction.
- `kedro run --params=key=value,nested.key=2` overrides project parameters for a run; keys are strings and values are converted to int or float when possible.
- Runtime parameter merge is destructive by default: overriding a nested key can replace the rest of that top-level key unless `merge_strategy` is configured as `soft`.
- Parameter validation through Pydantic models or dataclasses is opt-in through node function type hints; validation applies to `params:` inputs, not arbitrary datasets.

## Globals And Interpolation

```yaml
# conf/base/globals.yml
dataset_type:
  csv: pandas.CSVDataset
raw_folder: data/01_raw

# conf/base/catalog.yml
companies:
  type: "${globals:dataset_type.csv}"
  filepath: "${globals:raw_folder}/companies.csv"
```

- `globals.yml` values can be referenced from catalog and parameter config with `${globals:key}`.
- Nested globals use dot notation, for example `${globals:dataset_type.csv}`.
- Defaults are supported, for example `${globals:missing_key, 23}`.
- Global keys beginning with `_` are not supported by the globals resolver.
- Duplicate globals across base and selected runtime environments are merged so the runtime environment value wins.
- `${runtime_params:...}` is not allowed inside `globals`; Kedro raises `UnsupportedInterpolationType` with a message that the `runtime_params:` resolver is not supported for globals.

## Runtime Params Resolver

```yaml
# conf/base/catalog.yml
companies:
  type: pandas.CSVDataset
  filepath: "${runtime_params:raw_folder, 'data/01_raw'}/companies.csv"
```

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --params="raw_folder=data/fixture_raw"
```

- `${runtime_params:key}` can override catalog, parameters, and other config values except `globals`.
- Add a default value as `${runtime_params:key, default_value}` when a run parameter is optional.
- A manually created `OmegaConfigLoader` only sees runtime params you pass to its constructor; it does not automatically receive CLI `--params` values.
- Use the project context when code needs the actual run parameters supplied to `kedro run`.
- For command examples, set `KEDRO_DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` when the environment must avoid telemetry.

## Config Environments

The project convention is a `conf` source with a base environment and an overriding run environment.

```text
conf/
  base/
    catalog.yml
    parameters.yml
    globals.yml
  local/
    credentials.yml
    parameters.yml
```

```python
from kedro.config import OmegaConfigLoader

conf_loader = OmegaConfigLoader(
    conf_source="conf",
    env="local",
    base_env="base",
    default_run_env="local",
)
catalog_config = conf_loader["catalog"]
```

- Base config is loaded first, then `env` if supplied, otherwise `default_run_env`.
- If `env` equals `base_env`, Kedro loads it only once.
- `OmegaConfigLoader` supports local paths, some remote/cloud protocols through `fsspec`, and archive sources, but remote config loading can require extra filesystem dependencies and credentials.
- Hidden files and directories are ignored by default; pass `ignore_hidden=False` only when hidden config files are intentional.
- Missing known config keys such as `catalog`, `parameters`, or `credentials` raise `MissingConfigException`; handle this explicitly when missing config is valid.

## Merge Strategy

```python
# src/<package_name>/settings.py
from kedro.config import OmegaConfigLoader

CONFIG_LOADER_CLASS = OmegaConfigLoader
CONFIG_LOADER_ARGS = {
    "merge_strategy": {
        "parameters": "soft",
        "catalog": "destructive",
    }
}
```

- Same-environment files always merge softly but cannot contain duplicate non-private keys; duplicates raise `ValueError`.
- Across environments, the default strategy is `destructive`.
- `destructive` means a top-level key from the overriding environment replaces the whole base value for that key.
- `soft` means nested dictionaries are merged and the overriding environment wins only on colliding nested values.
- Accepted values are exactly `soft` and `destructive`; unsupported names raise `ValueError`.
- Use `soft` for nested parameter groups when run/local overrides should preserve unspecified nested keys.
- Use `destructive` when an environment should replace a complete top-level object such as a storage backend definition.

## Catalog Factories

Factories reduce repeated catalog entries by matching dataset names against placeholder patterns.

```yaml
# conf/base/catalog.yml
"{dataset_name}#csv":
  type: pandas.CSVDataset
  filepath: data/01_raw/{dataset_name}.csv

"{namespace}.model":
  type: pickle.PickleDataset
  filepath: data/06_models/{namespace}/model.pkl
  versioned: true
```

- Always quote factory keys containing `{...}` in YAML.
- A factory placeholder used in the entry body must appear in the factory key.
- Use literal suffixes such as `#csv` or prefixes to avoid ambiguous matches.
- Dataset patterns are matched before a user catch-all pattern and before the default runtime pattern.
- If no explicit or factory entry matches at runtime, `DataCatalog` can fall back to a `MemoryDataset` for intermediate datasets.
- A user catch-all factory such as `"{default_dataset}"` replaces the default in-memory behavior; allow only one catch-all.
- Inspect patterns programmatically with `catalog.config_resolver.list_patterns()` and resolve a specific name with `catalog.config_resolver.resolve_pattern("name")`.

Project catalog commands can inspect pipeline-aware factory resolution:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro catalog list-patterns
KEDRO_DISABLE_TELEMETRY=1 kedro catalog resolve-patterns --pipeline=my_pipeline
KEDRO_DISABLE_TELEMETRY=1 kedro catalog describe-datasets --pipeline=my_pipeline
```

These commands require a Kedro project context and may import project code; they should not be used as a standalone YAML validator.

## Versioned Catalog Entries

```yaml
trained_model:
  type: pickle.PickleDataset
  filepath: data/06_models/model.pkl
  versioned: true
```

```python
from kedro.io import DataCatalog

catalog = DataCatalog.from_config(
    catalog_config,
    credentials=credentials,
    load_versions={"trained_model": "2024-01-01T00.00.00.000Z"},
    save_version="2024-01-02T00.00.00.000Z",
)
```

- Set `versioned: true` in YAML for datasets that support `AbstractVersionedDataset` behavior.
- The versioned path shape is `filepath/<version>/<filename>`.
- Leave load/save versions unset for normal runs so Kedro loads the latest available version and generates a fresh save timestamp.
- Pin `load_versions` only when replaying or auditing exact inputs.
- Pin `save_version` only when all versioned outputs in the catalog should share one explicit save version.
- Do not enable versioning for HTTP/HTTPS datasets.
- Do not save twice to the same explicit version; versioned save paths must not already exist.

## Standalone Validation Pattern

For a standalone catalog file, prefer the bundled validator:

```bash
python skills/kedro/sub-skills/data-catalog-and-config/scripts/validate_catalog_config.py \
  --catalog-yaml conf/base/catalog.yml \
  --credentials-yaml conf/local/credentials.yml
```

Expected safe output includes dataset names, pattern names, and resolved type strings. It does not print credential values and does not load or save dataset contents.

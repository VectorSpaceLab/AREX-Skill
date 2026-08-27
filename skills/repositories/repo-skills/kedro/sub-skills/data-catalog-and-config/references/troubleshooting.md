# Troubleshooting

Use this guide to triage Kedro catalog, dataset, credentials, versioning, and `OmegaConfigLoader` failures.

## Fast Triage Checklist

1. Confirm the installed package is `kedro` and the import name is `kedro`; Kedro 1.4.0 supports Python `>=3.10`.
2. Confirm concrete dataset implementations are installed separately when the `type` points to `kedro_datasets`, `pandas.*`, `spark.*`, SQL, cloud, or API datasets.
3. Load YAML safely and validate structure before loading or saving data.
4. Redact credentials and connection strings from logs.
5. Distinguish `OmegaConfigLoader` failures from `DataCatalog.from_config()` failures: config loader errors happen while reading/merging config files; catalog errors happen while resolving dataset configs or materializing datasets.
6. If a failure appears during `kedro run`, route command/session/runner details to the execution or project sub-skill after isolating the catalog/config issue here.

## Install And Optional Dependency Errors

Symptoms:

- `DatasetError: Class 'pandas.CSVDataset' not found, is this a typo?`
- `ModuleNotFoundError` or a message asking to install missing dependencies for a dataset class path.
- Warning about `CSVDataSet` spelling.

Likely causes and fixes:

- Core Kedro 1.4.0 does not include most file/database datasets; install `kedro-datasets` and the needed extras for the dataset group.
- Use modern class spelling: `CSVDataset`, `ParquetDataset`, `SQLTableDataset`, not stale `CSVDataSet` or `ParquetDataSet`.
- Use a fully qualified custom dataset class path that is importable in the active environment.
- Ensure custom dataset classes subclass `kedro.io.AbstractDataset`.
- For cloud paths, install the matching filesystem package and provide credentials through `credentials.yml` or provider-standard environment variables.

Quick probe:

```python
from kedro.io import AbstractDataset
from kedro.io.core import parse_dataset_definition

class_obj, kwargs = parse_dataset_definition({"type": "MemoryDataset"})
assert issubclass(class_obj, AbstractDataset)
```

## Invalid Catalog Entry

Symptoms:

- `Catalog entry '<name>' is not a valid dataset configuration.`
- `'type' is missing from dataset catalog configuration.`
- Constructor error saying a dataset must only contain arguments valid for the constructor.

Likely causes and fixes:

- A top-level interpolation helper key in catalog config does not start with `_`; helper keys should be private, such as `_pandas` or `_paths`.
- A concrete dataset entry is a scalar/list instead of a mapping.
- The `type` key is missing or misspelled.
- A YAML key intended for one dataset implementation is being passed to a different dataset class.
- A `version` key was used directly in YAML; use `versioned: true` instead.

Use the validator script to catch these without printing credentials:

```bash
python skills/kedro/sub-skills/data-catalog-and-config/scripts/validate_catalog_config.py --catalog-yaml conf/base/catalog.yml
```

## Credentials Failures

Symptoms:

- `Unable to find credentials '<name>'`.
- Cloud or SQL dataset constructor fails after credentials resolution.
- Secrets appear in debug output.

Likely causes and fixes:

- The dataset has `credentials: some_name`, but the credentials mapping lacks `some_name`.
- `credentials.yml` is in the wrong environment or does not match the loader's `credentials` config patterns.
- `${oc.env:VAR}` is used in `credentials.yml`, but the environment variable is unset.
- A SQL dataset expects `con` in credentials or in `load_args`/`save_args`, depending on the dataset class.
- Do not print resolved catalog dictionaries, because credentials have been injected recursively.

Safe debugging pattern:

```python
from kedro.config import MissingConfigException, OmegaConfigLoader

conf = OmegaConfigLoader("conf", env="local", base_env="base", default_run_env="local")
try:
    credentials = conf["credentials"]
except MissingConfigException:
    credentials = {}
print(sorted(credentials))  # names only, not values
```

## OmegaConfigLoader Missing Or Duplicate Config

Symptoms:

- `MissingConfigException: Given configuration path either does not exist or is not a valid directory`.
- `MissingConfigException: No files of YAML or JSON format found ... matching the glob pattern(s)`.
- `ValueError: Duplicate keys found in ...`.
- `KeyError: No config patterns were found for '<key>' in your config loader`.

Likely causes and fixes:

- `conf_source`, `base_env`, `default_run_env`, or `env` points to a directory that does not exist.
- You are using `OmegaConfigLoader` directly but forgot that direct usage defaults to no `base` or `local` environment unless you pass `base_env` and `default_run_env`.
- Config files are named outside the default patterns; add `CONFIG_LOADER_ARGS["config_patterns"]`.
- Two files in the same environment define the same top-level key; for `parameters`, duplicate nested dotted keys also fail.
- The requested config key is not present in `config_patterns`; add a custom pattern such as `"spark": ["spark*/"]`.
- Hidden files/directories are ignored by default; pass `ignore_hidden=False` only if intentional.

## Interpolation And Resolver Errors

Symptoms:

- `UnsupportedInterpolationType` for `oc.env` outside credentials.
- `The runtime_params: resolver is not supported for globals.`
- `Globals key '<key>' not found and no default value provided.`
- `Runtime parameter '<key>' not found and no default value provided.`
- `Keys starting with '_' are not supported for globals.`

Likely causes and fixes:

- Use `${oc.env:VAR}` only in `credentials.yml` unless you explicitly and cautiously register `oc.env` as a custom resolver.
- Do not use `${runtime_params:...}` in `globals.yml`; use `${runtime_params:key, ${globals:fallback}}` in catalog or parameters instead.
- Provide resolver defaults for optional values, for example `${globals:missing, 23}` or `${runtime_params:folder, 'data/01_raw'}`.
- Do not reference `_private` globals through the `globals` resolver.
- When instantiating `OmegaConfigLoader` manually, pass `runtime_params={...}` explicitly; CLI `--params` is not automatically available to that standalone object.

## Merge Strategy Confusion

Symptoms:

- A nested parameter group loses keys after `local` or runtime overrides.
- A local catalog entry replaces all base fields under the same top-level dataset name.
- `ValueError: Merging strategy hard not supported` or similar.

Likely causes and fixes:

- Default merge across environments is `destructive`, so a top-level key in `local` replaces the entire base value for that key.
- Set `merge_strategy={"parameters": "soft"}` when nested parameter overrides should preserve unspecified nested keys.
- Use `destructive` intentionally when replacing an entire top-level object, such as a dataset definition for another environment.
- Same-environment duplicate keys are never resolved by merge strategy; they raise duplicate-key errors.
- Accepted strategy names are `soft` and `destructive` only.

Minimal check:

```python
from kedro.config import OmegaConfigLoader

conf = OmegaConfigLoader(
    "conf",
    env="local",
    base_env="base",
    default_run_env="local",
    merge_strategy={"parameters": "soft"},
)
print(conf["parameters"])
```

## Factory Pattern Failures

Symptoms:

- `Multiple catch-all patterns found in the catalog`.
- `Incorrect dataset configuration provided. Keys used in the configuration ... should present in the dataset pattern name ...`.
- A dataset resolves to an unexpected type or filepath.
- A missing dataset unexpectedly resolves to a persisted dataset instead of a `MemoryDataset`.

Likely causes and fixes:

- Quote pattern keys in YAML, for example `"{dataset_name}#csv"`.
- Ensure each placeholder used in `filepath`, `credentials`, `load_args`, or nested values also appears in the pattern key.
- Add literal prefixes/suffixes to make patterns specific and avoid accidental catch-all matches.
- Keep only one catch-all pattern with no literal characters.
- Remember precedence: specific dataset patterns, user catch-all, then default runtime pattern.
- Use `catalog.config_resolver.list_patterns()` and `catalog.config_resolver.resolve_pattern("dataset_name")` to explain a resolution.

## Lazy Dataset Materialization Errors

Symptoms:

- `DataCatalog.from_config()` succeeds but `catalog["name"]`, `catalog.load("name")`, or `catalog.values()` fails.
- Dataset import/constructor failures appear only when a dataset is accessed.

Likely causes and fixes:

- Kedro stores config-backed entries as lazy datasets and materializes them on first access.
- `catalog.keys()` can succeed even if a dataset class or optional dependency is missing.
- Force validation by iterating names and calling `catalog.get_type(name)` or accessing `catalog[name]` when safe.
- Avoid loading data during config validation unless the user explicitly asks for I/O validation.

The bundled validator materializes enough to resolve types when dependencies are installed, but it does not call `load()` or `save()`.

## Versioning Errors

Symptoms:

- `Versioning is not supported for HTTP protocols`.
- `Version string '<value>' is not allowed`.
- `Did not find any versions for <dataset>`.
- `Save path '<path>' ... must not exist if versioning is enabled`.
- `All datasets in the catalog must have the same save version`.
- Warning that load and save versions are inconsistent.

Likely causes and fixes:

- Remove `versioned: true` for `http://` and `https://` datasets.
- Use version strings that are single path components; do not include `/`, `\`, `.`, or `..`.
- If loading latest, ensure at least one version directory exists under `filepath/<version>/<filename>`.
- Do not save twice to an explicit existing save version.
- Pass one shared `save_version` to `DataCatalog.from_config()` when pinning save versions globally.
- Prefer unpinned save versions for normal runs so Kedro generates fresh timestamps.

## Memory And Cache Errors

Symptoms:

- `Data for MemoryDataset has not been saved yet.`
- `Saving 'None' to a 'Dataset' is not allowed`.
- `Invalid copy mode`.
- Cached dataset fails under multiprocessing.

Likely causes and fixes:

- Save data to `MemoryDataset` before loading it, or ensure an upstream node produces the intermediate output.
- Return a real value from nodes; `None` outputs cannot be saved.
- Use only `deepcopy`, `copy`, or `assign` for `MemoryDataset(copy_mode=...)`.
- Avoid `CachedDataset` with `ParallelRunner` because it is single-process; route runner-choice issues to `../runners-and-execution/SKILL.md`.

## Custom Dataset Errors

Symptoms:

- Dataset cannot be instantiated because abstract methods are missing.
- Dataset type does not subclass `AbstractDataset`.
- Load/save exceptions are wrapped as `DatasetError`.
- Parallel execution complains about serialization.

Likely causes and fixes:

- Implement `load()`, `save()`, `_exists()`, and `_describe()` or equivalent `_load()`/`_save()` methods.
- Subclass `kedro.io.AbstractDataset` or `AbstractVersionedDataset` for versioned storage.
- Make constructor arguments match the YAML keys exactly.
- Store only serializable state if the dataset may be used with `ParallelRunner`.
- Set `_SINGLE_PROCESS = True` if the dataset cannot be pickled or is not multiprocessing-safe.
- For extension/API design of custom datasets, route to `../hooks-and-extensions/SKILL.md`.

## Command And Telemetry Safety

- `kedro catalog list-patterns`, `kedro catalog resolve-patterns`, and `kedro catalog describe-datasets` require a project and may import project code.
- Prefix diagnostic `kedro` commands with `KEDRO_DISABLE_TELEMETRY=1` or set `DO_NOT_TRACK=1` when telemetry must be disabled.
- Do not run `kedro run` just to validate YAML; use `OmegaConfigLoader`, `DataCatalog.from_config()`, or the bundled validator first.
- Do not make network or cloud calls during validation unless the user explicitly asks to test external connectivity.

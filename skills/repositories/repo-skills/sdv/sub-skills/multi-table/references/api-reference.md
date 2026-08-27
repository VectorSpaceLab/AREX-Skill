# Multi-table API reference

This reference covers SDV relational synthesis for `dict[str, pandas.DataFrame]` data described by unified `Metadata` or legacy `MultiTableMetadata`.

## Imports

```python
from sdv.metadata import Metadata, MultiTableMetadata
from sdv.multi_table import HMASynthesizer, DayZSynthesizer
from sdv.utils import drop_unknown_references, load_constraints
```

## Relational metadata essentials

| API | Purpose | Notes |
| --- | --- | --- |
| `Metadata.detect_from_dataframes(data, infer_sdtypes=True, infer_keys='primary_and_foreign', foreign_key_inference_algorithm='column_name_match', verbose=False)` | Return unified metadata from a dict of tables. | Treat inferred keys/relationships as a first draft and review them. |
| `Metadata.add_table(table_name)` | Add a table manually. | Add all needed columns before relationships. |
| `Metadata.add_column(column_name, table_name=None, **kwargs)` / `update_column(...)` | Define sdtypes and key-related parameters. | Primary and foreign-key columns should have compatible `id` or PII/Faker sdtypes. |
| `Metadata.set_primary_key(column_name, table_name=None)` | Declare the parent table key. | Composite keys can be lists; child foreign keys must match key length. |
| `Metadata.add_relationship(parent_table_name, child_table_name, parent_primary_key, child_foreign_key)` | Add parent-child relation. | Parent key must be primary key and child key must exist with matching sdtype/length. |
| `Metadata.validate()` | Check metadata graph and table definitions. | Run before `validate_data`. |
| `Metadata.validate_data(data)` | Validate all DataFrames, primary-key uniqueness, and referential integrity. | `data` must be a dict keyed by metadata table names. |
| `drop_unknown_references(data, metadata, drop_missing_values=False, verbose=True)` | Return a copy with rows containing unknown foreign keys removed. | Use only when row loss is acceptable; otherwise repair keys manually. |

Legacy `MultiTableMetadata` exposes similar instance methods such as `detect_from_dataframes(data, verbose=False)`, `detect_from_csvs(folder_name, read_csv_parameters=None)`, `add_relationship`, `set_primary_key`, `validate`, `validate_data`, `visualize`, `save_to_json`, and `load_from_json`. Prefer unified `Metadata` for new code.

## `HMASynthesizer`

Constructor:

```python
HMASynthesizer(metadata, locales=['en_US'], verbose=True)
```

| Method | Purpose | Notes |
| --- | --- | --- |
| `fit(data)` | Validate/preprocess all tables and fit one hierarchy-aware model. | `data` is a dict of DataFrames. Validate data first for clearer errors. |
| `sample(scale=1.0)` | Generate all tables. | `scale` multiplies learned table sizes. `0.5` roughly halves and `1.5` roughly increases output size, subject to relationship constraints. |
| `reset_sampling()` | Reset the sampler state after fit. | Useful for reproducible repeated samples. |
| `preprocess(data)` / `fit_processed_data(processed_data)` | Advanced staged path. | Use only with processed data produced by the same synthesizer. |
| `auto_assign_transformers(data)` | Populate per-table RDT transformer defaults. | Use before `update_transformers` when custom transformers are needed. |
| `get_transformers(table_name)` | Inspect transformer mapping for one table. | Requires prior transformer assignment or fit. |
| `update_transformers(table_name, column_name_to_transformer)` | Override selected table transformers. | Refit after changes. |
| `get_table_parameters(table_name)` | Return parameters of the table's internal single-table synthesizer. | Useful for debugging per-table choices. |
| `set_table_parameters(table_name, table_parameters)` | Set parameters for one table before fitting. | Validate keys match supported single-table synthesizer parameters. |
| `get_parameters()` | Return global constructor parameters. | Includes metadata-independent settings. |
| `add_constraints(constraints)` | Attach CAG or programmable constraints. | Add before fit; per-table constraints usually need `table_name`. |
| `get_constraints(filepath=None)` | Return or save constraints JSON. | Path must not already exist. |
| `set_constraints(filepath)` | Deprecated JSON loader. | Prefer `load_constraints(filepath)` then `add_constraints`. |
| `validate_constraints(synthetic_data)` | Validate sampled dict against attached constraints. | Errors name table and invalid row indices. |
| `get_metadata(version='original')` | Return original or constraint-modified metadata. | Use `version='modified'` after constraints transform metadata. |
| `get_info()` | Return fit lifecycle information. | Useful after `load`. |
| `save(filepath)` / `HMASynthesizer.load(filepath)` | Serialize/deserialize with cloudpickle. | Load with the same class and compatible package version. |

## Multi-table `DayZSynthesizer`

Community SDV exposes parameter creation/validation only; constructing `DayZSynthesizer(metadata)` raises a public-feature error unless an enterprise runtime owns actual DayZ synthesis.

| API | Purpose | Notes |
| --- | --- | --- |
| `DayZSynthesizer.create_parameters(data, metadata, filepath=None)` | Create DayZ parameter dict from relational data. | Output contains `DAYZ_SPEC_VERSION`, `tables`, and `relationships`. Passing `filepath` writes JSON. |
| `DayZSynthesizer.validate_parameters(metadata, parameters)` | Validate a DayZ parameter dict. | Checks table/column presence, relationship structures, cardinality bounds, and table row counts. |

Relationship parameter entries use:

```json
{
  "parent_table_name": "customers",
  "child_table_name": "orders",
  "parent_primary_key": "customer_id",
  "child_foreign_key": "customer_id",
  "min_cardinality": 0,
  "max_cardinality": 10
}
```

`min_cardinality` must be an integer `>= 0`; `max_cardinality` must be an integer `> 0`; `min_cardinality <= max_cardinality`; and the relationship must exist in metadata.

## Constraints and utilities in multi-table workflows

- Current CAG constraints that target one table should include `table_name`.
- True multi-table programmable constraints should subclass `ProgrammableConstraint` and receive/return `dict[str, DataFrame]`.
- `SingleTableProgrammableConstraint` can be used with multi-table metadata only if the class stores a valid `table_name`.
- Use `load_constraints(filepath)` to read current JSON, compare the loaded count with the file entries, and call `synthesizer.add_constraints(loaded_constraints)` before fitting.

## Save/load compatibility

Saved multi-table synthesizers include metadata, fitted per-table state, constraints, and sampling state. If loading fails with version warnings or device errors, compare the saved SDV version with the runtime version and refit when possible. For GPU-backed custom/deep per-table components, prefer loading on compatible hardware.

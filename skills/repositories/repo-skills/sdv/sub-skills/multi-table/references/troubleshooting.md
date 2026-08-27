# Multi-table troubleshooting

## Metadata and relationship setup

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `data` is rejected as not a dictionary of DataFrames. | A single DataFrame, list, or dict with non-DataFrame values was passed. | Build `dict[str, pandas.DataFrame]` keyed by table name. Route file loading to data-preparation if needed. |
| Metadata has a table missing from data, or data has a table missing from metadata. | Table names differ between the dict and metadata. | Rename dict keys or update metadata tables so they match exactly. |
| Primary-key validation fails. | Primary-key column is missing, has nulls, duplicates, or an incompatible sdtype. | Set the key column sdtype to `id` or compatible PII/Faker sdtype, remove nulls, and ensure uniqueness. |
| Relationship validation fails with key length or sdtype errors. | Composite key lengths differ, or parent/child key sdtypes do not match. | Use matching key lists and compatible sdtypes on both sides before `add_relationship`. |
| Relationship graph is disconnected or circular. | Tables are not all reachable from the relationship graph, or a cycle was created. | Add missing relationships or split independent table groups. HMA expects a valid hierarchy. |
| HMA raises a complex-schema/depth error. | The relational graph is too deep or complicated for the selected HMA path. | Simplify the schema, model independent groups separately, or use another workflow/runtime that supports the schema. |

## Referential integrity

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `validate_data` reports unknown references. | Child foreign-key values are absent from parent primary keys. | Repair keys manually, or run `drop_unknown_references(data, metadata)` only if dropping rows is acceptable. |
| Null foreign keys remain after cleanup. | `drop_unknown_references` keeps nulls by default. | Set `drop_missing_values=True` when rows with null foreign keys should also be removed. |
| Cleanup removes too many rows. | Relationship direction, key dtype, whitespace, or formatting is wrong. | Compare parent keys and child keys after normalizing type/string formatting; do not continue until the relationship is semantically correct. |
| Fitting fails with null foreign-key message. | HMA cannot model missing foreign keys in selected relationships. | Fill or drop null foreign-key rows before fitting. |

## HMA fit/sample behavior

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `SamplingError` or not-fitted error when sampling. | `sample` was called before `fit`, or a loaded model is unfitted. | Fit first or load a fitted model. Inspect `get_info()` when unsure. |
| Sampled tables have unexpected row counts. | `scale` is approximate and relationship constraints affect row counts. | Validate relational integrity instead of asserting exact scaled sizes for every table. Use `scale=1.0` for closest learned-size behavior. |
| `sample(scale=...)` with invalid scale fails. | `scale` is not a positive numeric value. | Pass a positive float such as `0.5`, `1.0`, or `2.0`. |
| Sampling is not repeatable across calls. | Sampling state advances after each call. | Call `reset_sampling()` to reset to the post-fit state, then sample again. Do not expect cross-version bitwise equality. |
| `get_table_parameters` or `set_table_parameters` rejects a table. | Table name is absent from metadata or parameters target an unsupported table synthesizer setting. | Use exact table names and parameter keys from `get_table_parameters(table_name)` as the starting point. |
| Transformer update fails or appears ignored. | Transformer defaults were not assigned, transformer targets a protected key, or the model was not refit after updates. | Call `auto_assign_transformers(data)`, update only valid non-key columns, and refit. |

## Constraints in relational workflows

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Constraint says missing `table_name`. | A single-table CAG constraint is attached to multi-table metadata without a target table. | Recreate the constraint with `table_name='...'`. |
| `SingleTableProgrammableConstraint` fails in multi-table metadata. | The programmable class uses DataFrame-style methods but lacks `self.table_name`. | Store `self.table_name` in `__init__`, or use dictionary-style `ProgrammableConstraint`. |
| Constraints were added after fitting but ignored. | Constraint changes do not apply to a fitted model until refit. | Add constraints before `fit`, or refit after adding them. |
| `validate_constraints` reports invalid rows in one table. | Synthetic rows violated a constraint, often due to custom reverse logic or incompatible metadata. | Inspect invalid rows for the named table, revise the constraint or metadata, and refit. |

## DayZ parameters

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `DayZSynthesizer(metadata)` raises an error that only parameter methods are public. | Actual DayZ synthesis is not public in Community SDV. | Use `create_parameters` and `validate_parameters` only, unless the runtime explicitly provides SDV Enterprise DayZ generation. |
| Parameter validation reports unknown or missing relationship keys. | Relationship entries have unexpected keys or omit required names. | Use only `parent_table_name`, `child_table_name`, `parent_primary_key`, `child_foreign_key`, and optional `min_cardinality`/`max_cardinality`. |
| Cardinality validation fails. | `min_cardinality`, `max_cardinality`, parent row count, and child row count are inconsistent. | Ensure `min_cardinality >= 0`, `max_cardinality > 0`, `min <= max`, and child row counts can satisfy the bounds. |
| Relationship in parameters does not exist in metadata. | Parameter file describes a relationship not declared in metadata. | Add the relationship to metadata or remove/correct the parameter entry. |
| Multiple entries for the same relationship. | Duplicate relationship parameter dictionaries exist. | Keep one entry per metadata relationship. |

## Save/load and version compatibility

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Loading warns about SDV version mismatch. | Model was saved under another SDV version. | Prefer refitting under the current version; if only inspecting, record the warning. |
| Load succeeds but metadata differs from current data. | The saved model contains its own metadata snapshot. | Compare `loaded.get_metadata().to_dict()` with current metadata and refresh/refit if different. |
| Loading fails with device/backend errors. | A custom or deep per-table component was saved on a different backend. | Load in a compatible runtime or refit/save with portable CPU settings when possible. |

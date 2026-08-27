# Sequential troubleshooting

## PAR setup and metadata errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `PARSynthesizer is designed for multi-sequence data... metadata does not include a sequence key` | Metadata does not declare `sequence_key`. | Choose the column that groups rows into sequences, set its sdtype to `id`, then call `metadata.set_sequence_key(...)`. Do not use PAR for a flat table with no repeated sequence groups. |
| PAR rejects unified metadata with multiple tables. | `PARSynthesizer` only supports one sequential table. | Extract the sequential table and use one-table metadata, or route relational synthesis to the multi-table sub-skill. |
| Metadata validation says `sequence_index` must be `datetime` or `numerical`. | The sequence index column was detected or edited to an unsupported sdtype. | Update the column sdtype to `datetime` or `numerical`, or remove the sequence index if row order is not modeled. |
| Metadata says `sequence_index` and `sequence_key` have the same value. | The same column was assigned as both group id and row order. | Use separate columns: one repeated sequence key and one time/order column. |
| `Your provided sequence key is not in the data` during subsetting. | `get_random_sequence_subset` cannot find the metadata sequence key column in the DataFrame. | Rename the data column or fix metadata before calling the utility. |

## Context-column failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `The sequence key [...] cannot be a context column` | `context_columns` includes the sequence key. | Remove the sequence key from `context_columns`. Include it in `sample_sequential_columns` input only as the output sequence id, not as a context feature. |
| `Context column '<col>' is changing inside sequence` | A declared context column has more than one value for at least one sequence key. | Group by sequence key and inspect `nunique(dropna=False)`. Either clean the data so the value is constant per sequence or remove the column from `context_columns`. |
| `sample_sequential_columns` says the synthesizer has no context columns. | The model was created with `context_columns=None` or an empty list. | Use `sample()` for unconstrained new sequences, or refit a new PAR synthesizer with explicit context columns. |
| Known-context generation does not preserve requested sequence ids. | The context DataFrame omitted the sequence key column or used a different column name. | Include the sequence key column with one unique value per desired sequence in the `context_columns` DataFrame. |
| Datetime context rows fail validation or produce unexpected values. | Context datetime dtype/format differs from fitting data or metadata. | Convert known-context values with `pd.to_datetime` or use the same string format declared in metadata before calling `sample_sequential_columns`. |
| Transformer update fails with `Transformers for context columns are not allowed to be updated`. | A modelable context column was passed to `update_transformers`. | Update only non-context columns, or choose context columns that do not need custom transformation. Refit after transformer changes. |

## Sampling and sequence behavior

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Output is not in the intended chronological order. | Input rows were not sorted before fitting, or sequence index metadata was missing. | Sort by sequence key and sequence index before fit; declare `sequence_index` for datetime/numerical order columns. |
| Generated sequences have unexpected lengths. | `sequence_length=None` samples learned lengths; a fixed value forces all generated sequences to that length. | Pass `sequence_length=<int>` for fixed-size downstream requirements, or omit it to preserve learned variability. |
| All-null columns disappear or are not all null in output. | Metadata omitted the all-null column or an older workflow dropped it during reverse transform. | Ensure the all-null column is present in metadata with the intended sdtype before fit, and check the sampled output contains the column filled with nulls. |
| Sampling before fitting raises a not-fitted error. | The synthesizer was constructed or loaded before `fit`. | Fit before sampling, or load a fitted model. Saving an unfitted model is allowed but not sampleable. |
| `get_random_sequence_subset` returns fewer unique sequences than expected. | Random row-level draws can repeat sequence ids, especially with long or imbalanced sequences. | Set a NumPy seed for reproducibility and verify `subset[sequence_key].nunique()`; rerun or draw a larger subset if exact coverage is required. |
| Long-sequence subsetting raises a method error. | `long_sequence_subsampling_method` is not one of the supported strings. | Use `'first_rows'`, `'last_rows'`, or `'random'`. |

## Constraints with PAR

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `cannot accommodate constraints with a mix of context and non-context columns` | One constraint covers both context and time-varying columns. | Split the modeling objective, redesign the constraint, or change the context-column set so every constraint is context-only or non-context-only. |
| `cannot accommodate multiple constraints that overlap on the same columns` | Two constraints both act on at least one same column. | Combine the logic into one constraint or remove the overlap. |
| Programmable constraint rejected as not compatible with single-table synthesizers. | The constraint is multi-table or lacks single-table compatibility. | Use or implement a single-table programmable constraint; route design details to the constraints sub-skill. |
| Constraint appears ignored after being added post-fit. | Constraints were attached after the model was already fit. | Add constraints before `fit`; if attached later, refit before sampling. |

## Torch and CUDA

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No module named 'torch'... install torch in order to use the 'PARSynthesizer'` | PAR depends on deepecho/torch and torch is missing. | Install a compatible torch build for the target environment, or use a runtime where torch is already available. |
| Training is slow or uses CPU despite `cuda=True`. | CUDA is unavailable, incompatible, or torch cannot see it. | Treat `cuda=True` as permission to try CUDA, not a guarantee. Check torch CUDA availability outside the skill and set `cuda=False` when CPU is intended. |
| Loading a saved model fails on a CPU-only machine after GPU training. | The serialized object contains GPU-backed torch state. | Prefer fitting/saving with `cuda=False` when the model must be portable to CPU-only hosts, or reload in a compatible GPU runtime. |

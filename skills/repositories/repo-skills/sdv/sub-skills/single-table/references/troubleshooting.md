# Single-Table Troubleshooting

## Fit and Sample Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `SamplingError: This synthesizer has not been fitted...` | `sample`, `sample_from_conditions`, or `sample_remaining_columns` was called before `fit` / `fit_processed_data`. | Call `fit(real_data)` first. If using processed data, call `processed = synthesizer.preprocess(real_data.copy())` then `fit_processed_data(processed)` on the same synthesizer. Check `synthesizer.get_info()['is_fit']`. |
| `ValueError: You must specify the number of rows...` | `sample(num_rows=None)` or omitted `num_rows`. | Pass a positive integer, e.g. `sample(num_rows=100)`. Use conditions when row counts come from `Condition` objects. |
| Sampling interrupted and says no results were saved | Sampling raised an exception and `output_file_path` was omitted. | Re-run after fixing the root error. If long sampling may be interrupted, provide a new non-existing `output_file_path` so partial results can be written. |
| `AssertionError` because an output file already exists | `output_file_path` points to an existing file. | Choose a new path or delete/rename the old output before sampling. |
| Metadata modification warning before fit/sample | The metadata object was modified after synthesizer construction. | Create a fresh synthesizer with the updated metadata; metadata changes are not applied to an existing synthesizer. |

## Constructor and Metadata Errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `SynthesizerInputError` for `enforce_min_max_values` or `enforce_rounding` | A non-boolean value was passed. | Use `True` or `False` only. |
| Composite primary key error | Community single-table synthesizers do not support composite primary keys. | Redesign metadata to use a single primary key, remove the composite key, or route relational modeling to a multi-table workflow when appropriate. |
| Invalid `numerical_distributions` type | Passed something other than `None` or `dict`. | Use `{'column_name': 'gamma'}` style mappings or omit the argument. |
| Invalid `numerical_distributions` columns | Mapping includes columns absent from metadata or columns dropped/renamed by preprocessing. | Use metadata column names exactly; after constraints/transformers, confirm the numerical columns are still statistically modeled. |
| Invalid distribution name | Distribution is not one of SDV's supported copula options. | Use `norm`, `beta`, `truncnorm`, `uniform`, `gamma`, or `gaussian_kde`. |
| `SingleTableMetadata` deprecation warning | Legacy metadata class was used. | Prefer unified `Metadata`. Existing code may still run, but new code should migrate. |

## Conditional Sampling Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Unexpected column name ...` | Conditions include a column that was not in original fitted data/metadata. | Rename/drop bad condition columns. If metadata changed, build and fit a new synthesizer. |
| `Cannot conditionally sample ... primary key` | Conditions include the primary key column. | Do not condition on generated keys. Condition on descriptive columns, or generate keys after sampling if your workflow owns key assignment. |
| `Provided conditions are not valid for the given constraints` | Conditions violate attached constraints after transformation. | Adjust the requested values so they satisfy constraints; use the constraints sub-skill to check the business rule; refit if constraints changed. |
| `Unable to sample any rows for the given conditions` | Conditions are impossible, out of bounds, too rare, or rejected by constraints. | First verify the values exist or are plausible in real data. Then try larger `max_tries_per_batch` / `batch_size`. If still failing, relax conditions, remove incompatible constraints, or use GaussianCopula for easier conditional sampling. |
| Only fewer rows than requested are sampled | Reject sampling could not find enough valid rows. | Increase `max_tries_per_batch`, increase `batch_size`, split conditions into easier groups, or request fewer/less rare combinations. |
| Deep model conditionals are slow | CTGAN/TVAE/CopulaGAN may need SDV-level filtering when the underlying model does not support conditions. | Prefer GaussianCopula for heavy conditional workloads, or keep conditions broad and batch sizes reasonable. |

## Deep Models, Torch, and GPU

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CTGAN/TVAE/CopulaGAN constructor raises a missing-module error | `ctgan` or torch dependencies are unavailable. | Install SDV with deep-model dependencies in the runtime, or switch to `GaussianCopulaSynthesizer` for a CPU-friendly workflow. Verify `import ctgan` and `import torch` before retrying. |
| `InvalidDataTypeError` for pandas `category` dtype | CTGAN/TVAE reject columns stored as pandas categorical dtype. | Cast affected columns to `object` before fitting: `data[col] = data[col].astype('object')`. Keep metadata sdtype as categorical if semantically categorical. |
| CUDA or device mismatch during load | A deep model was saved from a GPU-backed run and loaded on a CPU-only machine. | This load path is unsupported by SDV. Sample on a compatible GPU-enabled machine, or retrain and save with `enable_gpu=False` for CPU portability. |
| Deprecated `cuda` argument confusion | Old code passes `cuda`; new code should use `enable_gpu`. | Replace `cuda=False` with `enable_gpu=False`. If both are present, remove `cuda` unless maintaining old behavior intentionally. |
| GPU expected but training is slow or CPU-bound | Torch cannot use a compatible GPU or `enable_gpu=False` was passed. | Verify torch GPU availability in the runtime. Recreate the synthesizer with `enable_gpu=True` only if the runtime supports it. |

## Transformer and Constraint Warnings

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `get_transformers` returns no transformers | Defaults have not been assigned yet. | Call `auto_assign_transformers(real_data)` or `fit(real_data)` first. |
| Transformer already fitted error | A fitted RDT transformer instance was passed to `update_transformers`. | Create a fresh unfitted transformer instance. |
| Key column transformer error | A primary/alternate/sequence key is being transformed with a non-generator transformer. | Use SDV/RDT generator-style key transformers or leave key handling to defaults. |
| Quality warning after replacing categorical/boolean transformers | Deep models rely on default categorical/boolean handling; replacements can reduce quality. | Keep defaults unless there is a clear reason. If changing them, compare quality in the evaluation workflow after refitting. |
| GaussianCopula OneHot warning | One-hot encoding can slow GaussianCopula preprocessing/modeling. | Prefer default categorical handling unless one-hot encoding is required for the task. |
| Rounding warning | A transformer cannot disable its rounding scheme while the synthesizer has `enforce_rounding=True`. | Set `enforce_rounding=False` on a new synthesizer or use a compatible transformer. |
| Refit warning after `update_transformers` or `preprocess` | The synthesizer was already fitted and its data-processing state changed. | Call `fit(real_data)` or `fit_processed_data(processed)` again before sampling. |
| Scalar constraint deprecation warning | Legacy `ScalarInequality`, `ScalarRange`, `Positive`, or `Negative` constraints are being used. | Prefer non-scalar or newer constraint patterns when possible. If preserving old behavior, accept the warning and verify sampled rows with `validate_constraints`. |
| `set_constraints` error because constraints already exist | Deprecated JSON constraint loader was called after constraints were applied. | Build a new synthesizer, then either use `set_constraints` before any other constraints or, preferably, instantiate constraints and call `add_constraints`. |

## Learned Distributions, Parameters, and Loss Values

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `get_learned_distributions` says distributions have not been learned | GaussianCopula/CopulaGAN was not fitted. | Call `fit` first. If no numerical columns are statistically modeled, an empty dict can be valid after fit. |
| `get_parameters` fails with non-parametric distributions | A GaussianCopula/CopulaGAN workflow used `gaussian_kde`. | Use a parametric distribution (`beta`, `norm`, `truncnorm`, `uniform`, `gamma`) if parameters must be extracted. |
| `get_loss_values` / `get_loss_values_plot` raises `NotFittedError` | Deep model was not fitted. | Call `fit` first. Loss APIs apply to CTGAN, TVAE, and CopulaGAN, not GaussianCopula or DayZ parameter creation. |
| Loss plot does not show expected columns | Underlying model loss history differs from expected generator/discriminator columns. | Inspect `get_loss_values()` first. Use custom plotting if columns differ. |

## DayZ Parameter Errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `DayZSynthesizer(metadata)` raises `SynthesizerInputError` | Community SDV exposes only DayZ parameter creation/validation. | Use `DayZSynthesizer.create_parameters(data, metadata, filepath=None)` and `validate_parameters`. Actual DayZ synthesis requires an enterprise-supported runtime. |
| `Data is empty` or `Metadata is empty` | Creating parameters without rows or without a table. | Provide a non-empty DataFrame and metadata with one table. |
| Unexpected DayZ key or unsupported spec version | Parameter dict includes keys outside `DAYZ_SPEC_VERSION`, `tables`, `relationships`, or has a non-`V1` version. | Remove unknown keys and use `DAYZ_SPEC_VERSION: 'V1'`. |
| Multi-table metadata or relationships error | Single-table DayZ validation saw multiple tables or `relationships`. | Use a single-table metadata object, or route to the multi-table DayZ workflow. |
| Missing table/column in metadata | Parameters reference a table/column not in metadata. | Align parameter dict names to metadata. |
| Invalid `num_rows` | `num_rows` is missing where required by the downstream task, non-integer, or non-positive. | Use a positive integer. |
| Invalid `missing_values_proportion` | Value is not numeric in `[0.0, 1.0]`, or a key column has nonzero missingness. | Use a float between 0 and 1; set key-column missingness to `0.0`. |
| Invalid numerical min/max or decimal digits | `min_value > max_value`, non-numeric min/max, or negative/non-integer decimal digits. | Correct bounds and use a non-negative integer for `num_decimal_digits`. |
| Invalid datetime timestamps | Timestamps are not strings, do not match metadata `datetime_format`, or start is after end. | Format timestamps according to metadata and ensure `start_timestamp <= end_timestamp`. |
| Invalid categorical values | `category_values` is not a list. | Provide a list of categories, or omit it for all-null categorical columns. |

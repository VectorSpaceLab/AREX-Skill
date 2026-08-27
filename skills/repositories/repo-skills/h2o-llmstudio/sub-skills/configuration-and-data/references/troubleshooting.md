# Troubleshooting configuration and data issues

Start with the read-only checks:

```bash
python skills/disco/h2o-llmstudio/sub-skills/configuration-and-data/scripts/inspect_config.py --config CONFIG.yaml --expect-problem-type text_causal_language_modeling
python skills/disco/h2o-llmstudio/sub-skills/configuration-and-data/scripts/validate_dataset.py --config CONFIG.yaml
```

Run from a project/runtime root that contains the local prompt-template assets, or pass `--root` to the scripts.

## Common symptoms

| Symptom | Likely cause | Fix |
|---|---|---|
| `Problem Type ... not implemented` | YAML `problem_type` is missing or not one of the exact supported values. | Use one of the five values in `problem-types.md`. |
| `inspect_config.py` reports unknown keys | The YAML contains a typo, stale field, or fields for a different problem type. | Fix the key, switch `problem_type`, or regenerate a normalized YAML with `--write-roundtrip` after confirming the loss of the field is acceptable. |
| Config loads but behaves like the wrong task | `problem_type` selected the wrong dataclass tree. | Re-run with `--expect-problem-type`; change the YAML problem type and rebuild problem-specific fields. |
| Config loading fails from an unrelated directory | Config constructors resolve some local assets, such as prompt templates, relative to the current working directory. | Run from the project/runtime root or pass `--root PROJECT_ROOT`. |
| `Could not determine type of file` | Direct dataframe readers were given an unsupported extension. | Use `.csv`, `.pq`, or `.parquet`. Zip archives are for import flows, not direct dataframe reading. |
| Missing prompt column | `prompt_column` points to a column absent from the dataframe. | Rename the dataframe column or update `dataset.prompt_column`. |
| Missing answer column | `answer_column` or `rejected_answer_column` points to a missing column. | Update the YAML or add the required column. DPO needs both chosen and rejected answer columns. |
| `contains missing values` | Required answer/target values are null. | Fill or remove missing labels/answers. Prompt columns are filled/dropped earlier, but answer/target columns must remain valid. |
| Parent chain is ignored | `parent_id_column` is set but absent from the dataframe. | Add the parent-id column or set `parent_id_column: None` to make single-turn rows explicit. |
| `ID column is required for conversation chaining` | Parent IDs are enabled but `id_column` is not available. | Add an id column with unique values and set `dataset.id_column`. |
| `None of the Parent IDs ... were found in the Id Column` | Parent IDs do not reference available ids. | Ensure parent IDs match ids exactly after CSV/Parquet type conversion. |
| `ID list contains duplicate values` | Chained conversation ids are not unique. | Make `id_column` unique before import. |
| `Circular reference detected` or max loop count exceeded | Conversation rows contain a parent cycle. | Break the cycle and ensure each chain reaches a root row. |
| `Parent ID column is not supported for classification/regression` | Classification or regression YAML still has parent-id settings. | Remove parent-id fields or switch to a generation problem type. |
| Classification labels fail to cast to int | Target columns contain strings/floats that cannot be interpreted as integer labels. | Encode labels as integer values before validation. |
| `BinaryCrossEntropyLoss requires num_classes == 1` | Binary/multilabel settings are mixed with multiclass settings. | For binary use one 0/1 column and `num_classes: 1`; for multiclass use `CrossEntropyLoss` and one class column. |
| `Wrong number of classes for multilabel classification` | Multiple answer columns are selected but `num_classes` does not equal the number of columns. | Set `num_classes` to the number of multilabel target columns. |
| Regression target failure | Target columns contain non-float values or nulls. | Convert targets to numeric floats and remove invalid rows. |
| DPO dataset assertion for `limit_chained_samples` | DPO requires complete final-turn preference samples. | Keep `dataset.limit_chained_samples: true`. |
| Rejected prompt mismatch | `rejected_prompt_column` is set but the column is missing, or it is set when chosen/rejected prompts are actually shared. | Keep `rejected_prompt_column: None` unless prompts differ; otherwise add the named column. |
| `No GPU selected` or selected GPUs exceed available devices | Config was created on another machine or GPU selection is empty. | Re-select available GPU string indices before training. Dataset validation itself does not need training to run. |
| DeepSpeed plus int4/int8 error | DeepSpeed is enabled with quantized backbone dtype. | Use float16/bfloat16 for DeepSpeed or disable DeepSpeed. |

## Recovery checklist

1. Inspect the YAML with the expected problem type.
2. Remove unknown/dropped keys before training.
3. Validate dataset files with the final YAML.
4. For chained data, inspect id and parent-id roots before automatic validation splitting.
5. Only after config/data validation succeeds, route training tasks to `training-and-experiments`.

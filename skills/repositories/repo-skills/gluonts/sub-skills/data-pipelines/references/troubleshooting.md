# Data-pipeline troubleshooting

## PandasDataset construction

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError: You need to provide freq along with timestamp` | A `timestamp` column was provided without an explicit frequency. | Pass `freq`, e.g. `PandasDataset(df, timestamp="timestamp", freq="H", target="value")`. |
| Frequency inference fails or produces an unexpected frequency | The index is too short, irregular, or pandas inferred an anchored start frequency that is not usable for the target workflow. | Pass `freq` explicitly and ensure the index is uniformly spaced. |
| `Dataframe index is not uniformly spaced` | Gaps, duplicates, unsorted timestamps, or multiple items are mixed in one target column. | For one item, sort/resample/fill to a uniform index. For many items in one table, use `PandasDataset.from_long_dataframe(...)`. Use `unchecked=True` only after independent validation. |
| Static object/string columns disappear | `static_features` object dtype columns are intentionally ignored. | Convert categorical static columns with `astype("category")`; keep numeric static columns numeric. |
| Missing or wrong static features for keyed pandas data | `static_features` index does not match the item ids from the dictionary or `(item_id, dataframe)` pairs. | Reindex the static dataframe to exactly the item ids used by `dataframes`. |
| Static columns in a long dataframe assert or duplicate unexpectedly | A `static_feature_columns` value changes within one item. | Move that column to a dynamic feature, or reduce it to one constant value per item before construction. |
| Dynamic feature shape surprises | `PandasDataset` transposes dynamic feature columns into `(num_features, T)`. | Inspect one entry with `next(iter(dataset))` before training. Multivariate targets are also transposed to `(target_dim, T)`. |
| Last target values are missing | `future_length` removed the last observations from `target` and `past_feat_dynamic_real`. | Use `future_length` only when the dataframe intentionally includes known-future rows for dynamic features. |

## ListDataset and FileDataset validation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Object is missing a required field target` | Each entry must contain `target`. | Add `target` or use `translate` to map your source field to `target`. |
| Error while reading field `start` | `start` cannot be converted to `pd.Period(start, freq)` or `pd.Timestamp(start)`. | Check date strings and frequency. Use `use_timestamp=True` only if downstream code accepts timestamps instead of periods. |
| `Array 'target' has bad shape` | `one_dim_target=True` but the target is multivariate, or a static/dynamic field has the wrong rank. | Set `one_dim_target=False` for multivariate targets. Static features must be 1-D; dynamic features must be 2-D. |
| Dynamic real feature is one-dimensional | `ProcessDataEntry` expects dynamic fields shaped `(num_features, T)`. | Wrap one feature as `[values]`, not just `values`. |
| Categorical feature dtype issues | `feat_static_cat` and `feat_dynamic_cat` are converted to integer arrays. | Encode categories as integer ids before `ListDataset`/`FileDataset`, or use pandas categorical static features with `PandasDataset`. |

## File loading

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `FileNotFoundError` | The file/directory path does not exist in the current environment. | Resolve the dataset path in the caller's project; the generated skill does not require the original GluonTS checkout. |
| `Cannot infer loader` warning | File suffix is not a recognized JSON Lines or optional Arrow/Parquet suffix. | Use `.json`, `.jsonl`, `.json.gz`, `.jsonl.gz`, `.arrow`, `.feather`, or `.parquet`; or provide `loader_class`. |
| `Cannot find any loadable data` | Directory traversal found no supported files, hidden files were ignored, or optional Arrow support is unavailable. | Check `pattern`, `levels`, and `ignore_hidden`; install `pyarrow`/the Arrow extra for Arrow and Parquet files; use JSON Lines as a fallback. |
| JSON line parse error | A line is not a complete JSON object. | Validate that each line is independent JSON and not a pretty-printed multi-line object. |
| File-backed iteration is slow on repeated passes | Entries are re-read and processed each time. | Use `cache=True` for small/medium datasets when repeated iteration is required and memory use is acceptable. |
| Arrow import fails | Arrow support is optional and not part of the minimum base workflow. | Install a compatible `pyarrow` or avoid Arrow by writing JSON Lines. Treat Arrow claims as optional unless verified in the active environment. |

## Splitting failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `You need to provide offset or date, but not both` | `split` received both arguments or neither. | Call exactly one of `split(dataset, offset=...)` or `split(dataset, date=pd.Period(...))`. |
| `Not enough data to generate some of the windows` | Split point is too late for `prediction_length`, `windows`, and `distance`. | Move the split earlier. For `windows=N` trailing non-overlapping windows, use `offset=-(prediction_length * N)` rather than `offset=-prediction_length`. |
| Label start does not match expectation | Date split includes the provided period in training; offset split uses integer positions. | For date splits, first label begins one period after the inclusive date. For offset splits, first label begins at the offset position. |
| Date split yields wrong horizon alignment | The `pd.Period` frequency differs from entry `start.freq`. | Construct the split date with the same frequency string as the dataset entries. |
| Dynamic features appear longer than target in test inputs | Known dynamic features are intentionally extended through the forecast horizon. | For features known only in the past, store them as `past_feat_dynamic_real`; use `feat_dynamic_real` only for known-future covariates. |
| `max_history` removes too much input context | `max_history` truncates generated input entries to their trailing history. | Increase or remove `max_history` when predictors need longer context. |

## Practical debug pattern

Before training or evaluating, inspect a tiny sample:

```python
from gluonts.dataset.field_names import FieldName

entry = next(iter(dataset))
print(entry[FieldName.START], entry[FieldName.TARGET].shape)
for name in ["feat_static_cat", "feat_static_real", "feat_dynamic_real", "past_feat_dynamic_real"]:
    if name in entry:
        print(name, entry[name].shape)
```

Then run a one-window split:

```python
from gluonts.dataset.split import split

prediction_length = 3
train, template = split(dataset, offset=-prediction_length)
input_entry, label_entry = next(iter(template.generate_instances(prediction_length=prediction_length)))
assert label_entry["target"].shape[-1] == prediction_length
assert label_entry["start"] == input_entry["start"] + input_entry["target"].shape[-1]
```

If these assertions fail, fix frequency, target shape, feature lengths, or split position before moving to transforms, model training, or evaluation.

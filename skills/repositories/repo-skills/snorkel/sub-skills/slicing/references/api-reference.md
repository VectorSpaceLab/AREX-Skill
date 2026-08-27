# API reference

This page summarizes the slicing API that future agents should reach for first.

## Slice function creation

| Member | Use | Notes |
| --- | --- | --- |
| `SlicingFunction` | Callable wrapper for slice logic | Behaves like Snorkel's labeling-function wrapper, but is used for binary slice membership. |
| `slicing_function(name=None, resources=None, pre=None)` | Decorator for simple slice functions | Use `@slicing_function()`; missing parentheses raises a `ValueError`. |
| `NLPSlicingFunction` | spaCy-backed slice function | Use when slice logic depends on parsed text fields such as entities or tokens. Shares a cached preprocessor across instances. |
| `nlp_slicing_function(name=None, resources=None, pre=None, text_field='text', doc_field='doc', language=..., disable=None, memoize=True, memoize_key=None, gpu=False)` | Decorator for NLP slice functions | Keep preprocessing details here; route deeper spaCy mechanics to the data-transforms skill. |

## Appliers

| Member | Input | Output / notes |
| --- | --- | --- |
| `SFApplier([...])` | List of data points or NumPy objects | Returns a named-field `np.recarray` whose fields are the slice-function names. |
| `PandasSFApplier([...])` | Pandas `DataFrame` | Same named-field `np.recarray` behavior as `SFApplier`. |
| `DaskSFApplier([...])` | Dask `DataFrame` | Optional Dask/Distributed backend; same named-field `np.recarray` behavior as the Pandas-style appliers. |
| `PandasParallelSFApplier([...])` | Pandas `DataFrame` | Optional Dask/Distributed backend for parallel Pandas application; use `n_parallel >= 2`. |
| `SparkSFApplier([...])` | Spark `RDD` | Optional PySpark + Java backend; follows the Spark applier pattern and returns the standard dense label matrix rather than a named-field recarray. |

## Monitoring and slice utilities

| Member | Use | Notes |
| --- | --- | --- |
| `slice_dataframe(df, sf)` | Filter a Pandas `DataFrame` to one slice | Convenience wrapper around `PandasSFApplier([sf])`; keeps only rows where the slice function is active. |
| `add_slice_labels(dataloader, base_task, S)` | Add slice labels to a `DictDataLoader` | Mutates `dataloader.dataset.Y_dict` in place. Adds `base` if needed, then creates `*_ind` and `*_pred` labels. `pred` labels are masked with `-1` outside the slice. |
| `convert_to_slice_tasks(base_task, slice_names)` | Expand one base task into slice tasks | Creates the base task plus `*_ind` and `*_pred` tasks for the base slice and each named slice. Mutates the base task's module pool in place. |

## Slice-aware modeling

| Member | Use | Notes |
| --- | --- | --- |
| `SliceCombinerModule(slice_ind_key='_ind_head', slice_pred_key='_pred_head', slice_pred_feat_key='_pred_transform', temperature=1.0)` | Combine slice representations | Uses indicator logits and predictor confidence to reweight slice features. Binary only. Predictor heads must output exactly 2 logits. |
| `SliceAwareClassifier(base_architecture, head_dim, slice_names, input_data_key='input_data', task_name='task', scorer=Scorer(metrics=['accuracy', 'f1']), **multitask_kwargs)` | Build a slice-aware multitask classifier | Creates a base task plus slice indicator/predictor tasks, stores the base task on the instance, and exposes `make_slice_dataloader(...)` and `score_slices(...)`. Binary classification only. |
| `SliceAwareClassifier.make_slice_dataloader(dataset, S, **dataloader_kwargs)` | Attach slice labels to a `DictDataset` | Requires the base task labels in `dataset.Y_dict`; adds `base`, `*_ind`, and `*_pred` labels in place through `add_slice_labels`. |
| `SliceAwareClassifier.score_slices(dataloaders, as_dataframe=False)` | Evaluate slice-oriented metrics | Remaps every `pred` label to the base task and skips `ind` labels. Can return a DataFrame. |

### Scoring behavior

- `score(...)` reports metrics for every label present in the dataloader under `label/dataset/split/metric`.
- `score_slices(...)` keeps the slice names in the output but evaluates them using the base task head and ignores `ind` labels.

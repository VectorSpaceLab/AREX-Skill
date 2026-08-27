# Troubleshooting

Use this guide for the most common slice-function and slice-aware model issues.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Looks like this decorator is missing parentheses!` | Used `@slicing_function` instead of `@slicing_function()` | Add the parentheses and pass `name`, `resources`, or `pre` to the decorator call if needed. |
| A slice looks empty even though the logic should match rows | The active branch returns `0` or another falsey value | Return `1` or `True` for in-slice membership so the mask stays active later. |
| `KeyError` or missing field when indexing `S[...]` | Slice names do not match the recarray field names | Check `S.dtype.names`; each field comes from the slice-function name. |
| `S`, `golds`, `preds`, and `probs` must have the same number of elements | The slice matrix and score inputs were built from different example orders or lengths | Rebuild them from the same examples in the same order. |
| `Base task (...) labels missing from DictDataset(...)` | The dataset does not contain the base task key in `Y_dict` | Add the base labels before calling `make_slice_dataloader`. |
| `pred` labels contain `-1` values outside the active rows | This is expected masking behavior | `ind` labels mark slice membership; `pred` labels keep the base labels only inside the slice. |
| `score_slices(...)` returns fewer labels than `score(...)` | It intentionally skips indicator labels | Use `score(...)` if you want every label scored, or `score_slices(...)` if you only want slice-oriented evaluation. |
| `SliceCombiner does not support more than 2 classes yet.` | Tried to use multiclass slice-aware modeling | These helpers are binary-only; keep the base head at 2 classes or build a custom model. |
| `SparkSFApplier` does not give named fields | Spark output follows the dense Spark applier pattern | Use the Pandas/Dask-style appliers when you need a named-field recarray for downstream slice utilities. |
| `DaskSFApplier`, `PandasParallelSFApplier`, `SparkSFApplier`, or `NLPSlicingFunction` fail to import or initialize | Missing optional backend packages or runtime support | Install the matching backend stack: Dask/Distributed, PySpark + Java, or spaCy + a language model. |
| `PandasParallelSFApplier` rejects the request | `n_parallel` was less than 2 | Use `PandasSFApplier` for single-process Pandas runs. |
| `convert_to_slice_tasks` changed my original task | The helper mutates the base task's module pool in place | Build from a fresh `Task` if you need to keep the original task untouched. |

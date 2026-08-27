# Workflows

## 1) Build an `S` matrix

Use this path when you need slice membership for a full dataset.

1. Define each slice with `@slicing_function()` or `@nlp_slicing_function(...)`.
2. Pick `SFApplier` for list-like inputs or `PandasSFApplier` for `DataFrame` inputs.
3. Apply the same row order you will use downstream.
4. Inspect `S.dtype.names` to confirm the field names.

```python
@slicing_function()
def short_text(x):
    return int(len(x.text) < 80)

S = PandasSFApplier([short_text]).apply(df, progress_bar=False)
assert S.dtype.names == ("short_text",)
```

If a slice should be active, return a truthy membership value such as `True` or `1`. Falsey values are treated as off-slice later.

## 2) Monitor one slice in a DataFrame

Use `slice_dataframe(df, sf)` when you only need the rows for a single slice.

```python
subset = slice_dataframe(df, short_text)
```

This is a convenience wrapper around `PandasSFApplier([sf])`. If you need multiple slices at once, keep the `S` matrix instead of filtering one slice at a time.

## 3) Add slice labels to an existing loader

Use this when you already have a base `DictDataset` and want slice-aware labels.

1. Build a `DictDataset` that already contains the base task labels.
2. Wrap it in `DictDataLoader`.
3. Call `add_slice_labels(dataloader, base_task, S)`.

This adds:
- `base_ind`: all ones
- `base_pred`: a copy of the base labels
- `{slice}_ind`: the slice membership mask
- `{slice}_pred`: the base labels masked with `-1` outside the slice

```python
add_slice_labels(dataloader, base_task, S)
print(dataloader.dataset.Y_dict["task_slice:my_slice_pred"])
```

## 4) Convert a base task into slice tasks

Use `convert_to_slice_tasks(base_task, slice_names)` when you are assembling a custom `MultitaskClassifier`.

1. Start from a fresh base `Task`.
2. Pass the slice names you want to learn.
3. Use the returned tasks to build the model.

The helper creates:
- the base task
- `*_ind` tasks for the base slice and each named slice
- `*_pred` tasks for the base slice and each named slice

Important: the base task's module pool is mutated in place. Keep a fresh task object if you also need an unmodified version.

## 5) Train and score a slice-aware classifier

Use `SliceAwareClassifier` when you want the model to manage the slice-task expansion for you.

1. Build a binary base architecture whose final representation has dimension `head_dim`.
2. Build `S` from the exact examples and row order used by your dataset.
3. Call `make_slice_dataloader(dataset, S, batch_size=...)`.
4. Train with the standard classification trainer.
5. Call `score(...)` for all labels or `score_slices(...)` for slice-oriented evaluation.

```python
model = SliceAwareClassifier(...)
dl = model.make_slice_dataloader(dataset, S, batch_size=32)
scores = model.score([dl])
slice_scores = model.score_slices([dl], as_dataframe=True)
```

`score_slices(...)` keeps the slice names in the output, but it evaluates them using the base task head.

## 6) Scale out the applier

- Use `DaskSFApplier` or `PandasParallelSFApplier` for Dask-backed Pandas workflows.
- Use `SparkSFApplier` for Spark RDDs.
- Keep the same slice functions; only the input container changes.
- If an optional backend is missing, fall back to `SFApplier` or `PandasSFApplier`.

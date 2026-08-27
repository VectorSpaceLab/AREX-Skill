# Evaluation and plotting API reference

## Public functions

### `evaluate(ground_truth_map=None, retrieved_map=None, metric='all')`

Returns a dictionary of evaluation results.

Metric options:

- `map`
- `ndcg`
- `jaccard`
- `classification`
- `all`

Behavior notes:

- The ground-truth and retrieved maps must contain the same keys.
- Both maps must be symmetric: if `A` lists `B`, then `B` must list `A`.
- `metric='all'` combines information-retrieval and classification metrics.
- `classification` returns per-class precision, recall, F1, and support as numpy arrays.
- `map`, `ndcg`, and `jaccard` return one-number dictionaries.

### `plot_duplicates(image_dir, duplicate_map, filename, outfile=None)`

Plots one image and its duplicate group.

Behavior notes:

- `duplicate_map` may contain plain filenames or `(filename, score)` tuples.
- `filename` must be a key in the map.
- The duplicate list for that key must be non-empty.
- If `outfile` is provided, the figure is saved there.

## Metric interpretation

### Information-retrieval metrics

- `MAP`: mean average precision
- `NDCG`: normalized discounted cumulative gain
- `Jaccard`: overlap of retrieved and correct duplicate sets

These metrics treat each key as an independent query.

### Classification metrics

- `precision`
- `recall`
- `f1_score`
- `support`

These metrics collapse symmetric duplicate relationships into unique unordered pairs.

## Validation rules that matter

- Ground-truth and retrieved maps must have exactly the same key set.
- Duplicate relationships must be symmetric in both maps.
- Missing symmetry or missing keys is a validation error, not a warning.

## When to read this file

Read this file when you need to know what `evaluate` returns, how the metrics differ, or what `plot_duplicates` expects from the duplicate map.
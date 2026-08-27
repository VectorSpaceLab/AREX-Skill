# Evaluation and inference

This reference covers the package surface for measuring retrieval quality and doing nearest-neighbor inference.

## AccuracyCalculator

```python
AccuracyCalculator(
    include=(),
    exclude=(),
    avg_of_avgs=False,
    return_per_class=False,
    k=None,
    label_comparison_fn=None,
    device=None,
    knn_func=None,
    kmeans_func=None,
)
```

### Key parameters

- `include` / `exclude`: select the metrics to compute.
- `avg_of_avgs`: average over classes first, then average again.
- `return_per_class`: return a class-wise list instead of a single scalar.
- `k`: `None`, a positive integer, or `"max_bin_count"`.
- `label_comparison_fn`: custom equivalence function for 1D or 2D labels.
- `device`: evaluation device for tensors.
- `knn_func`: custom nearest-neighbor backend. Defaults to faiss-backed KNN.
- `kmeans_func`: custom clustering backend. Defaults to faiss-backed KMeans.

### Default metrics

- `NMI`
- `AMI`
- `precision_at_1`
- `r_precision`
- `mean_average_precision_at_r`
- `mean_average_precision`
- `mean_reciprocal_rank`

### Important evaluation rules

- Set `ref_includes_query=True` when the query set is part of the reference set.
- Use `k="max_bin_count"` when you want the metric to adapt to the number of reference examples per label.
- `mean_average_precision_at_r` and `r_precision` are only correct when `k` is large enough for the label distribution.
- Custom label comparison functions are compatible with 1D or 2D labels, but clustering metrics do not mix with custom comparison logic.

## Tester map

| Tester | Best for | Shape notes |
| --- | --- | --- |
| `GlobalEmbeddingSpaceTester` | Standard retrieval evaluation over the full embedding space | Dataset dict maps split names to datasets that yield `(input, label)` |
| `WithSameParentLabelTester` | Hierarchical retrieval where siblings share a parent label | Labels should be 2D, with the parent label available at the configured hierarchy level |
| `GlobalTwoStreamEmbeddingSpaceTester` | Two-stream datasets where anchor and positive/negative come from different sources | Dataset items must be `(anchor, positive, label)` |

### Tester workflow

1. Build a `dataset_dict` keyed by split name.
2. Build the tester, optionally passing a custom `AccuracyCalculator`.
3. Call `tester.test(dataset_dict, epoch, trunk, embedder=None, splits_to_eval=None, collate_fn=None)`.
4. Read the returned accuracy dictionary or the tester's `all_accuracies` attribute.

Important tester options:

- `normalize_embeddings`: normalize before nearest-neighbor scoring.
- `pca`: optional dimensionality reduction before scoring.
- `use_trunk_output`: skip the embedder if the trunk output is already the final representation.
- `batch_size`, `dataloader_num_workers`, `data_device`, `dtype`: evaluation execution controls.
- `label_hierarchy_level`: select the label depth to evaluate.
- `set_min_label_to_zero`: remap arbitrary labels to ranks.
- `visualizer` and `visualizer_hook`: optional 2D projection and visualization hooks.

## InferenceModel

```python
InferenceModel(
    trunk,
    embedder=None,
    match_finder=None,
    normalize_embeddings=True,
    knn_func=None,
    data_device=None,
    dtype=None,
)
```

### Common methods

- `train_knn(inputs, batch_size=64)`
- `add_to_knn(inputs, batch_size=64)`
- `get_nearest_neighbors(query, k)`
- `is_match(x, y, threshold=None)`
- `get_matches(query, ref=None, threshold=None, return_tuples=False)`
- `save_knn_func(filename)` / `load_knn_func(filename)`

### Backend choices

- `FaissKNN` is the default k-NN backend.
- `CustomKNN` uses a distance object and can be easier for CPU-only experiments or testing.
- `FaissKMeans` is useful for clustering-based metrics or custom workflows.
- `MatchFinder` converts a distance or similarity into a match/no-match decision.

### Tiny-input patterns

- A list of tensors can be stacked automatically.
- A `torch.utils.data.Dataset` can be indexed and embedded in batches.
- A plain tensor or list of tensors works when the trunk accepts that type.

## EmbeddingDataset helper

`pytorch_metric_learning.utils.common_functions.EmbeddingDataset` is a tiny in-memory dataset that returns `(embedding, label)` pairs.

It is useful for:

- evaluation smoke tests,
- tiny trainer smoke tests,
- tester examples where the inputs are already embeddings.

## Cross-check against the tests

Useful native references for this layer include:

- `tests/utils/test_calculate_accuracies.py`
- `tests/testers/test_global_embedding_space_tester.py`
- `tests/testers/test_with_same_parent_label_tester.py`
- `tests/testers/test_global_two_stream_embedding_space_tester.py`
- `tests/utils/test_inference.py`

# Metrics and re-ranking

This reference covers the distance, rank, and re-ranking utilities used after feature extraction.

## Distance matrices

### `torchreid.metrics.compute_distance_matrix(input1, input2, metric='euclidean')`

- `input1` and `input2` must both be 2-D `torch.Tensor` objects with the same feature dimension.
- Returns a `torch.Tensor` with shape `(input1.size(0), input2.size(0))`.
- Supported metrics:
  - `euclidean`: **squared** Euclidean distance, not square-root distance.
  - `cosine`: `1 - cosine_similarity`, after L2-normalizing each row.

Typical use:

```python
q_feat = extractor(query_images)    # shape (Nq, D)
g_feat = extractor(gallery_images)  # shape (Ng, D)
distmat = torchreid.metrics.compute_distance_matrix(q_feat, g_feat, metric='euclidean')
```

## Rank evaluation

### `torchreid.metrics.evaluate_rank(distmat, q_pids, g_pids, q_camids, g_camids, max_rank=50, use_metric_cuhk03=False, use_cython=True)`

- `distmat` must be a NumPy array with shape `(num_query, num_gallery)`.
- `q_pids`, `g_pids`, `q_camids`, and `g_camids` must be 1-D NumPy arrays with lengths matching the query/gallery counts.
- Returns `(cmc, mAP)`.
- `cmc` is a NumPy array; `mAP` is a scalar float.

### Metric semantics

- **Market1501 metric** (`use_metric_cuhk03=False`): gallery entries with the same person ID and camera ID as the query are removed.
- **CUHK03 metric** (`use_metric_cuhk03=True`): one gallery image per identity is sampled randomly for each query identity, repeated 10 times.
- If the gallery is smaller than `max_rank`, the implementation truncates `max_rank` to the gallery size.
- If none of the query identities appear in the gallery, evaluation raises:

```text
AssertionError: Error: all query identities do not appear in gallery
```

### Cython fallback

- `use_cython=True` is preferred when the compiled extension is available.
- If the extension cannot be imported, the code falls back to the Python implementation and warns once.
- The Python and Cython paths should agree on the reported metrics.

### Legacy speed demo

- `torchreid.metrics.rank_cylib.test_cython.py` is a randomized speed/precision demo.
- It is not a stable correctness harness because random inputs can trigger the no-query-match assertion.
- For actual feature-extraction workflows, prefer direct `evaluate_rank(...)` calls on real embeddings and labels.

## Re-ranking

### `torchreid.utils.re_ranking(q_g_dist, q_q_dist, g_g_dist, k1=20, k2=6, lambda_value=0.3)`

- Input arrays must be NumPy distance matrices.
- Shapes:
  - `q_g_dist`: `(num_query, num_gallery)`
  - `q_q_dist`: `(num_query, num_query)`
  - `g_g_dist`: `(num_gallery, num_gallery)`
- Returns the adjusted query-gallery distance matrix with shape `(num_query, num_gallery)`.
- The implementation is the standard k-reciprocal encoding re-ranking algorithm.

### Re-ranking workflow

1. Compute query-gallery, query-query, and gallery-gallery distances.
2. Convert the three matrices to NumPy.
3. Pass them into `re_ranking(...)`.
4. Feed the returned query-gallery matrix into `evaluate_rank(...)` if labels are available.

Example:

```python
q_g = compute_distance_matrix(q_feat, g_feat, metric='cosine').cpu().numpy()
q_q = compute_distance_matrix(q_feat, q_feat, metric='cosine').cpu().numpy()
g_g = compute_distance_matrix(g_feat, g_feat, metric='cosine').cpu().numpy()
reranked = torchreid.utils.re_ranking(q_g, q_q, g_g)
cmc, mAP = torchreid.metrics.evaluate_rank(reranked, q_pids, g_pids, q_camids, g_camids)
```

## Auxiliary accuracy helper

### `torchreid.metrics.accuracy(output, target, topk=(1,))`

- Accepts classification logits or a tuple/list whose first element is the logits tensor.
- Returns a list of top-k accuracies in percent.
- This helper is mostly relevant when a model is in a classification/training path rather than a pure embedding path.

## Optional GPU re-ranking

- The separate GPU-Re-Ranking extension shipped with Torchreid is optional and hardware-specific.
- It is not part of the default bundled helper scripts for this sub-skill.
- Use the CPU `re_ranking(...)` helper unless you have explicitly prepared and verified the external CUDA extension.

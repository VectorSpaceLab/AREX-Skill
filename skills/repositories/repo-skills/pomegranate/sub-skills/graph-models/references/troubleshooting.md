# Graph Models Troubleshooting

## Distribution type errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Must be Categorical or ConditionalCategorical` from `BayesianNetwork` | A continuous or unsupported distribution was added as a node. | Use `Categorical` for root nodes and `ConditionalCategorical` for child nodes. |
| `Child distribution must be conditional` | Tried to add an edge into a `Categorical` child. | Use `ConditionalCategorical` for nodes that have parents. |
| Factor graph rejects a factor | Factor is not `Categorical` or `JointCategorical`. | Use `Categorical` for univariate factors or `JointCategorical` for multivariate factors. |
| Factor graph rejects an edge | Edge does not connect a marginal to a factor. | Use `(marginal_distribution, factor_distribution)` edge tuples only. |

## Edge and structure mistakes

- `BayesianNetwork` edges are directed `(parent, child)` pairs of distribution objects, not names or indices.
- `FactorGraph` edges are undirected bipartite links but still passed as `(marginal, factor)` pairs.
- Self-loops and edges involving nodes not yet added to the graph are rejected.
- For `structure`, parent tuples are indexed by variable position, not by distribution object.
- Old v0.x code that constructs `State`/`Node` objects and calls `bake()` must be rewritten for v1.x direct distribution objects.

## Categorical data problems

- Graph-model data must be integer-coded categories, usually shaped `(n, d)`.
- Negative values or category ids above the learned table size will fail validation.
- `ConditionalCategorical` probability tensor dimensions must match the parent categories followed by the child category axis.
- Structure learning routines expect categorical integer tensors; do not pass floats or continuous arrays.

## Missing-value inference

- Use `torch.masked.MaskedTensor(X, mask=mask)`.
- `mask=True` means observed and `mask=False` means missing.
- The numeric value stored under a missing mask is ignored, but it should still have a valid tensor dtype.
- `predict_proba` returns a list of per-variable tensors, not one rectangular tensor, because variables can have different category counts.

## Convergence and approximation

Factor-graph inference uses loopy belief propagation/sum-product.

- Tree-like structures produce exact results.
- Acyclic but non-tree structures are expected to converge but may be approximate.
- Cyclic graphs have no guarantee of convergence or exactness.
- Increase `max_iter` or relax/adjust `tol` if a model is close but not converging.
- Use small hand-checkable graphs while debugging edge order and probability tables.

## Structure learning pitfalls

- Use `algorithm='chow-liu'` for tree-structured categorical approximations.
- Use `algorithm='exact'` only for small variable counts because exact structure learning grows quickly.
- `include_parents`, `exclude_parents`, and `max_parents` constrain the learned parent sets; incorrect constraints can prevent the intended structure.
- Add `pseudocount` for sparse categories or zero-count instability.

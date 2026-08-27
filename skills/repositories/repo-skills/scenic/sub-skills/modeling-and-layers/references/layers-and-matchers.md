# Layers, Attention, and Matchers

This reference covers the Scenic layer families that support model construction, shape-preserving smoke checks, and matching utilities for detection-style alignment.

## Layer families and contracts

### Attention and position embeddings

- `dot_product_attention(query, key, value, *, bias=None, bias_kv=None, deterministic, dropout_rng=None, ...)` expects q/k/v tensors with the same rank, matching batch and head dimensions, matching q/k depth, and matching k/v length. The output has the same batch/head/query structure and the value depth.
- `axial_dot_product_attention(...)` is the axial/head-split variant. It requires `query.shape == key.shape`, rejects `bias`, and splits heads across attention axes.
- `MultiHeadAttention(num_heads, qkv_features=None, out_features=None, dropout_rate=0.0, ...)` projects inputs into q/k/v, applies the attention fn, and returns the output in the original feature space. The module uses keyword-only `deterministic` and optional `attention_bias` / `attention_bias_kv`.
- `MlpBlock(mlp_dim, out_dim=None, dropout_rate=0.1, ...)` is the transformer feed-forward block.
- `Add1DPositionEmbedding` expects `[batch, length, channels]` and returns the same shape.
- `Add2DPositionEmbedding` expects `[batch, height, width, channels]` and returns the same shape.
- `AddFixedSinCosPositionEmbedding` accepts `[batch, height, width, channels]` or `[batch, time, height, width, channels]` and adds fixed embeddings.
- `RelativeAttentionBias(num_heads, nd_shape, ...)` returns a learnable bias tensor with shape `[num_heads, length, length]`, where `length = prod(nd_shape)`.

### General NN layers

- `Residual(residual_type='add' | 'highway' | 'rezero' | 'sigtanh' | 'gated')` requires equal input/output shapes.
- `SqueezeAndExcite(reduction_factor=4)` expects 4D inputs in `[batch, height, width, channels]` form.
- `IdentityLayer` is a named no-op wrapper useful for tagging intermediates.
- `Affine` performs per-channel scaling and optional bias on the final dimension.
- `StochasticDepth(rate=..., deterministic=...)` drops whole samples/broadcast slices and preserves the expected activation scale.

### Masked layers and spatial helpers

- `BatchNorm` and `GroupNorm` support optional `spatial_shape` to exclude padded spatial regions from statistics.
- `Conv` returns both the output tensor and the updated spatial shape when `spatial_shape` is provided.
- Masked convolutions with dynamic spatial shapes do not support `'SAME'` padding when the kernel is larger than `1` in any spatial dimension.
- `avg_pool` and `max_pool` preserve or update `spatial_shape` when it is supplied.
- `apply_spatial_mask` and `mask_from_spatial` help keep padded regions zeroed out.
- `pooling` supports `avg_pooling`, `max_pooling`, and `space_to_depth`.
- `weighted_avg_pool` and `weighted_max_pool` return pooled outputs and, optionally, pooled weights.
- `upscale2x_nearest_neighbor`, `central_crop`, `patch_image`, and `extract_image_patches` are useful for tiny geometric smoke checks.
- `compute_relative_positions` and `compute_1d_relative_distance` build offset tables for relative attention lookups.
- `truncated_normal_initializer(stddev=...)` returns a Flax-compatible initializer with the requested standard deviation.

## Matcher families and contracts

Matcher inputs are batched cost matrices with shape `[batch, n_rows, n_cols]`. Match outputs are index pairs with shape `[batch, 2, min(n_rows, n_cols)]`.

| Matcher | Behavior | Notes |
| --- | --- | --- |
| `greedy_matcher` | Fast approximate assignment | Batch-vmapped; useful for quick alignment checks. |
| `hungarian_matcher` | Exact Hungarian assignment | Uses the CPU callback wrapper and requires `scipy`. |
| `hungarian_tpu_matcher` | Exact JAX Hungarian assignment | TPU-friendly JAX implementation. |
| `hungarian_scan_tpu_matcher` | Exact JAX Hungarian assignment | Scan-based exact variant. |
| `hungarian_cover_tpu_matcher` | Exact cover-based assignment | Exact variant exposed for TPU-friendly paths. |
| `lazy_matcher` | Identity assignment | Ignores the cost matrix; useful for smoke tests. |
| `sinkhorn_matcher` | Approximate soft matching | Requires `ott-jax` and samples the best permutation from the transport coupling. |
| `cpu_matcher` | Host-callback wrapper | Converts a pure Python/NumPy matcher into a JIT-callable function with no gradient. |
| `slicer` | Removes padded columns before matching | Use when trailing padded targets would otherwise slow matching or change the assignment cost. |

## Optional dependency considerations

- `scipy` is required for the CPU Hungarian path and for exact-cost comparisons against SciPy assignments.
- `ott-jax` is required for Sinkhorn matching.
- `shapely` may be required by nearby box-utility validation code, but it is not part of the core layer or matcher API surface.
- If the optional dependency is missing, prefer a different matcher path or a tiny shape-only smoke check rather than claiming the whole modeling stack is unavailable.

## Tiny validation patterns

- **Attention:** Create a small q/k/v triple, run the attention fn with and without dropout, and verify the output shape.
- **Multi-head attention:** Check that self-attention preserves the input shape, and if hidden size is not divisible by the head count, only use the non-divisibility path when the module explicitly allows it.
- **Position embeddings:** Verify that learned embeddings change the input by a same-shape additive tensor and that the parameter tensors have the expected shapes.
- **Residual / stochastic depth:** Check that `Residual(add)` gives `x + y` and that stochastic depth preserves the expected mean scale on an all-ones input.
- **Masked layers:** Compare masked padded outputs against the unpadded reference and confirm that padded regions remain zeroed.
- **Exact matchers:** On a tiny cost matrix, compare the total matched cost against SciPy or another exact reference.
- **Approximate matchers:** Use a tiny identity or diagonal cost matrix to confirm that the approximation returns the expected pairing on an easy case.

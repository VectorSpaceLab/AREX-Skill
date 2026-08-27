# Operator Coverage and Fallback

## Decision tree

1. **Is the op unsupported by TensorRT?**
   - Check the exact schema reported by the error or dryrun output.
   - Confirm whether the op is missing because of a converter gap, unsupported dtype/layout, or data-dependent shape behavior.
2. **Can fallback be accepted?**
   - If yes, keep the op in PyTorch with default partitioning or `torch_executed_ops`.
   - If no, continue.
3. **Can the model be rewritten or decomposed?**
   - Prefer this when the rewrite is local, low-risk, and preserves numerics.
4. **Should a custom converter or plugin be written?**
   - Use this when the op is important, stable, and repeated across models.
5. **Is the problem actually a runtime issue?**
   - If compile coverage is fine but execution fails, route to runtime optimization or deployment troubleshooting instead.

## `torch_executed_ops`

Use `torch_executed_ops` to force specific ops to stay in PyTorch. Good cases:

- unsupported but low-cost ops,
- ops with acceptable fallback overhead,
- models where only a few operators need to stay out of TensorRT.

Bad cases:

- forcing a whole bottleneck subgraph to stay in PyTorch,
- using fallback to hide a large unsupported region,
- relying on fallback when a fully TensorRT-optimized model is the actual goal.

## `require_full_compilation`

Set `require_full_compilation=True` when the user explicitly wants every eligible op compiled into TensorRT. This turns partial support into an early failure and is useful for production acceptance tests.

## `min_block_size`

Lowering `min_block_size` can increase coverage, but it can also create tiny TRT partitions that are not worth the runtime overhead. Use it intentionally.

## Common unsupported-op categories

- data-dependent control flow,
- shape-manipulation ops that need custom lowering,
- unsupported reductions or indexing patterns,
- precision/layout combinations that the target backend cannot lower,
- ops that require a custom TensorRT plugin or QDP kernel.

## What to report back to the user

- the exact unsupported op schema,
- whether fallback is enabled,
- which subgraph boundaries were produced,
- whether the fix is likely a model rewrite, converter, plugin, or runtime change,
- what tiny repro proves the issue.

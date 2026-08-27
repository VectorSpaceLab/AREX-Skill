# Parallelism Guide

## Topology terms

- Data parallel (DP): replicates model shards across data batches.
- Tensor parallel (TP): shards tensor operations within layers; ColossalAI docs cover 1D, 2D, 2.5D, and 3D modes conceptually.
- Pipeline parallel (PP): partitions layers into stages; requires microbatching and pipeline-aware loss handling.
- Sequence parallel (SP): shards sequence dimensions or attention-related work for long-context models.
- Expert parallel (EP): shards Mixture-of-Experts experts, usually through MoE hybrid plugin paths.

## Sizing rule

For a world size of `W`, choose topology factors so:

```text
W % (tp_size * pp_size * sp_size * ep_size) == 0
```

The quotient is the data-parallel remainder when no special grouping changes it.

Example with eight processes:

- TP=2, PP=2, SP=1 => DP=2.
- TP=1, PP=4, SP=1 => DP=2.
- TP=2, PP=1, SP=2 => DP=2.

Use `scripts/parallelism_config_advisor.py` to check this before launching.

## Pipeline considerations

Pipeline parallelism changes the loop. Use microbatches and provide a criterion for `booster.execute_pipeline`. Check whether the schedule style is ordinary 1F1B, interleaved, or zero-bubble before interpreting stage outputs.

## Sequence parallelism

Enable sequence parallelism only when the model/policy and attention implementation support the chosen mode. Sequence parallelism can interact with tensor parallelism, ring attention, and fused attention paths.

## Optimization flags

`enable_all_optimization=True` can enable multiple performance paths at once. For safer debugging, enable individual flags one at a time: `enable_fused_normalization`, `enable_flash_attention`, `enable_jit_fused`, `enable_sequence_parallelism`, `fp8_communication`, and `use_fp8`.

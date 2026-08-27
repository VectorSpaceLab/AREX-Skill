# Parallelism and Sharding Troubleshooting

## Topology errors

- World size not divisible by topology product: change `tp_size`, `pp_size`, `sp_size`, `ep_size`, or launched process count.
- Pipeline has no loss: provide a criterion and use Booster pipeline execution.
- Microbatch mismatch: set either `num_microbatches` or `microbatch_size` consistently with batch size.
- Stage imbalance: adjust layer-per-stage settings or pipeline partitions.

## ShardFormer and policy errors

- Unsupported model policy: choose a supported model family, provide a custom policy, or avoid ShardFormer for that model.
- Vocabulary divisibility error: adjust `make_vocab_size_divisible_by` or pad vocabulary where appropriate.
- Sequence parallel mode unsupported: disable sequence parallelism or choose a supported mode/policy.
- Fused normalization/attention error: disable fused flags or install Apex/flash-attn-compatible packages.

## Runtime failures

- NCCL/device mesh failures: verify launch, process counts, GPU visibility, and topology sizing.
- CUDA OOM after sharding: reduce microbatch size, change TP/PP balance, enable checkpointing/offload, or reduce optional fused/kernel memory use.
- Ring attention or long-context failure: confirm sequence parallel support and attention implementation constraints.

## Experimental feature failures

- Missing solver for auto-parallel: install the documented solver dependency in an isolated environment or avoid auto-parallel.
- Version-specific auto-parallel failure: treat the example as experimental and use manual plugin topology for production.
- TensorNVMe missing: disable async/NVMe paths unless that dependency is installed and checked.

# Booster Plugin Guide

| Goal | Start with | Notes |
| --- | --- | --- |
| Basic distributed data parallel training | `TorchDDPPlugin()` | Good first smoke path; mostly delegates to PyTorch DDP. |
| Optimizer-state and gradient sharding | `LowLevelZeroPlugin(stage=1 or 2)` | Stage 1 shards optimizer states; stage 2 also shards gradients. |
| Large model memory management / ZeRO-3-style behavior | `GeminiPlugin(...)` | Uses Gemini/ZeRO DDP, chunk memory, placement/offload knobs. |
| Tensor + pipeline + data parallel combinations | `HybridParallelPlugin(tp_size=..., pp_size=..., zero_stage=...)` | Requires topology choices that divide world size. |
| PyTorch FSDP | `TorchFSDPPlugin(...)` | Available when PyTorch version supports FSDP. |
| Mixture-of-Experts hybrid parallelism | `MoeHybridParallelPlugin(tp_size=..., pp_size=..., ep_size=...)` | Route detailed MoE app scripts to application-recipes. |

## Inspected constructor highlights

- `TorchDDPPlugin(broadcast_buffers=True, bucket_cap_mb=25, find_unused_parameters=False, static_graph=False, fp8_communication=False)`
- `LowLevelZeroPlugin(stage=1, precision='fp16', reduce_bucket_size_in_m=12, overlap_communication=True, cpu_offload=False, master_weights=True, extra_dp_size=1)`
- `GeminiPlugin(placement_policy='static', precision='fp16', shard_param_frac=1.0, offload_optim_frac=0.0, offload_param_frac=0.0, min_chunk_size_m=32, gpu_margin_mem_ratio=0.0, tp_size=1, extra_dp_size=1, enable_flash_attention=False, enable_sequence_parallelism=False)`
- `HybridParallelPlugin(tp_size, pp_size, sp_size=None, precision='fp16', zero_stage=0, num_microbatches=None, microbatch_size=None, pp_style='1f1b', num_model_chunks=1, enable_sequence_parallelism=False)`

## Decision questions

1. How many processes/GPU workers will run? If the answer is one, use DDP/low-risk plugin smoke first.
2. Is the bottleneck optimizer memory, parameter memory, activation memory, or model partitioning?
3. Does world size divide cleanly by desired tensor, pipeline, sequence, expert, and data parallel sizes?
4. Does the task require fused kernels, flash attention, FP8, Apex, or TensorNVMe? If not, keep those flags off.
5. Is the training loop pipeline-parallel? If yes, define a criterion and use `execute_pipeline`.

Use `scripts/plugin_decision_helper.py --help` for a safe command-line version of this triage.

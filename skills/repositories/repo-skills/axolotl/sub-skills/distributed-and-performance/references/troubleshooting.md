# Distributed and Performance Troubleshooting

Use symptom-driven triage. Do not claim that a fix is verified until the user has run `axolotl preprocess` or a bounded training smoke test in their own ML environment.

## NCCL and Multi-Node Failures

Common symptoms:

- `Watchdog caught collective operation timeout`.
- Processes hang after rendezvous.
- One rank exits and other ranks wait indefinitely.
- Multi-node training is much slower than one-node training.

Checks:

1. Confirm every node launches the same number of processes and uses the same Axolotl config YAML.
2. Confirm `MASTER_ADDR`, rendezvous endpoint, port reachability, `nnodes`, `nproc_per_node`, and scheduler rank variables.
3. For InfiniBand, verify the cluster's required NCCL environment. Axolotl docs call out `NCCL_IB_DISABLE=0`, `NCCL_SOCKET_IFNAME`, and `NCCL_BUFFSIZE` as common torchrun settings.
4. Enable `NCCL_DEBUG=INFO` and `NCCL_DEBUG_SUBSYS=ALL` for a short repro, then disable verbose logging for production.
5. If NVLink should be used, ask the user to check GPU topology with `nvidia-smi topo -m` and consider `NCCL_P2P_LEVEL=NVL` when appropriate.
6. Treat network/interface selection as environment-specific. Do not hard-code cluster hostnames, paths, modules, or secrets into skill content.

## CUDA, Torch, and Optional Backend Mismatches

Symptoms:

- Flash Attention import/build errors.
- `xformers` unavailable or incompatible.
- `bitsandbytes` CUDA errors for QLoRA.
- FP8 rejected by schema or missing FP8 libraries.
- ROCm/AMD runs fail in attention kernels.

Checks:

- Match CUDA/ROCm, PyTorch, driver, GPU architecture, and optional package wheels before changing YAML.
- For attention, switch to a known available backend temporarily: `attn_implementation: sdpa` for compatibility, `flash_attention_2` for modern NVIDIA speed, or `xformers` for older supported GPUs.
- Use canonical `attn_implementation` values; remove legacy boolean attention flags if a canonical backend is set.
- For QLoRA, route adapter/quantization details to `model-loading-and-adapters`, but keep distributed memory advice here: FSDP+QLoRA needs FSDP enabled and bitsandbytes support in the user's environment.
- For ROCm, expect environment-specific Flash Attention and xFormers workarounds; prefer a user-provided working container or module stack.

## DeepSpeed Problems

Symptoms:

- `deepspeed` path not found.
- ZeRO stage does not match the intended memory plan.
- Scheduler or optimizer settings appear ignored.
- ZeRO-3 checkpoint output is not a plain single-file model.

Checks:

1. Run `python scripts/check_distributed_config.py config.yaml` to catch missing local JSON paths and obvious conflicts.
2. If using a path, inspect `zero_optimization.stage` inside the JSON and compare to the filename/user expectation.
3. Do not combine `deepspeed` with `fsdp_config` in one YAML.
4. Remember that DeepSpeed can own optimizer/scheduler behavior; Axolotl custom scheduler warnings may indicate DeepSpeed took over.
5. For ZeRO-3, use DeepSpeed-aware save/load or consolidation procedures; do not assume a normal Hugging Face checkpoint layout.

## FSDP and FSDP QLoRA Problems

Symptoms:

- `fp32_norms` validation fails.
- FSDP settings seem ignored.
- FSDP1 config fields no longer work.
- FSDP+QLoRA still OOMs.
- Sharded checkpoint merge fails or produces unexpected adapter names.

Checks:

- Ensure `fsdp_config` exists; `fsdp_version: 2` alone does not enable FSDP.
- Migrate deprecated `fsdp:` list fields to `fsdp_config`.
- Set `fsdp_version: 2` for new work and for `fp32_norms`.
- For FSDP+QLoRA, use `adapter: qlora` and confirm quantization prerequisites with the model-loading sub-skill.
- If OOM persists, reduce `micro_batch_size`, shorten `sequence_len`, enable checkpointing/offload, or consider CPU offload with expected slowdown.
- For final artifacts, distinguish FSDP sharded checkpoints from merged model outputs; merge only after training with the appropriate Axolotl operation.

## Ray Train Problems

Symptoms:

- `--use-ray` starts but no workers run.
- Ray dashboard shows missing GPUs.
- YAML `ray_num_workers` exceeds cluster resources.
- Ray is not installed in the environment.

Checks:

1. Run `ray status` on the head node outside Axolotl.
2. Match `ray_num_workers` to available GPU worker slots.
3. Use `resources_per_worker` only for deliberate heterogeneous scheduling.
4. Confirm Axolotl and all training dependencies exist on workers or in the Ray runtime environment.
5. Remember Ray is an orchestration layer; it does not replace coherent FSDP/DeepSpeed/batch/precision config choices.

## OOM Triage

For `CUDA out of memory`, illegal memory access after a prior OOM, or process-killed jobs:

1. Reproduce with a smaller `max_steps` or training smoke configuration if the user permits.
2. Lower `micro_batch_size` first; then increase `gradient_accumulation_steps` to preserve effective batch size.
3. Reduce `sequence_len` or enable `sample_packing` with a varlen-capable attention backend.
4. Enable `gradient_checkpointing: true`; then consider `activation_offloading` or `layer_offloading` depending on full fine-tune vs adapter training.
5. Move to FSDP2 or DeepSpeed ZeRO; use higher ZeRO stages or FSDP CPU offload only after simpler levers are exhausted.
6. For long context, set `context_parallel_size` so sequence chunks fit, and remember it reduces data-parallel batch count.
7. For full fine-tunes that OOM while a LoRA run fits, do not assume a LoRA config scales to full training. Full training needs optimizer-state and gradient memory for all parameters.

## Parallelism Shape Errors

Run the checker with the intended world size:

```bash
python scripts/check_distributed_config.py config.yaml --world-size 8
```

Fixes:

- If `context_parallel_size` does not divide world size, change CP or process count.
- If EP is active, make `expert_parallel_size * dp_shard_size * tensor_parallel_size * context_parallel_size == world_size` unless the design is pure EP with world-size EP.
- Avoid TP/CP with pure DDP. Add FSDP sharding through `dp_shard_size > 1` and `fsdp_config`, or remove TP/CP.
- Keep `micro_batch_size: 1` for context-parallel examples unless the user has proven a larger per-rank batch fits.

## Checkpoint Save/Resume Failures

- For long jobs, prefer scheduled `save_steps` plus `dynamic_checkpoint.enabled: true` for on-demand checkpointing.
- File-triggered dynamic checkpoints are resumable; Control+C saves model weights only and is not a complete optimizer-state checkpoint.
- In multi-node jobs, use shared storage for `output_dir` unless the cluster intentionally consolidates per-node outputs later.
- For FSDP/DeepSpeed sharded weights, use the backend-specific merge or consolidation command after training; do not move shard directories manually unless the user knows the backend layout.

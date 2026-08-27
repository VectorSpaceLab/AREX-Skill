# Distributed backend troubleshooting

Use this reference to diagnose AReaL backend, parallelism, placement, LoRA/FP8, CUDA/NCCL, OOM, and weight-sync problems. It is safe to read during planning; do not start training or services unless the user explicitly asked for an operation and the correct sibling sub-skill owns that lifecycle.

## Triage order

1. Identify which role failed: `rollout`, `actor`, `critic`, `ref`, `teacher`, weight-update gateway, or scheduler/launcher.
2. Determine whether the failure happened during parsing/config load, installation/import, process launch, model load, generation, training forward/backward, weight update, checkpoint/recovery, or teardown.
3. Parse the backend plan safely:

   ```bash
   python scripts/check_backend_plan.py --probe-env \
     rollout.backend=sglang:d2t4 actor.backend=fsdp:d8 \
     cluster.n_nodes=2 cluster.n_gpus_per_node=8 \
     actor.weight_update_mode=xccl
   ```

4. Separate facts from unverified assumptions. CPU imports, CLI help, and this checker do not prove GPU backend behavior.
5. If the user needs process lifecycle for v2 services or inference servers, route to `services-cli-operations`; if they need a full experiment command/config selection, route to `post-training-experiments`.

## Fast failure table

| Symptom | Likely cause | Action |
|---|---|---|
| `Backend must be explicitly specified` | Backend string is `d4`, `[actor]:d4`, or a bare hybrid MoE string | Use `fsdp:d4`, `sglang:d4`, `megatron:d2p2t4`, or `megatron:(attn:...|ffn:...)`. |
| FSDP allocation rejects `p` or `e` | FSDP only supports data/tensor/context dimensions | Use Megatron/Archon for PP/EP, or change FSDP string to `fsdp:d...t...c...`. |
| Hybrid MoE parse error | `attn`/`ffn` dimensions invalid, PP differs, or worlds mismatch | Ensure `attn` uses `d/t/p/c`, `ffn` uses `d/t/p/e`, PP matches, and both worlds match. Use `scripts/check_backend_plan.py`. |
| Plan fits CPU import but not GPU run | Optional CUDA/backend runtime absent or wrong variant | Install the correct SGLang/vLLM/Megatron/Archon variant; import success is not GPU verification. |
| SGLang LoRA + XCCL error | SGLang distributed update path does not support LoRA | Set `actor.weight_update_mode=disk` for SGLang LoRA, or switch rollout to vLLM when compatible. |
| Megatron LoRA raises on init | `bridge_type` not `megatron-bridge` | Set `actor.megatron.bridge_type=megatron-bridge` and use vLLM rollout. |
| Archon LoRA requested | Archon LoRA is unsupported | Use FSDP2/Megatron LoRA or full-parameter Archon training. |
| AWEX setup fails or hangs | Not Megatron+SGLang, not colocated, allocator config conflict, or service lifecycle issue | AWEX needs Megatron actor + SGLang rollout + intentional colocation. Remove `expandable_segments` from global CUDA allocator config. Route process lifecycle to `services-cli-operations`. |
| NCCL/HCCL timeout or hang | Rank divergence, mismatched collective, PP shape mismatch, network issue, or early exception on subset of ranks | Dump all rank stacks with `py-spy`, enable distributed debug env vars, and compare call sites. |
| OOM during generation | Too many concurrent rollouts, too little inference TP, SGLang memory fraction too high | Reduce `max_concurrent_rollouts`, increase rollout TP, reduce `sglang.mem_fraction_static`, or reduce sequence lengths. |
| OOM during train forward/backward | Microbatch token budget too high, no checkpointing, insufficient TP/CP/PP/EP | Reduce `actor.mb_spec.max_tokens_per_mb`, enable gradient checkpointing, increase parallelism, or use optimizer memory reductions. |
| OOM during weight update | XCCL bucket memory too large or rollout/inference memory not paused/offloaded enough | Switch to disk update or reduce `weight_chunked_mem_mb`; verify pause/resume and offload sequence. |
| Recovery checkpoint load fails | Parallelism/config changed or wrong checkpoint type | Resume with identical backend/parallelism, experiment/trial names, and matching DCP/Megatron checkpoint format. |

## Parse and config problems

### Explicit backend prefixes

Every per-engine field needs a backend prefix:

```yaml
rollout:
  backend: "sglang:d4t2"
actor:
  backend: "fsdp:d8"
```

Invalid examples:

```yaml
actor:
  backend: "d8"          # missing backend
rollout:
  backend: "sglang.d4"   # dot syntax is wrong; use colon
actor:
  backend: "fsdp:d4p2"   # FSDP cannot use pipeline parallelism
```

### Deprecated `allocation_mode`

Legacy SPMD allocation strings can use `+` for separation and `|` for colocation, but modern single-controller configs use per-engine fields. If a user hands you a legacy string, translate each component into the corresponding engine's `backend` and scheduling fields rather than stuffing the legacy string into `actor.backend`.

### Inheritance of critic/ref backend

When `critic.backend` or `ref.backend` is empty and that role is enabled, it inherits `actor.backend`. Count that inherited role in resource planning only when the algorithm/config actually uses the role. If uncertain, ask or route to `post-training-experiments` for algorithm-level command/config decisions.

## Installation and optional dependency failures

### SGLang vs vLLM variant mismatch

SGLang and vLLM are separate environment variants because their Torch/TorchAO pins differ. Symptoms include import errors, wrong worker CLI flags, CUDA extension failures, or runtime crashes inside inference workers.

Actions:

- Confirm which rollout backend the task needs (`rollout.backend=sglang:...` vs `vllm:...`).
- Rebuild or activate the matching variant; do not try to combine both pin sets unless the project already provides a proven environment.
- Run safe import checks, then a real backend smoke only when authorized and resources/model are available.

### Megatron dependency failures

Common missing or mismatched packages: Megatron-Core, Megatron-Bridge, TransformerEngine, grouped GEMM, Apex, and model-specific CUDA extensions.

Actions:

- Check whether the selected path really needs Megatron. If not, consider FSDP2.
- Prefer `bridge_type=megatron-bridge` for new models and LoRA, but keep `mbridge` for tree training or backwards compatibility.
- Treat FP8/MoE optimized packages as hardware- and version-sensitive; do not repair CUDA/driver stacks without explicit user approval.

### Archon dependency/architecture failures

Archon avoids Megatron-Core but still needs compatible PyTorch distributed/DTensor/FSDP2 behavior. Unsupported model types fail until an Archon model spec exists.

Actions:

- Confirm model type is supported by built-in Archon specs or that a custom spec exists.
- Disable `actor.archon.enable_compile` for compiler debugging or unsupported operations.
- For FP8, verify BF16 dtype, Hopper-class support when required, and 128-aligned local shard dimensions.

### CPU import succeeded but backend failed

This is expected when optional CUDA/service packages are missing or hardware differs. State exactly what was verified, for example: "imported `areal` and parsed config; did not verify SGLang server launch, vLLM worker extension, FSDP multi-GPU, Megatron, Archon, Ray, or Slurm execution."

## CUDA/NCCL/HCCL hangs and deadlocks

### Symptoms

- Logs stop advancing while Python processes remain alive.
- Some GPUs are idle while other ranks show utilization.
- Job reports completion but hangs during cleanup.
- Only a subset of ranks prints an exception; others wait in collectives.

### Debug commands

Set debug env vars **before** launch:

```bash
export NCCL_DEBUG=INFO
export TORCH_DISTRIBUTED_DEBUG=DETAIL
export NCCL_TIMEOUT=300
export CUDA_LAUNCH_BLOCKING=1   # debug only; large performance hit
```

Inspect a live hang:

```bash
# Confirm processes and GPU state.
nvidia-smi
ps aux | grep 'python.*areal' | grep -v grep

# Dump all Python worker stacks without stopping the job.
for pid in $(ps aux | grep 'python.*areal' | grep -v grep | awk '{print $2}'); do
  echo "========== PID $pid =========="
  py-spy dump --pid "$pid"
done
```

How to read stacks:

| Pattern | Meaning | Fix direction |
|---|---|---|
| Some ranks in `destroy_process_group`, others in forward/backward/recv | Earlier exception on a subset of ranks was swallowed by cleanup | Find first-rank exception in logs; reproduce with fewer ranks. |
| Ranks blocked in different collectives | Mismatched collective path or conditional branch differs by rank | Ensure all ranks call same collectives with same group semantics. |
| All ranks in same NCCL collective | Network, slow rank, timeout, or real collective performance issue | Inspect fabric/NCCL logs, reduce timeout for faster failure, check host/device mapping. |
| PP stage waiting in send/recv/shape inference | Pipeline tensor shape or microbatch mismatch | Compare microbatch counts, pad-to-maximum, sequence alignment, and PP schedule. |

Rules:

- Dump stacks for every rank, not just rank 0.
- Reproduce with the smallest GPU count that still exercises the failing dimension (for example PP=2 or TP=2).
- Do not insert barriers as a fix unless you know which collective contract is mismatched; barriers can hide or worsen the bug.

## OOM triage

### Generation OOM

High-impact knobs:

```yaml
max_concurrent_rollouts: 128       # reduce first
rollout:
  backend: "sglang:d2t2"          # increase TP, reduce independent replicas
sglang:
  mem_fraction_static: 0.8         # leave more headroom
```

Also check:

- `train_dataset.max_length` and `gconfig.max_new_tokens` determine total sequence length.
- SGLang `max_running_requests`, `context_length`, `chunked_prefill_size`, and `max_prefill_tokens` may need backend-specific tuning.
- vLLM `max_num_seqs`, `max_model_len`, `gpu_memory_utilization`, and sleep/wake behavior affect memory.

### Training OOM

High-impact knobs:

```yaml
actor:
  mb_spec:
    max_tokens_per_mb: 4096
  gradient_checkpointing: true
  backend: "fsdp:d2c2"      # or fsdp:d2t2 / megatron:... / archon:...
```

Notes:

- `actor.mb_spec.max_tokens_per_mb` cannot be below prompt length + generated length for the longest trajectory handled by the workflow.
- `train_dataset.batch_size` is not the main peak-memory knob; microbatch token count and sequence length are.
- Ulysses/context parallel size must divide the model's attention head count.
- PP reduces parameter/activation placement per rank but can increase warmup activation peaks if too few microbatches are used.
- FSDP `fsdp.memory_efficient_load=true` helps initialization OOM, not necessarily training-step OOM.
- FSDP `fsdp.per_layer_optim_step=true` speeds optimizer step under CPU/offload patterns and requires Adam.
- Optimizer memory can be reduced with `optimizer_dtype=bfloat16` + `optimizer.type=adam_bf16`; avoid plain Adam with bf16 optimizer storage.

### Weight-update OOM

Choices:

```yaml
actor:
  weight_update_mode: disk      # lower GPU update buffer pressure; needs shared storage
```

or reduce XCCL bucket memory:

```python
WeightUpdateMeta.from_fsdp_xccl(
    gen_allocation=..., weight_chunked_mem_mb=512
)
```

Operational notes:

- XCCL updates pause generation, transfer buckets, then resume generation.
- If pause/resume is stuck, inspect inference-side worker health and service lifecycle via `services-cli-operations`.
- For SGLang LoRA, use disk update; distributed update raises.

## LoRA failures

| Failure | Action |
|---|---|
| Missing `gconfig.lora_name`/`rollout.lora_name` | Set a non-empty adapter name and keep training/request names aligned. |
| Megatron LoRA with `mbridge` | Switch to `actor.megatron.bridge_type=megatron-bridge`. |
| Megatron LoRA with SGLang | Switch rollout to vLLM or disable LoRA. |
| SGLang LoRA with XCCL | Use `actor.weight_update_mode=disk`. |
| Unsupported Megatron target module | Use `all-linear` or supported bridge targets that map to HF/vLLM names. |
| Stale adapters accumulate in inference memory | Set bounded `lora_keep_versions` large enough for off-policy rollouts but small enough to bound VRAM. |

## FP8 failures

### Archon blockwise FP8

Common errors:

- `FP8 training requires dtype=bfloat16`: set `actor.dtype=bfloat16`.
- Non-128-aligned local weight shape after TP/ETP: adjust TP/ETP degree or add the module substring to `actor.archon.fp8_config.exclude_modules`.
- Expert FP8 local shape mismatch: disable `include_experts` or choose a parallel plan that preserves 128 alignment.
- Unsupported hardware/kernel path: fall back to BF16 or a supported GPU/runtime.

### Megatron FP8

Common errors:

- Training FP8 enabled but model weights/config are not FP8/quantized: use matching FP8 checkpoint/config or disable FP8.
- Missing TransformerEngine or optimized packages: install the correct CUDA-compiled packages for the runtime image.
- Weight sync path falls back unexpectedly: check bridge type, quantization, LoRA, and registry support.

## Ray/Slurm placement failures

Checklist:

- Planned effective GPU demand <= allocated GPUs.
- Role colocation is explicit, documented, and memory-budgeted.
- `CUDA_VISIBLE_DEVICES`, local rank, global rank, and scheduler-assigned devices agree.
- Slurm node-local rank mapping does not make multiple SGLang servers claim the same physical GPU range.
- Shared storage is mounted inside every container/process for disk updates, checkpoints, logs, and recovery.
- Ports per worker/server are reserved; process lifecycle issues route to `services-cli-operations`.
- Role-specific allocator/debug variables are set in `scheduling_spec.env_vars`, not by package import side effects.

AWEX-specific checks:

```bash
python scripts/check_backend_plan.py --probe-env --colocated-actor-rollout \
  rollout.backend=sglang:d4 actor.backend=megatron:d4 \
  actor.weight_update_mode=awex
```

If this reports `expandable_segments`, remove that global allocator setting for the AWEX SGLang plugin and configure any actor-only allocator behavior per role.

## Checkpoint and recovery failures

AReaL has two checkpoint concepts:

| Mechanism | Purpose | Format | Includes optimizer/dataloader/RNG |
|---|---|---|---|
| Saver/HF export | Evaluation or publishing | HuggingFace | no |
| Recovery | Fault-tolerant resume | backend distributed checkpoint | yes |

Recovery rules:

- Use identical backend, parallelism, experiment name, and trial name when loading distributed recovery checkpoints.
- Delete recovery metadata only when intentionally starting fresh.
- After loading recovery state, synchronize inference engine weights to the recovered training version before new rollouts.
- For Megatron distributed optimizer cases, optimizer-state save/load compatibility may require disabling optimizer save in HF-style checkpoints while keeping recovery semantics clear.

## Perf and memory profiling

Safe planning knobs:

```yaml
perf_tracer:
  enabled: true
  experiment_name: ${experiment_name}
  trial_name: ${trial_name}
  fileroot: ${cluster.fileroot}
  save_interval: 1
  session_tracer:
    enabled: true
```

Trace conversion after a run:

```bash
python -m areal.tools.perf_trace_converter logs/**/perf_tracer/traces-*.jsonl merged.json
```

For backend memory snapshots, prefer backend-provided memory-profile hooks only during an authorized run. Do not start a long run just to collect traces unless the user approves.

## When to stop and ask

Ask for clarification before recommending a concrete backend or install mutation when any of these are unknown:

- exact model family/size and whether it is MoE/VLM/GDN/SSM,
- available GPUs per node, node count, GPU architecture, network, and shared filesystem,
- desired inference backend (SGLang vs vLLM) when LoRA/vLLM-specific features matter,
- whether actor/rollout are separated or colocated,
- whether the user accepts experimental Archon or compiled Megatron/FP8 packages,
- whether a full GPU/service smoke is allowed or the answer must stay at planning level.

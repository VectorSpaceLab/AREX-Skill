# Engine API and weight synchronization

This reference is for planning/debugging AReaL engine internals and weight synchronization. It is not a high-level experiment recipe. For choosing or launching a training workflow, route to `post-training-experiments`. For managing v2 service processes, route to `services-cli-operations`.

## Core lifecycle

AReaL separates train engines and inference engines.

### Train engine lifecycle

All train backends implement the same `TrainEngine` shape:

1. `create_process_group(parallel_strategy=None)`
   - Initializes distributed communication groups and backend-specific meshes.
   - Called before `initialize()`.
2. `initialize(addr=None, ft_spec=FinetuneSpec(...))`
   - Creates devices/models/optimizers and applies parallelism.
   - FSDP, Megatron, and Archon assert that remote `addr` initialization is not supported.
3. Optional connection to rollout engine:
   - `connect_engine(engine, meta)` creates weight-update wiring for online RL.
4. Rollout/debug helpers:
   - `rollout_batch(data, workflow, workflow_kwargs, group_size=...)` is a blocking/offline/debug helper, not the normal asynchronous production path.
   - `prepare_batch(dataloader, workflow, ...)` collects rollout data for training.
5. Versioning:
   - `set_version(version)` and `get_version()` track the training-side model version.
6. Saving/loading:
   - `save(SaveLoadMeta)` and `load(SaveLoadMeta)` support HF export and distributed checkpoint/recovery formats.
7. Optimization:
   - `forward_backward_batch(mb_list, process_output_fn, forward_only=False)` is the backend hook for microbatch execution.
   - `train_batch(input_, loss_fn, loss_weight_fn)` and `eval_batch(...)` use packed 1D training tensors.
   - `optimizer_zero_grad()`, `optimizer_step()`, and `lr_scheduler_step()` are backend-owned.
8. Memory/profile:
   - `offload()`, `onload()`, `get_device_stats()`, `start_memory_profile()`, `stop_memory_profile()`, and `save_perf_tracer()` are safe concepts to discuss; do not invoke memory-affecting methods unless operating an actual run.

### Inference engine lifecycle

Remote SGLang and vLLM engines are composition wrappers around AReaL's remote inference engine implementation. The public `InferenceEngine` shape includes:

- `initialize(engine_id=None, addr=None, train_data_parallel_size=None)` — connect to already-launched servers or discover them through the scheduler.
- `launch_server(server_args)` / `teardown_server()` — process lifecycle; route actual lifecycle operations to `services-cli-operations` unless the user only asks about backend arguments.
- `agenerate(ModelRequest)` — async generation.
- `submit(...)`, `wait(count, timeout=...)`, and `wait_for_task(task_id, timeout=...)` — asynchronous rollout queue interface.
- `rollout_batch(...)` — blocking helper for debugging/evaluation, not a production training loop.
- `init_weights_update_group(meta, rank_ids=None)` — initialize the inference side of distributed updates.
- `update_weights_from_distributed(meta, param_specs)` — nonblocking XCCL/NCCL/HCCL receive/update.
- `update_weights_from_disk(meta)` — nonblocking disk/HF checkpoint load.
- `set_version(version)` / `get_version()` — inference-side model version.
- `compute_logp(data)` — optional inference-side scoring API for teacher distillation.

## Data structures that matter

### `FinetuneSpec`

A small training schedule descriptor:

```python
FinetuneSpec(total_train_epochs: int, dataset_size: int, train_batch_size: int)
```

Derived properties:

- `total_train_steps = total_train_epochs * (dataset_size // train_batch_size)`
- `steps_per_epoch = dataset_size // train_batch_size`

Megatron requires positive total train steps and warmup steps less than total train steps.

### `ModelRequest` and `ModelResponse`

`ModelRequest` carries token IDs, optional image payloads, generation hyperparameters, metadata, and version data into `InferenceEngine.agenerate()`.

Important generation hyperparameters forwarded by both SGLang and vLLM remote backends include:

- `top_p`, `top_k`, `max_new_tokens`, `temperature` or greedy `temperature=0`,
- `stop_token_ids`, `stop`, `ignore_eos`, `skip_special_tokens`,
- `frequency_penalty`,
- LoRA adapter selection through `gconfig.lora_name` when LoRA is enabled.

Backend-specific request details:

| Backend | Endpoint style | Notes |
|---|---|---|
| SGLang | `/generate` with `input_ids`, `image_data`, and nested `sampling_params` | Always requests output logprobs. Beam search is not supported by AReaL's SGLang remote backend. `return_routed_experts` can be requested through request metadata for MoE diagnostics. |
| vLLM | `/v1/completions` for token prompts or `/v1/chat/completions` for VLM chat payloads | Uses flat OpenAI-compatible fields. For VLM, the number of base64 images must match image_url slots. vLLM LoRA generation selects the versioned adapter name as `model`. |

Response parsing must preserve one logprob per sampled output token. Malformed response shapes should be treated as backend/API failures, not silently accepted.

### `WeightUpdateMeta`

`WeightUpdateMeta` tells the training and inference engines how to synchronize weights:

```python
WeightUpdateMeta(
    type: Literal['disk', 'xccl', 'awex'],
    path: str | None = None,
    gen_allocation: ModelAllocation | None = None,
    nccl_master_address: str | None = None,
    nccl_master_port: int | None = None,
    nccl_group_name: str | None = None,
    weight_chunked_mem_mb: int = 1024,
    use_lora: bool = False,
    lora_name: str = '',
    lora_int_id: int = 0,
    base_model_name: str = '',
    peft_config: dict = {},
    lora_keep_versions: int = 0,
    clear_checkpoint_after_load: bool = True,
    version: int | None = None,
)
```

Convenience constructors:

- `WeightUpdateMeta.from_disk(experiment_name, trial_name, file_root, name='default', use_lora=False, ...)`
- `WeightUpdateMeta.from_fsdp_xccl(gen_allocation, weight_chunked_mem_mb=1024, use_lora=False, ...)`
- `WeightUpdateMeta.from_megatron_xccl(gen_allocation, weight_chunked_mem_mb=1024, use_lora=False, ...)`
- `WeightUpdateMeta.from_awex(meta_server_addr=None, use_lora=False, ...)`
- `meta.with_version(version)` copies metadata and rewrites a disk path suffix to `weight_update_v{version}`.

## Weight-update modes

### `disk`

Training saves HF-format weights or adapters to a shared path; inference loads from disk.

Use `disk` when:

- distributed XCCL/NCCL update OOMs,
- using SGLang + LoRA,
- cluster networking is unreliable but shared storage is healthy,
- you need simpler failure recovery and can afford more I/O.

Requirements and pitfalls:

- Multi-node jobs need shared `cluster.fileroot` readable/writable from every node.
- Disk update blocks on save/load synchronization and can be slower than XCCL.
- For LoRA, the disk payload is adapter-only. Preserve versioned adapter naming and unload stale versions to prevent VRAM leaks.

### `xccl`

Training broadcasts parameter buckets directly into inference workers through a custom process group.

Use `xccl` when:

- rollout and actor are separated and network/NCCL is reliable,
- you want lower shared-storage traffic,
- you can budget extra GPU memory for update buffers.

Runtime behavior:

- Training rank 0 (or pipeline-stage heads for PP cases) pauses generation, sends bucket metadata to inference, broadcasts tensors, waits for futures, resumes generation, and synchronizes.
- `weight_chunked_mem_mb` controls bucket size. Reducing it lowers peak update memory but may increase overhead.
- FSDP casts fp32 master storage to compute dtype before HF export or rollout sync.
- Megatron with inference PP uses per-PP-rank group names such as `update_weight_group_0` so each stage transfers only its own parameters.
- Archon mirrors this per-PP-stage behavior for PP inference; non-PP-head ranks participate only where required by collectives.

Backend-specific XCCL notes:

| Pair | Notes |
|---|---|
| FSDP -> SGLang/vLLM | Full-model XCCL supported. FSDP LoRA + SGLang XCCL is not supported; use disk. |
| Megatron -> vLLM | Full-model and LoRA XCCL paths exist; Megatron LoRA requires `bridge_type=megatron-bridge`. |
| Megatron -> SGLang | Full-model XCCL supported; Megatron LoRA + SGLang is not supported. |
| Archon -> SGLang/vLLM | Full-model XCCL paths exist; Archon LoRA is not supported. |

### `awex`

AWEX is a v2 colocated actor-rollout weight-transfer mode based on training/inference adapter protocols and direct P2P operations.

Use `awex` only when all are true:

- actor backend is Megatron,
- rollout backend is SGLang,
- actor and rollout are intentionally colocated on the same placement,
- the operator has v2 service/worker lifecycle covered by `services-cli-operations`,
- LoRA is disabled unless you have separate project evidence for that exact path.

AWEX adapter protocols report parallelism strategy, expose parameter metadata, initialize update groups, execute updates, release/resume memory, and tear down groups. Training-side adapters send; inference-side adapters receive. In colocated mode, SGLang plugin startup must not see `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:...`.

## Backend implementation notes

### FSDP2 engine

Process groups and mesh:

- Initializes global process group with the platform communication backend and a Gloo CPU group.
- Builds FSDP/world mesh with data parallel (`dp`), sequence/context parallel (`sp`), and sequence+tensor model parallel (`sp_tp`) groups.
- Eagerly warms communication groups to avoid lazy-init races with colocated engines.

Initialization and model creation:

- Requires FSDP2-capable Torch.
- Loads LLMs with HuggingFace `AutoModelForCausalLM` or critics with `AutoModelForTokenClassification`.
- VLMs use image-text model classes and do not support float16 compute dtype.
- `fsdp.memory_efficient_load` uses CPU/meta loading and rank-0 broadcast for LLMs; VLMs load independently on CPU.
- `use_lora` wraps with PEFT LoRA and stores adapter weights with `autocast_adapter_dtype=False`.

Known constraints:

- FSDP backend strings reject PP and EP.
- Tree training cannot combine with sequence parallel size > 1 in the FSDP path.
- `per_layer_optim_step` requires Adam optimizer.
- Do not pair `optimizer.type=adam` with `optimizer_dtype=bfloat16`; use `adam_bf16` if optimizing for bf16 optimizer-state memory.

### Megatron engine

Process groups and mesh:

- Initializes Megatron model parallel with `tp-cp-ep-dp-pp` ordering.
- `virtual_pipeline_parallel_size > 1` requires PP > 1.
- Creates a context/model parallel group for AReaL data distribution and a CPU group for synchronization/offload control.

Initialization and model bridge:

- `bridge_type=mbridge` is default and remains required for Megatron tree-training.
- `bridge_type=megatron-bridge` is preferred for newer model architectures and LoRA.
- LoRA with Megatron raises unless `bridge_type=megatron-bridge`.
- If `use_bridge_for_update_weights` is requested but unsupported by quantization, LoRA, or bridge type, runtime logs a fallback and uses registry conversion.
- VLM and padded-sequence model types can reject CP > 1.

Precision and checkpoint notes:

- `actor.optimizer.type=adam_bf16` is normalized to Megatron precision-aware optimizer settings (`exp_avg_dtype=bfloat16`, `exp_avg_sq_dtype=bfloat16`).
- Megatron FP8 requires FP8-compatible weights/quantization configuration.
- Distributed optimizer checkpoints can have backend-specific optimizer-state limitations; when recovery or HF export fails, check optimizer save flags and bridge support.

### Archon engine

Process groups and mesh:

- Archon is PyTorch-native and builds `DeviceMesh` dimensions for PP, DP shard, CP, TP, EP, and ETP.
- Without EP, useful mesh names include `pp`, `dp`, `dp_shard_cp`, `dp_cp`, `dp_shard`, `cp`, `tp`, and `pp_cp_tp`.
- With EP, additional mesh names include `ep`, `dp_shard_mod_ep`, `dp_shard_in_ep`, and optional `ep_tp`.

Initialization:

- No remote initialization; requires `FinetuneSpec`.
- Creates model on device/meta path, builds a state-dict adapter, applies FP8 conversion before parallelism when enabled, prepares activation checkpointing/compile config, then applies parallelism and materializes weights.
- Built-in model support is limited; unsupported model types should use FSDP/Megatron or a custom Archon model spec.

Constraints:

- LoRA unsupported.
- FP8 blockwise requires `dtype=bfloat16`, `fp8_config.use_triton=True`, and aligned local shard dimensions.
- PP with tied input/output embeddings is unsupported.
- PP memory depends heavily on microbatch count and schedule.

## Version consistency and recovery

AReaL asynchronous rollouts track model versions so training can limit off-policyness and align updates.

Checklist:

- When generation stalls, check `max_head_offpolicyness` and `max_concurrent_rollouts`; too-strict staleness control can block rollout progress.
- Disk recovery checkpoints are backend-specific DCP/Megatron distributed formats; resume with the same parallelism configuration, experiment name, and trial name.
- After recovery, synchronize inference weights to the recovered training state before accepting new rollouts.
- Do not treat a saved HF checkpoint as equivalent to a full recovery checkpoint; HF exports omit optimizer/dataloader/RNG state.

## Safe API-level smoke checks

These commands inspect surfaces only and do not launch services/training:

```bash
python scripts/check_backend_plan.py --help
python scripts/check_backend_plan.py --probe-env \
  rollout.backend=vllm:d2t4 actor.backend=megatron:d2p2t4 \
  actor.megatron.bridge_type=megatron-bridge

python - <<'PY'
from areal.api.alloc_mode import ModelAllocation
for spec in ['sglang:d2t4', 'fsdp:d8', 'megatron:(attn:d1p4t2c2|ffn:d1p4t1e4)']:
    a = ModelAllocation.from_str(spec)
    print(spec, a.backend, a.parallel.world_size)
PY
```

If the package import fails, fix installation first. If it succeeds, still require real GPU/service/native evidence before claiming that a backend run is verified.

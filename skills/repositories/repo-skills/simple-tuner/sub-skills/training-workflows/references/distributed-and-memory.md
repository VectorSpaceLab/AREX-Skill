# Distributed and memory planning

Use this reference before changing multi-GPU settings, DeepSpeed, FSDP2, context parallelism, attention backends, precision, quantization, offload, or resume topology.

## Launch layers

SimpleTuner training is ultimately launched through Accelerate.

- `simpletuner train` discovers an Accelerate config if one exists; otherwise it launches with `mixed_precision`, `TRAINING_NUM_PROCESSES`, `TRAINING_NUM_MACHINES`, and `TRAINING_DYNAMO_BACKEND` from environment/config.
- Manual multi-GPU configuration can use `num_processes` in `config.json`, `TRAINING_NUM_PROCESSES` in `config.env`, `CUDA_VISIBLE_DEVICES`, or a full Accelerate config.
- Multi-node jobs require all nodes to agree on rank count, network rendezvous, shared/output storage, and the same effective training topology.

## Choose the distributed strategy

| Need | Strategy | Notes |
| --- | --- | --- |
| Faster training when the model fits on every GPU | DDP / normal multi-GPU | Prefer this for LoRA when each rank can hold the model. Check dataset bucket size against the effective batch. |
| Full-model or memory-bound run where normal DDP does not fit | FSDP2 | DTensor-backed FSDP2 shards parameters/gradients/optimizer state. It is often a memory tool, not the fastest path. |
| CUDA full-model run needing ZeRO optimizer/state offload | DeepSpeed ZeRO | CUDA-focused; not available on macOS/MPS or normal ROCm route. Use the lowest ZeRO stage that fits. LoRA with DeepSpeed is documented as unsupported. |
| Long video/context sequences where attention sequence length is the bottleneck | Context parallelism | Requires careful process count, model `_cp_plan` support, and usually FSDP2 for sharded context-parallel jobs. |
| Low VRAM single-GPU run | Quantization, gradient checkpointing, group offload, startup offload, VAE tiling/chunking | Use model quickstart recommendations first; do not mix incompatible offload systems. |

## Dataset size gate for multi-GPU

Every aspect bucket must be large enough for the configured effective batch:

```text
effective_batch_size = train_batch_size × num_processes × gradient_accumulation_steps
```

If a bucket has fewer usable samples after repeats, SimpleTuner can fail with a zero-usable-batches error. Solutions are to reduce `train_batch_size`, reduce GPU/process count, reduce `gradient_accumulation_steps`, add samples, increase dataset `repeats`, or enable `allow_dataset_oversubscription` when automatic repeat adjustment is acceptable. Manual repeats are not overridden by automatic oversubscription.

## DeepSpeed decision points

Source evidence: `documentation/DEEPSPEED.md`, `documentation/DISTRIBUTED.md`, `simpletuner/helpers/training/deepspeed.py`, and `tests/test_fsdp_cmd_args.py`.

- DeepSpeed ZeRO stages shard optimizer state, gradients, and parameters progressively. Choose the lowest stage that fits to reduce overhead.
- DeepSpeed is CUDA-oriented and documented as unavailable on macOS/MPS and ROCm systems.
- DeepSpeed and FSDP are mutually exclusive; supplying both `fsdp_enable` and `deepspeed_config` raises an error.
- DeepSpeed cannot be enabled when resuming a checkpoint that did not use DeepSpeed, and cannot be disabled when resuming one that did. Export a model-only checkpoint and start a new trainer run if changing this topology.
- DeepSpeed ZeRO-3 can complicate validation and checkpoint layout; keep validation/checkpoint expectations explicit before long runs.
- `deepspeed_config` may be raw JSON or a path to JSON. WebUI has a builder, but CLI users can put the config in `config.json`.

## FSDP2 decision points

Source evidence: `documentation/FSDP2.md`, `simpletuner/helpers/configuration/cmd_args.py`, `simpletuner/helpers/training/trainer.py`, and `tests/test_fsdp_cmd_args.py`.

- Prefer FSDP2 for full-model runs or LoRA runs that cannot fit under DDP. If a LoRA run fits with DDP, DDP is usually faster.
- Required/important fields: `fsdp_enable`, `fsdp_version=2`, `fsdp_state_dict_type`, `fsdp_auto_wrap_policy`, `fsdp_transformer_layer_cls_to_wrap`, `fsdp_cpu_ram_efficient_loading`, `fsdp_reshard_after_forward`, and `num_processes`.
- `SHARDED_STATE_DICT` scales better for large models; `FULL_STATE_DICT` gathers on rank 0 and increases memory pressure.
- FSDP v1 is deprecated; use v2 unless maintaining an old config.
- FSDP2 rejects Quanto precision on sharded parameters because Quanto kernels do not register DTensor sharding strategies. Disable Quanto precision for FSDP2 runs or choose a non-FSDP LoRA plan.
- FSDP2 CPU parameter offload is incompatible with post-accumulate gradient hook optimizer paths such as `optimizer_release_gradients` with optimi optimizers, and with TorchAO CPU-offload optimizer mode.
- If `fsdp_activation_checkpointing` is enabled, SimpleTuner disables model-level gradient checkpointing to avoid duplicate checkpointing.

## Context parallelism

Source evidence: `documentation/FSDP2.md`, `simpletuner/helpers/training/context_parallel.py`, `simpletuner/helpers/training/trainer.py`, and `tests/test_context_parallel_plans.py`.

- `context_parallel_size` must be an integer greater than 0; `1` disables context parallelism.
- Process count must be known, at least as large as `context_parallel_size`, and evenly divisible by it.
- `context_parallel_comm_strategy` is `allgather` or `alltoall`. Use `allgather` as the default starting point; use `alltoall` for workloads or examples that explicitly require Ulysses/all-to-all routing.
- FSDP-enabled context parallelism requires `fsdp_version=2`. The trainer raises `Context parallelism with FSDP sharding requires FSDP2` when a sharded CP topology is requested without the FSDP2 plugin.
- Standalone context parallelism keeps model weights replicated and only shards the sequence axis; it is not a replacement for FSDP2 memory sharding.
- The model must define a valid `_cp_plan`. The test suite verifies plans for several supported families, but individual models can still reject CP when their implementation says it is unsupported.
- Known model restrictions include Mage-Flow rejecting `context_parallel_size`, ERNIE TREAD routing rejecting CP, and MiniMax H3 rejecting CP with CachedKV reference mode, TREAD routing, or hidden-state capture.

## Attention backend decisions

| Backend family | Use when | Caveats |
| --- | --- | --- |
| `diffusers` / native PyTorch SDPA | Default stable route | Classic SD/SDXL UNets may not use Diffusers' `attention_backend` dispatcher even when a backend flag is set. |
| `xformers` | Model exposes xformers memory-efficient attention and xformers is installed | Verify package/build compatibility with the target GPU. |
| `flash-attn`, `flash-attn-2`, `flash-attn-3`, varlen, and hub aliases | CUDA/Hopper/Ada/Ampere transformer-style workloads, especially video CP examples | Install matching kernels or allow hub kernels if configured. FlashAttention 3 targets Hopper-class GPUs. Benchmark on the target hardware. |
| `flex` | CUDA PyTorch 2.5+ FlexAttention experiments | Requires CUDA, Ampere+ GPU, matching compiler toolchain, and BF16/FP16 tensors. Prototype backend; rebuild kernels after driver/CUDA/PyTorch changes. |
| `metal-flash-attention` and quantized aliases | Apple Silicon MPS with Universal Metal Flash Attention installed | Requires separate manual UMFA build/install and runtime parity checks. Do not select on CUDA/ROCm/CPU. |
| `sla` | Fine-tuning with Sparse-Linear Attention and matching inference plan | CUDA-only reference package; checkpoint saves `sla_attention.pt`, which must travel with the checkpoint. SLA-trained weights should keep SLA enabled for validation/resume/inference. |
| `sageattention` variants | Inference-oriented speed trials | Training use requires explicit `sageattention_usage` and is risky because gradients may not propagate through all custom kernels. |
| `native-math`, `cudnn`, `native-efficient`, `native-flash`, vendor-native selectors | Determinism, CuDNN SDPA, or vendor accelerator experiments | Use only when the installed PyTorch backend supports the selected target. |

## Memory knobs before expensive training

Apply lower-risk knobs before changing topology:

1. Confirm the model-family quickstart and use its VRAM-tier example.
2. Set `train_batch_size=1` for large/image-video models before increasing it.
3. Enable `gradient_checkpointing`; tune `gradient_checkpointing_interval` and `gradient_checkpointing_segment_stride` only on supported families.
4. Use `base_model_precision`, `quantize_via=cpu`, and text-encoder precision from the quickstart when supported.
5. Use `offload_during_startup` when startup/VAE/text-encoder caching OOMs.
6. Use group offload for memory-bound transformer models, but do not combine incompatible offload systems.
7. Reduce resolution and video frame count before changing distributed topology.
8. Move to FSDP2 or DeepSpeed only after the single-node/single-GPU memory plan is insufficient and the user approves the compute cost.

## Resume topology constraints

Before resuming, compare the new plan against the checkpoint:

- Same `model_family`, `model_type`, `model_flavour`, and architecture metadata.
- Same distributed mode: DDP vs DeepSpeed vs FSDP2; do not add/remove DeepSpeed mid-resume.
- Same world size/process layout, context-parallel size/strategy, FSDP state-dict expectations, batch sizing, gradient accumulation, dataset repeats, and dataloader semantics.
- Same sampler/bucket assumptions. If a checkpoint records per-dataset batch size, SimpleTuner raises unless the user explicitly accepts the override via `--i_know_what_i_am_doing` or `SIMPLETUNER_ALLOW_MODIFYING_BSZ=1`; do not use that override casually.

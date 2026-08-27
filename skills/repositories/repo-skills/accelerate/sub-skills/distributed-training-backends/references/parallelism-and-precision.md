# Parallelism, Precision, Quantization, and Compile Backends

Use this reference for backend add-ons and non-DeepSpeed/FSDP runtime choices: torch native parallelism, Megatron-LM, TPU/XLA, Gaudi/HPU, low precision, FP8, quantization, `torch.compile`, Local SGD, and DDP communication hooks.

## Torch Native Parallelism

Accelerate exposes PyTorch `DeviceMesh`/`DTensor` parallelism through `parallelism_config` and related dataclasses. It is normally composed with FSDP2.

### Launch Config Keys

```yaml
distributed_type: FSDP
mixed_precision: bf16
num_processes: 8
fsdp_config:
  fsdp_version: 2
  fsdp_auto_wrap_policy: TRANSFORMER_BASED_WRAP
  fsdp_reshard_after_forward: true
  fsdp_state_dict_type: SHARDED_STATE_DICT
parallelism_config:
  parallelism_config_dp_replicate_size: 2
  parallelism_config_dp_shard_size: 2
  parallelism_config_tp_size: 2
  parallelism_config_cp_size: 1
```

Key meanings:

- `parallelism_config_dp_replicate_size`: data-parallel replicas, like DDP groups.
- `parallelism_config_dp_shard_size`: data-parallel sharding, implemented with FSDP2.
- `parallelism_config_tp_size`: tensor parallel size, using Transformers/PyTorch tensor parallel support.
- `parallelism_config_cp_size`: context parallel size, using FSDP2-related context parallel support.
- `parallelism_config_cp_comm_strategy`: `allgather` or `alltoall`.
- `parallelism_config_sp_size`: sequence parallel size.
- `parallelism_config_sp_backend`: sequence-parallel backend; DeepSpeed sequence parallelism has its own constraints.
- `parallelism_config_sp_seq_length` and `parallelism_config_sp_seq_length_is_variable`: fixed-vs-variable sequence length control.
- `parallelism_config_sp_attn_implementation`: `flash_attention_2`, `flash_attention_3`, `sdpa`, or a compatible hub-hosted flash-attention kernel. `eager` and `flex_attention` are not supported for DeepSpeed sequence parallelism.

### Constraints

- `--use_parallelism_config` requires `--use_fsdp` and `--fsdp_version=2`.
- Tensor parallelism generally expects a recent PyTorch and Transformers version.
- Context parallelism expects a recent PyTorch with beta CP support.
- Keep tensor parallelism intra-node unless the user has high-performance interconnect and has validated cross-node TP.
- The product of configured parallel dimensions should fit the process count; if it does not, flag the config before launch.

## Megatron-LM

Use `MegatronLMPlugin` only when the project is explicitly Megatron-LM compatible.

Important fields:

- `tp_degree`: tensor parallel degree.
- `pp_degree`: pipeline parallel degree.
- `num_micro_batches`: pipeline micro-batch count.
- `sequence_parallelism`: Megatron sequence parallelism.
- `recompute_activations`: activation recomputation.
- `use_distributed_optimizer`: distributed optimizer path.
- `gradient_clipping`, scheduler-related fields such as `train_iters`, `train_samples`, `lr_decay_style`, and warmup fields.
- Custom hooks such as `custom_model_provider_function`, `custom_prepare_model_function`, `custom_get_batch_function`, and `custom_loss_function`.
- `other_megatron_args`: escape hatch for Megatron-native arguments.

Megatron-LM has strong assumptions about model provider functions, datasets, optimizer/scheduler wrappers, and training loop shape. Do not recommend it as a drop-in replacement for ordinary PyTorch/Transformers code.

## TPU/XLA

Use TPU/XLA only when `torch_xla` and a TPU runtime are available.

- Launch/config identifies XLA with TPU flags or `distributed_type: XLA` in generated config.
- TPU pod flows use `torch_xla.distributed.xla_dist` under the hood.
- TPU training supports `mixed_precision="bf16"`; `downcast_bf16=True` changes dtype behavior for tensors that would otherwise remain fp32.
- XLA execution is lazy; debugging often requires marking steps or checking where tensors materialize.
- CPU-only inspection can validate config shape and imports, not TPU runtime behavior.

## Gaudi/HPU

Accelerate has Gaudi/HPU pathways for Habana devices, but execution requires the Habana software stack and HPU hardware. Treat HPU communication hooks, mixed precision, and device placement as hardware-backed features that cannot be proven in a generic CPU environment.

## Mixed Precision and FP8

### Standard Mixed Precision

- `mixed_precision="no"`: no autocast path from Accelerate.
- `mixed_precision="fp16"`: common CUDA path; requires compatible GPU backend.
- `mixed_precision="bf16"`: common on Ampere+ NVIDIA GPUs, TPUs, HPUs, and some CPU/XPU paths depending on installed PyTorch/backend support.
- `mixed_precision="fp8"`: requires an FP8 backend and suitable hardware.

### FP8 Backends

Accelerate supports multiple FP8 recipe handlers:

- `TERecipeKwargs`: Transformer Engine backend. Requires `transformer-engine`; useful fields include `fp8_format`, `amax_history_len`, `amax_compute_algo`, `override_linear_precision`, `use_autocast_during_eval`, and `use_mxfp8_block_scaling`.
- `AORecipeKwargs`: torchao FP8 backend. Requires `torchao`; useful with FSDP2 float8 all-gather and `Float8LinearConfig`.
- `MSAMPRecipeKwargs`: MS-AMP backend. Requires `ms-amp`; `opt_level` is `O1` or `O2`.
- `FP8RecipeKwargs`: deprecated compatibility wrapper; prefer backend-specific recipe classes.

Launch-level FP8 keys include:

```yaml
mixed_precision: fp8
fp8_config:
  fp8_backend: te
  fp8_format: HYBRID
  fp8_amax_compute_algo: most_recent
  fp8_amax_history_len: 1024
  fp8_use_autocast_during_eval: false
```

For torchao-style FSDP2 FP8, pair `mixed_precision="fp8"`, `AORecipeKwargs`, FSDP2, and hardware with FP8 tensor cores. Performance depends heavily on matrix dimensions, sequence length, and compilation.

## Quantization

### bitsandbytes

Use `BnbQuantizationConfig` for 8-bit or 4-bit loading/dispatch paths:

- `load_in_8bit=True` for 8-bit quantization.
- `load_in_4bit=True` for 4-bit quantization.
- Do not set both `load_in_8bit` and `load_in_4bit`.
- `bnb_4bit_quant_type`: `fp4` or `nf4`.
- `bnb_4bit_compute_dtype`: `fp32`, `fp16`, or `bf16`.
- `skip_modules` and `keep_in_fp32_modules` exclude sensitive modules.
- 4-bit serialization is not generally supported in the Accelerate quantization utility path; route save/load details to checkpointing.

Quantized fine-tuning usually means PEFT/adapters rather than pure training of all quantized weights.

### torchao

Use `AORecipeKwargs` for FP8 linear replacement flows. It can set `pad_inner_dim` and `enable_fsdp_float8_all_gather`. It requires `torchao` and hardware/compiler support; without kernels or compilation, performance may not improve.

## `torch.compile` / TorchDynamo

Use `TorchDynamoPlugin` when the user asks for `torch.compile` integration:

```python
from accelerate import Accelerator
from accelerate.utils import TorchDynamoPlugin

dynamo = TorchDynamoPlugin(
    backend="inductor",
    mode="default",
    fullgraph=False,
    dynamic=None,
    use_regional_compilation=True,
)
accelerator = Accelerator(dynamo_plugin=dynamo)
```

Important fields:

- `backend`: Dynamo backend such as `inductor`, `aot_eager`, or `no`.
- `mode`: `default`, `reduce-overhead`, or `max-autotune`.
- `fullgraph`: whether graph breaks are allowed.
- `dynamic`: dynamic shape tracing.
- `options`: backend options dict.
- `disable`: no-op compile path for testing.
- `use_regional_compilation`: compile repeated blocks separately to reduce cold start.

Compilation can combine with DDP, FSDP, DeepSpeed, and mixed precision, but graph breaks, unsupported ops, dynamic shape behavior, or backend-specific limitations can dominate runtime.

## Local SGD

Use `LocalSGD` for ordinary multi-GPU or multi-CPU distributed training when the user wants to reduce gradient synchronization frequency without changing effective batch size.

Pattern:

```python
from accelerate.local_sgd import LocalSGD

with LocalSGD(accelerator=accelerator, model=model, local_sgd_steps=8, enabled=True) as local_sgd:
    for batch in dataloader:
        with accelerator.accumulate(model):
            outputs = model(**batch)
            loss = outputs.loss
            accelerator.backward(loss)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            local_sgd.step()
```

Limitations: Local SGD is for basic multi-device training and is not a DeepSpeed/FSDP replacement.

## DDP Communication Hooks

Use `DistributedDataParallelKwargs` with `DDPCommunicationHookType` for DDP gradient communication optimization:

```python
from accelerate import Accelerator, DDPCommunicationHookType, DistributedDataParallelKwargs

ddp = DistributedDataParallelKwargs(
    comm_hook=DDPCommunicationHookType.POWER_SGD,
    comm_wrapper=DDPCommunicationHookType.FP16,
    comm_state_option={"matrix_approximation_rank": 2},
)
accelerator = Accelerator(kwargs_handlers=[ddp])
```

Supported hook concepts:

- `FP16`: fp16 compression hook.
- `BF16`: bf16 compression hook; requires backend support such as suitable NCCL versions.
- `POWER_SGD`: PowerSGD compression hook.
- `BATCHED_POWER_SGD`: batched PowerSGD hook.
- `comm_wrapper`: optional `FP16` or `BF16` wrapper around PowerSGD hooks.
- `comm_state_option`: PowerSGD state kwargs such as matrix approximation rank.

DDP hooks only apply when the prepared model is wrapped in PyTorch DDP, not DeepSpeed or FSDP.

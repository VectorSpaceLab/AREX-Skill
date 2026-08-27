# Backend API Reference

This page summarizes Accelerate APIs most relevant to backend selection. Use it as a quick lookup before writing code or validating config snippets.

## Core Backend Plugins

### `DeepSpeedPlugin`

Import from `accelerate` or `accelerate.utils`.

```python
from accelerate import Accelerator, DeepSpeedPlugin

plugin = DeepSpeedPlugin(zero_stage=2, gradient_accumulation_steps=4)
accelerator = Accelerator(deepspeed_plugin=plugin, mixed_precision="bf16")
```

Key fields:

- `hf_ds_config`: DeepSpeed config dict/path/object.
- `zero_stage`: `0`, `1`, `2`, `3`.
- `gradient_accumulation_steps`, `gradient_clipping`.
- `offload_optimizer_device`, `offload_param_device`: `none`, `cpu`, `nvme`.
- `offload_optimizer_nvme_path`, `offload_param_nvme_path`.
- `zero3_init_flag`, `zero3_save_16bit_model`.
- `transformer_moe_cls_names`.
- `enable_msamp`, `msamp_opt_level`.

Environment fallbacks use names such as `ACCELERATE_DEEPSPEED_ZERO_STAGE`, `ACCELERATE_DEEPSPEED_CONFIG_FILE`, `ACCELERATE_GRADIENT_ACCUMULATION_STEPS`, and `ACCELERATE_DEEPSPEED_OFFLOAD_*`.

### `FullyShardedDataParallelPlugin`

```python
from accelerate import Accelerator, FullyShardedDataParallelPlugin

fsdp = FullyShardedDataParallelPlugin(
    fsdp_version=2,
    reshard_after_forward=True,
    auto_wrap_policy="transformer_based_wrap",
)
accelerator = Accelerator(fsdp_plugin=fsdp, mixed_precision="bf16")
```

Key fields:

- `fsdp_version`: `1` or `2`.
- `sharding_strategy` for FSDP1; `reshard_after_forward` for FSDP2.
- `backward_prefetch`, `forward_prefetch`, `limit_all_gathers`.
- `mixed_precision_policy`.
- `auto_wrap_policy`, `transformer_cls_names_to_wrap`, `min_num_params`.
- `cpu_offload`, `ignored_modules`.
- `state_dict_type`, `state_dict_config`, `optim_state_dict_config`.
- `activation_checkpointing`, `cpu_ram_efficient_loading`, `sync_module_states`, `use_orig_params`.

Environment fallbacks use the `FSDP_` prefix, such as `FSDP_VERSION`, `FSDP_RESHARD_AFTER_FORWARD`, `FSDP_SHARDING_STRATEGY`, and `FSDP_OFFLOAD_PARAMS`.

### `MegatronLMPlugin`

```python
from accelerate import Accelerator, MegatronLMPlugin

megatron = MegatronLMPlugin(tp_degree=2, pp_degree=2, num_micro_batches=4, sequence_parallelism=True)
accelerator = Accelerator(megatron_lm_plugin=megatron)
```

Key fields include `tp_degree`, `pp_degree`, `num_micro_batches`, `sequence_parallelism`, `recompute_activations`, distributed optimizer flags, scheduler fields, and custom provider/loss/batch functions. Use only for Megatron-compatible projects.

## Torch Native Parallelism APIs

### `TorchTensorParallelPlugin`

```python
from accelerate.utils import TorchTensorParallelPlugin

tp = TorchTensorParallelPlugin(tp_size=2)
```

Fields: `tp_size`, optional `torch_device_mesh`.

### Parallelism Config Classes

Accelerate includes config dataclasses for torch tensor/context parallelism and DeepSpeed sequence parallelism. User-facing launch keys are under `parallelism_config`, including `parallelism_config_dp_replicate_size`, `parallelism_config_dp_shard_size`, `parallelism_config_tp_size`, `parallelism_config_cp_size`, `parallelism_config_sp_size`, and related CP/SP backend options.

## Precision and FP8 APIs

### `TERecipeKwargs`

```python
from accelerate.utils import TERecipeKwargs

kwargs = TERecipeKwargs(fp8_format="HYBRID", amax_compute_algo="most_recent")
```

Requires `transformer-engine`. Fields include `use_autocast_during_eval`, `margin`, `interval`, `fp8_format`, `amax_history_len`, `amax_compute_algo`, `override_linear_precision`, and `use_mxfp8_block_scaling`.

### `AORecipeKwargs`

```python
from accelerate.utils import AORecipeKwargs

kwargs = AORecipeKwargs(pad_inner_dim=True, enable_fsdp_float8_all_gather=True)
```

Requires `torchao`. Fields include `config`, `module_filter_func`, `pad_inner_dim`, and `enable_fsdp_float8_all_gather`.

### `MSAMPRecipeKwargs`

```python
from accelerate.utils import MSAMPRecipeKwargs

kwargs = MSAMPRecipeKwargs(opt_level="O2")
```

Requires `ms-amp`. `opt_level` must be `O1` or `O2`.

### `FP8RecipeKwargs`

Deprecated compatibility wrapper. Prefer `TERecipeKwargs`, `AORecipeKwargs`, or `MSAMPRecipeKwargs`.

## Quantization APIs

### `BnbQuantizationConfig`

```python
from accelerate.utils import BnbQuantizationConfig

config = BnbQuantizationConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype="bf16")
```

Requires `bitsandbytes`. Key fields: `load_in_8bit`, `load_in_4bit`, `llm_int8_threshold`, `bnb_4bit_quant_type`, `bnb_4bit_use_double_quant`, `bnb_4bit_compute_dtype`, `torch_dtype`, `skip_modules`, `keep_in_fp32_modules`.

Related utilities include `init_empty_weights`, `load_and_quantize_model`, `infer_auto_device_map`, and `load_checkpoint_and_dispatch`; route large-model inference details to the appropriate root skill/reference if present.

## Compile API

### `TorchDynamoPlugin`

```python
from accelerate.utils import TorchDynamoPlugin

dynamo = TorchDynamoPlugin(backend="inductor", mode="default", use_regional_compilation=True)
```

Fields: `backend`, `mode`, `fullgraph`, `dynamic`, `options`, `disable`, `use_regional_compilation`.

## DDP and Process Group Kwargs

### `DistributedDataParallelKwargs`

```python
from accelerate import DDPCommunicationHookType, DistributedDataParallelKwargs

ddp = DistributedDataParallelKwargs(
    find_unused_parameters=True,
    comm_hook=DDPCommunicationHookType.BF16,
)
```

Fields mirror PyTorch DDP arguments such as `broadcast_buffers`, `bucket_cap_mb`, `find_unused_parameters`, `gradient_as_bucket_view`, `static_graph`, plus Accelerate hook fields `comm_hook`, `comm_wrapper`, and `comm_state_option`.

### `InitProcessGroupKwargs`

```python
from datetime import timedelta
from accelerate.utils import InitProcessGroupKwargs

process_group = InitProcessGroupKwargs(backend="nccl", timeout=timedelta(seconds=900))
```

Fields: `backend`, `init_method`, `timeout`. Defaults differ by backend; NCCL gets a shorter default timeout than non-NCCL.

## Launch/Config Key Families

- DeepSpeed: `distributed_type: DEEPSPEED`, `deepspeed_config`, `deepspeed_config_file`, `zero_stage`, offload keys, gradient accumulation/clipping keys.
- FSDP: `distributed_type: FSDP`, `fsdp_config`, `fsdp_version`, `fsdp_auto_wrap_policy`, `fsdp_reshard_after_forward`, `fsdp_state_dict_type`, `fsdp_transformer_layer_cls_to_wrap`.
- FP8: `mixed_precision: fp8`, `fp8_config`, `fp8_backend`, `fp8_format`, amax keys, `fp8_opt_level`, torchao FSDP float8 keys.
- Compile: `dynamo_backend`, `dynamo_mode`, `dynamo_use_fullgraph`, `dynamo_use_dynamic`, `dynamo_use_regional_compilation`.
- TPU/XLA: TPU launch flags and `distributed_type: XLA` config paths.
- Native parallelism: `parallelism_config` and `--use_parallelism_config`, requiring FSDP2.

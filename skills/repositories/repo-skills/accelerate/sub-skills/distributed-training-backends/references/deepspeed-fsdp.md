# DeepSpeed and FSDP/FSDP2

This reference covers backend selection, plugin/config objects, and launch/config implications for DeepSpeed and PyTorch FSDP in Accelerate. Use it after the generic `Accelerator` loop shape is known.

## Choose Between DeepSpeed and FSDP

| Need | Prefer | Why |
| --- | --- | --- |
| ZeRO stages 1/2/3, DeepSpeed JSON, CPU/NVMe offload, DeepSpeed optimizer/scheduler features | DeepSpeed | Accelerate forwards a DeepSpeed config through `DeepSpeedPlugin` and launch `deepspeed_config` keys. |
| PyTorch-native sharding, state-dict controls, transformer auto-wrap, no DeepSpeed runtime dependency | FSDP | Accelerate wraps via `FullyShardedDataParallelPlugin` and PyTorch FSDP APIs. |
| FSDP plus native tensor/context parallelism | FSDP2 | `parallelism_config` requires `--use_fsdp` with `--fsdp_version=2`. |
| Existing model code already expects Megatron/DeepSpeed internals | DeepSpeed or Megatron-LM | Avoid rewriting backend-specific optimizer/scheduler assumptions unless the user asks. |
| CPU-only validation | Neither as execution target | Validate config shape only; do not claim hardware-backed training works. |

## DeepSpeed

### Entry Points

- `Accelerator(deepspeed_plugin=DeepSpeedPlugin(...))` for explicit Python configuration.
- `accelerate launch --use_deepspeed ...` or a config file with `distributed_type: DEEPSPEED` and `deepspeed_config:` for CLI-driven runs.
- Multiple-model cases can pass a dictionary of `DeepSpeedPlugin` objects keyed by model role; enable the desired plugin before preparing the matching model.

### `DeepSpeedPlugin` Fields

Important constructor fields and corresponding DeepSpeed config concepts:

- `hf_ds_config`: dict, path, or `HfDeepSpeedConfig` object. If provided, the config must include `zero_optimization`.
- `zero_stage`: `0`, `1`, `2`, or `3`; maps to `zero_optimization.stage`.
- `gradient_accumulation_steps`: maps to `gradient_accumulation_steps`; can be `auto` in JSON if Accelerate fills it from runtime values.
- `gradient_clipping`: maps to `gradient_clipping`.
- `offload_optimizer_device`: `none`, `cpu`, or `nvme`; only meaningful for ZeRO-2/3.
- `offload_param_device`: `none`, `cpu`, or `nvme`; only meaningful for ZeRO-3.
- `offload_optimizer_nvme_path` and `offload_param_nvme_path`: needed only when the matching offload device is `nvme`.
- `zero3_init_flag`: enables `deepspeed.zero.Init` style construction for massive models; only valid with ZeRO-3.
- `zero3_save_16bit_model`: maps to `zero_optimization.stage3_gather_16bit_weights_on_model_save`.
- `transformer_moe_cls_names`: comma-separated, case-sensitive MoE layer class names.
- `enable_msamp` and `msamp_opt_level`: enable MS-AMP FP8 through DeepSpeed for stages 0/1/2; ZeRO-3 is not supported for this path.

### DeepSpeed Config Shape

A minimal Accelerate launch config points to a DeepSpeed JSON or uses inline DeepSpeed settings:

```yaml
distributed_type: DEEPSPEED
mixed_precision: bf16
deepseed_config:  # typo: should be deepspeed_config; validators should catch this
  zero_stage: 2
```

Correct shape:

```yaml
distributed_type: DEEPSPEED
mixed_precision: bf16
deepspeed_config:
  zero_stage: 2
  gradient_accumulation_steps: 4
  gradient_clipping: 1.0
  offload_optimizer_device: none
```

A DeepSpeed JSON should include `zero_optimization`:

```json
{
  "train_batch_size": "auto",
  "train_micro_batch_size_per_gpu": "auto",
  "gradient_accumulation_steps": "auto",
  "zero_optimization": {
    "stage": 3,
    "offload_optimizer": {"device": "cpu"},
    "offload_param": {"device": "cpu"},
    "stage3_gather_16bit_weights_on_model_save": true
  }
}
```

### DeepSpeed Precedence Rules

- If a full `hf_ds_config` dict/path is passed, its explicit values are authoritative unless fields are `auto` or Accelerate fills matching values.
- If no DeepSpeed config is passed, `DeepSpeedPlugin` creates a config from constructor fields and environment variables.
- Mismatches between plugin kwargs and explicit DeepSpeed JSON values can raise errors or silently keep the JSON value depending on the mapped field; inspect `plugin.deepspeed_config` after construction when debugging.
- `deepspeed_config_file` is a launch/config concept; `hf_ds_config` is the Python plugin concept.

## FSDP and FSDP2

### Entry Points

- `Accelerator(fsdp_plugin=FullyShardedDataParallelPlugin(...))` for explicit Python configuration.
- `accelerate launch --use_fsdp ...` or a config file with `distributed_type: FSDP` and `fsdp_config:` for CLI-driven runs.
- `accelerate to-fsdp2` can help convert old FSDP1-style config files to FSDP2 naming.

### `FullyShardedDataParallelPlugin` Fields

Important constructor fields:

- `fsdp_version`: `1` or `2`; FSDP2 requires a sufficiently recent PyTorch.
- `sharding_strategy`: FSDP1 strategy such as `FULL_SHARD`, `SHARD_GRAD_OP`, `NO_SHARD`, or `HYBRID_SHARD`; deprecated in favor of `reshard_after_forward`.
- `reshard_after_forward`: string strategy for FSDP1, boolean for FSDP2.
- `backward_prefetch`: FSDP1 prefetch option; FSDP2 ignores or warns on unsupported values.
- `mixed_precision_policy`: string (`fp8`, `fp16`, `bf16`, `fp32`), dict with dtype keys, or PyTorch policy object.
- `auto_wrap_policy`: `transformer_based_wrap`, `size_based_wrap`, `no_wrap`, or callable.
- `transformer_cls_names_to_wrap`: class names for transformer-based wrapping; use exact class names such as `BertLayer`, `GPTJBlock`, or model-specific block classes.
- `min_num_params`: threshold for `size_based_wrap`.
- `cpu_offload`: boolean or PyTorch CPU offload policy.
- `ignored_modules`: modules or regex-style names to skip.
- `state_dict_type`: `FULL_STATE_DICT`, `LOCAL_STATE_DICT`, or `SHARDED_STATE_DICT`; FSDP2 has a smaller supported set.
- `activation_checkpointing`, `limit_all_gathers`, `forward_prefetch`, `use_orig_params`, `sync_module_states`, `cpu_ram_efficient_loading`.

### FSDP Config Shape

FSDP1-style config:

```yaml
distributed_type: FSDP
mixed_precision: bf16
fsdp_config:
  fsdp_auto_wrap_policy: TRANSFORMER_BASED_WRAP
  fsdp_backward_prefetch_policy: BACKWARD_PRE
  fsdp_offload_params: false
  fsdp_sharding_strategy: FULL_SHARD
  fsdp_state_dict_type: FULL_STATE_DICT
  fsdp_transformer_layer_cls_to_wrap: BertLayer
  fsdp_use_orig_params: true
```

FSDP2-style config with native parallelism support:

```yaml
distributed_type: FSDP
mixed_precision: bf16
num_processes: 8
fsdp_config:
  fsdp_version: 2
  fsdp_auto_wrap_policy: TRANSFORMER_BASED_WRAP
  fsdp_reshard_after_forward: true
  fsdp_state_dict_type: SHARDED_STATE_DICT
  fsdp_activation_checkpointing: true
parallelism_config:
  parallelism_config_dp_replicate_size: 2
  parallelism_config_dp_shard_size: 2
  parallelism_config_tp_size: 2
  parallelism_config_cp_size: 1
```

### FSDP Wrap Guidance

- For Transformers models, prefer `transformer_based_wrap` and exact block class names. If available, use the model's `_no_split_modules` as the source of classes that should stay together.
- Avoid wrapping shared embeddings, tied weights, or tiny leaf modules separately; this can break tied-parameter assumptions or hurt performance.
- Use `size_based_wrap` only when class-based wrapping is unavailable and the parameter threshold is meaningful for the model.
- FSDP2 expects `reshard_after_forward` to be a boolean. FSDP1 expects a strategy string or enum.
- CPU-RAM-efficient loading is Transformers-specific and implies synchronized module states; it does not mean the whole training can run efficiently on CPU.

## Minimal Python Snippets

DeepSpeed:

```python
from accelerate import Accelerator, DeepSpeedPlugin

plugin = DeepSpeedPlugin(zero_stage=3, offload_optimizer_device="cpu", offload_param_device="cpu")
accelerator = Accelerator(mixed_precision="bf16", deepspeed_plugin=plugin)
```

FSDP2:

```python
from accelerate import Accelerator, FullyShardedDataParallelPlugin

fsdp = FullyShardedDataParallelPlugin(
    fsdp_version=2,
    reshard_after_forward=True,
    auto_wrap_policy="transformer_based_wrap",
    state_dict_type="SHARDED_STATE_DICT",
)
accelerator = Accelerator(mixed_precision="bf16", fsdp_plugin=fsdp)
```

## Validation Checklist

- DeepSpeed config includes `zero_optimization.stage` or launch `deepspeed_config.zero_stage`.
- ZeRO offload choices match the ZeRO stage: optimizer offload for ZeRO-2/3, parameter offload only for ZeRO-3.
- FSDP2 uses `fsdp_reshard_after_forward` as a boolean and avoids FSDP1-only options.
- `parallelism_config` is only used with FSDP2.
- State-dict type and checkpointing expectations are routed to the checkpointing sub-skill before finalizing save/load code.

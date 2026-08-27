# V1 Configs

V1 configs are parsed into four dataclasses: model, data, training, and sampling. The parser accepts YAML, JSON, or CLI-style arguments. YAML/JSON config values can be overridden from the CLI, and unknown keys are rejected unless `ALLOW_EXTRA_KEYS` is enabled.

## Minimal V1 SFT Shape

```yaml
model: Qwen/Qwen3-0.6B
model_class: llm
template: qwen3_nothink
trust_remote_code: true

train_dataset: data/v1_sft_demo.yaml

output_dir: outputs/v1_sft
micro_batch_size: 1
global_batch_size: 1
cutoff_len: 2048
learning_rate: 1.0e-4
max_steps: 10
bf16: false

sample_backend: hf
max_new_tokens: 128
```

Run only when v1 is intended:

```bash
USE_V1=1 llamafactory-cli sft path/to/config.yaml
```

`lmf` is equivalent to `llamafactory-cli`.

## Model Keys

Common model keys:

- `model`: model path or Hugging Face model ID.
- `template`: rendering template; current v1 examples focus on Qwen3-style templates.
- `trust_remote_code`: passed to processor/config/model loading.
- `flash_attn`: one of `eager`, `sdpa`, or `flash_attention_2`; `sdpa` is the default.
- `model_class`: `llm`, `cls`, or `other`.
- `init_config`, `peft_config`, `kernel_config`, `quant_config`: plugin config blocks.

Every non-null plugin config must include `name`.

```yaml
peft_config:
  name: lora
  r: 16
  lora_alpha: 32
  lora_dropout: 0.05
  target_modules: all
```

```yaml
peft_config:
  name: freeze
  freeze_trainable_layers: 1
  freeze_trainable_modules: all
```

```yaml
init_config:
  name: init_on_meta
```

Known initialization names: `init_on_meta`, `init_on_rank0`, `init_on_default`.

## Data Keys

V1 data args are intentionally small:

- `train_dataset`: path, local dataset-info YAML, HF dataset ID, or dataset-info YAML in a dataset repo.
- `eval_dataset`: optional evaluation dataset path.

Dataset-info YAML may describe multiple named datasets. Entries can use:

- `path`: dataset path or ID.
- `source`: defaults to HF hub; `local` uses the local data-loader plugin.
- `split`: defaults to `train`.
- `streaming`: all datasets must agree on streaming mode.
- `size` or `weight`: adjust the generated data index.
- `converter`: built-in names include `alpaca`, `sharegpt`, and `pair`.

V1 does not consume v0 dataset registry keys such as `dataset`, `dataset_dir`, or v0 `dataset_info.json` in the same way.

## Training Keys

Common training keys:

- `output_dir`: output path; defaults to a generated `outputs/<uuid>` path if omitted.
- `micro_batch_size`: per-micro-batch size.
- `global_batch_size`: optional global batch size; defaults from DP size and micro batch size.
- `cutoff_len`: max sequence length.
- `learning_rate`: optimizer learning rate.
- `num_train_epochs`: epoch count when `max_steps` is not set.
- `max_steps`: step cap; overrides epoch count when positive.
- `max_grad_norm`: gradient clipping norm.
- `bf16`: mixed precision flag used by distributed plugins.
- `batching_strategy`: `normal`, `padding_free`, `dynamic_batching`, or `dynamic_padding_free`.
- `batching_workers`: batch generation workers.
- `enable_activation_checkpointing`: enables gradient checkpointing.
- `dist_config`: distributed plugin config.
- `optim_config`: optimizer plugin config.
- `lr_scheduler_config`: scheduler plugin config.
- `seed` and `full_determinism`: set early after parsing.
- `resume_from_checkpoint`: checkpoint path or `auto`.
- `save_steps`, `save_epochs`, `save_ckpt_as_hf`, `save_total_limit`: checkpoint controls.
- `logging_steps`: logging interval.

Batching constraints:

- `dynamic_batching` requires `max_steps > 0`.
- `dynamic_batching` cannot use `save_epochs`; use `save_steps`.
- `padding_free` requires `flash_attn: flash_attention_2`.

## Distributed Configs

FSDP2 example:

```yaml
dist_config:
  name: fsdp2
  dcp_path: null
```

DeepSpeed example:

```yaml
dist_config:
  name: deepspeed
  config_file: path/to/deepspeed.json
```

Context parallel options belong in `dist_config`, but current source requires `dist_config.name: fsdp2` when `cp_size > 1`, and sequence parallel requires flash attention.

Common launch environment:

```bash
USE_V1=1 FORCE_TORCHRUN=1 NPROC_PER_NODE=2 llamafactory-cli sft config.yaml
```

Multi-node variables recognized by the v1 launcher include `NNODES`, `NODE_RANK`, `MASTER_ADDR`, `MASTER_PORT`, `RDZV_ID`, `MIN_NNODES`, `MAX_NNODES`, and `MAX_RESTARTS`.

## Quantization And Kernels

Bitsandbytes QLoRA-style example:

```yaml
quant_config:
  name: bnb
  quantization_bit: 4
```

Automatic quantization currently delegates to bitsandbytes when a valid bit is supplied:

```yaml
quant_config:
  name: auto
  quantization_bit: 4
```

Kernel examples:

```yaml
kernel_config:
  name: auto
  include_kernels: auto
```

```yaml
kernel_config:
  name: liger_kernel
```

Kernel availability depends on device type, model class, optional packages, and registered kernel implementations. Do not assume all kernels are available on CPU-only or minimal environments.

## Sampling Keys

Common sampling keys:

- `sample_backend`: `hf` is the supported safe default.
- `max_new_tokens`: generation length cap.

Although `vllm` appears as an enum value, the current base sampler only constructs the Hugging Face backend. Treat non-HF sampling in v1 as experimental or incomplete unless verified in the target checkout.

## V0-To-V1 Field Mapping

Use this as a review aid, not as an automatic converter:

| V0 habit | V1 equivalent or caveat |
| --- | --- |
| `stage: sft` | choose v1 command `sft` or `train`; no `stage` field needed |
| `do_train: true` | implicit when invoking v1 training command |
| `dataset: name1,name2` | `train_dataset: ...`; often a v1 dataset-info YAML or HF dataset ID |
| `dataset_dir` | not a primary v1 dataclass field |
| `finetuning_type: lora` | `peft_config: {name: lora, ...}` |
| `finetuning_type: freeze` | `peft_config: {name: freeze, ...}` |
| `per_device_train_batch_size` | `micro_batch_size` |
| `gradient_accumulation_steps` | usually expressed through `global_batch_size` versus `micro_batch_size` |
| `deepspeed: ds_config.json` | `dist_config: {name: deepspeed, config_file: ...}` |
| v0 template names | v1 renderer plugins may differ; verify the template exists in v1 |
| v0 DPO/PPO/KTO/RM stage configs | v1 supports RM and SFT routes; DPO route is not enabled; PPO/KTO are v0 routes |

## Static Review Checklist

Before proposing a v1 command:

1. Confirm the command is run with `USE_V1=1`.
2. Confirm the config does not contain obvious v0-only keys unless `ALLOW_EXTRA_KEYS` is intentionally used for experimentation.
3. Confirm each plugin block has `name` when not null.
4. Confirm `train_dataset` points to v1-compatible data or uses a converter.
5. Confirm `sample_backend: hf` unless the user is explicitly developing a non-HF backend.
6. Confirm batching constraints: dynamic batching needs `max_steps`; padding-free needs flash attention.
7. Confirm optional dependencies for quantization, DeepSpeed, FSDP2, Liger, or device kernels before running.

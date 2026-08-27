# Training YAML configuration reference

LLM Foundry training YAMLs are read by the public command:

```bash
llmfoundry train <config.yaml> [overrides...]
```

The command loads the YAML with OmegaConf, merges CLI dotlist overrides, transforms the config, constructs a `TrainConfig`, builds tokenizer/model/dataloaders/evaluators/callbacks/algorithms/loggers/optimizer/scheduler, then creates a Composer `Trainer`.

## Builder signatures to remember

Installed package inspection confirmed these public signatures:

```text
llmfoundry.command_utils.train.train_from_yaml(yaml_path: str, args_list: Optional[list[str]] = None) -> composer.trainer.trainer.Trainer
llmfoundry.utils.builders.build_tokenizer(tokenizer_name: str, tokenizer_kwargs: dict[str, Any]) -> transformers.PreTrainedTokenizerBase
llmfoundry.utils.builders.build_composer_model(name: str, cfg: dict[str, Any], tokenizer: Optional[PreTrainedTokenizerBase], init_context: Optional[ContextManager] = None, master_weights_dtype: Optional[str] = None) -> composer.models.base.ComposerModel
llmfoundry.utils.builders.build_optimizer(model: torch.nn.Module, name: str, optimizer_config: dict[str, Any]) -> torch.optim.optimizer.Optimizer
llmfoundry.utils.builders.build_scheduler(name: str, scheduler_config: Optional[dict[str, Any]] = None) -> composer.optim.scheduler.ComposerScheduler
llmfoundry.utils.builders.build_callback(name: str, kwargs: Optional[dict[str, Any]] = None, train_config: Any = None) -> composer.core.callback.Callback
llmfoundry.utils.builders.build_logger(name: str, kwargs: Optional[dict[str, Any]] = None) -> composer.loggers.logger_destination.LoggerDestination
```

These signatures explain the YAML shape: registry `name` keys select model, callback, logger, optimizer, and scheduler implementations; the remaining mapping entries become constructor keyword arguments.

## Required top-level training fields

The `TrainConfig` mandatory fields are:

| Field | Purpose | Practical note |
| --- | --- | --- |
| `model` | Model registry selection and constructor kwargs. | Must contain `name`; common values include `mpt_causal_lm`, `hf_causal_lm`, and `hf_t5`. |
| `tokenizer` | Tokenizer name and kwargs. | Must contain `name`; for HF tokenizers, kwargs are passed to `AutoTokenizer.from_pretrained`. |
| `optimizer` | Optimizer registry selection and kwargs. | Must contain `name`; common choices include `decoupled_adamw` and `decoupled_lionw`. |
| `scheduler` | Composer scheduler registry selection and kwargs. | Must contain `name`; common choices include `cosine_with_warmup` and `linear_decay_with_warmup`. |
| `train_loader` | Training dataloader config. | Must contain `name`; common choices are `text` and `finetuning`. |
| `device_train_batch_size` | Per-device batch size after transforms. | Most user YAMLs provide `global_train_batch_size` plus `device_train_microbatch_size`; LLM Foundry transforms derive `device_train_batch_size`. |
| `device_eval_batch_size` | Eval batch size per device. | Required even when eval is disabled in many templates. Use a small integer for ICL/eval. |
| `max_duration` | Training duration. | Examples: `10ba`, `4800ba`, `1ep`. Always bound smoke runs. |
| `max_seq_len` | Sequence length used by model/data/eval. | Keep top-level, tokenizer `model_max_length`, loader dataset `max_seq_len`, and model overrides consistent. |

If a YAML has neither `device_train_batch_size` nor `global_train_batch_size`, it is likely incomplete. Prefer `global_train_batch_size` in user-authored YAMLs so the package can compute per-device batch and gradient accumulation from world size.

## Common optional TrainConfig fields

| Category | Fields |
| --- | --- |
| Seed/precision | `seed`, `precision` |
| User code/imports | `code_paths` |
| CUDA allocation | `max_split_size_mb`, `expandable_segments`, `cuda_load_lazy` |
| Distributed | `dist_timeout`, `fsdp_config`, `tp_config`, `accumulate_train_batch_on_tokens` |
| Evaluation during training | `eval_interval`, `eval_loader`, `eval_loaders`, `icl_tasks`, `icl_subset_num_batches`, `icl_seq_len`, `eval_first`, `eval_subset_num_batches` |
| Logging | `loggers`, `progress_bar`, `log_to_console`, `python_log_level`, `console_log_interval`, `log_config`, `metadata`, `flatten_metadata`, `run_name` |
| Callbacks/algorithms | `callbacks`, `algorithms` |
| Checkpoints | `save_folder`, `save_latest_filename`, `save_overwrite`, `save_weights_only`, `save_filename`, `save_interval`, `save_num_checkpoints_to_keep`, `load_path`, `load_weights_only`, `load_strict_model_weights`, `load_ignore_keys`, `save_ignore_keys`, `only_hf_checkpoint`, `only_composer_checkpoint`, `autoresume` |
| Dataloader bounds | `train_subset_num_batches`, `device_train_microbatch_size`, `global_train_batch_size`, `spin_dataloaders` |
| Compilation/profiling | `compile_config`, `profiler` |
| Template variables | `variables` |

Do not add arbitrary top-level variables unless a config transform is known to consume them. Put custom constants under `variables` and reference them with OmegaConf interpolation such as `${variables.max_seq_len}`.

## Model section

Common MPT-from-scratch shape:

```yaml
model:
  name: mpt_causal_lm
  init_device: meta
  d_model: 768
  n_heads: 12
  n_layers: 12
  expansion_ratio: 4
  max_seq_len: ${variables.max_seq_len}
  vocab_size: 50368
  attn_config:
    attn_impl: flash
```

Common HF causal LM fine-tuning shape:

```yaml
model:
  name: hf_causal_lm
  pretrained_model_name_or_path: <hf-model>
  pretrained: true
  config_overrides:
    max_seq_len: ${variables.max_seq_len}
    attn_config:
      attn_impl: flash
  use_auth_token: false
```

Notes:

- `hf_causal_lm` can be used with `pretrained: false` to train a HF architecture from scratch, provided the architecture config is compatible.
- Gated models such as some Llama variants need `use_auth_token: true` and an external Hugging Face token in the environment.
- `load_in_8bit` is rejected for training; route quantized inference elsewhere.
- `init_device: meta` and `init_device: mixed` are only valid with FSDP-style initialization. Without FSDP, use `cpu`.
- PEFT/LoRA uses `model.peft_config`; optional PEFT dependencies and target module names must match the model.

## Tokenizer section

```yaml
tokenizer:
  name: <hf-tokenizer-or-registered-tokenizer>
  kwargs:
    model_max_length: ${variables.max_seq_len}
```

Tokenizer building can download files, require credentials, and fail if the tokenizer has no EOS token. Set `TOKENIZERS_PARALLELISM=false` if noisy tokenizer warnings appear in custom environments; LLM Foundry sets this during tokenizer construction.

## Train loader patterns

### MDS text/pretraining loader

```yaml
train_loader:
  name: text
  dataset:
    local: ${variables.data_local}
    remote: ${variables.data_remote}
    split: train
    shuffle: true
    max_seq_len: ${variables.max_seq_len}
    shuffle_seed: ${variables.global_seed}
  drop_last: true
  num_workers: 8
```

Use this for pretraining, continued pretraining, domain adaptation, and sequence-length adaptation on pre-tokenized MDS shards.

### Fine-tuning loader from local JSON/JSONL

```yaml
train_loader:
  name: finetuning
  dataset:
    hf_name: json
    hf_kwargs:
      data_dir: <data-local>
    preprocessing_fn: <python.module>:<function>
    split: train
    shuffle: true
    max_seq_len: ${variables.max_seq_len}
    decoder_only_format: true
  drop_last: true
  num_workers: 8
```

Use this only when the local data can be loaded by HF `datasets`. If raw examples do not already have `prompt` and `response`, provide a preprocessing function or prepare the data elsewhere.

### Fine-tuning loader from MDS streams

```yaml
train_loader:
  name: finetuning
  dataset:
    streams:
      train_stream:
        remote: <data-remote>
        local: <data-local>
        split: train
    shuffle: true
    max_seq_len: ${variables.max_seq_len}
    decoder_only_format: true
```

Use stream entries for local or remote MDS fine-tuning data. Remote credentials and local cache size are environment concerns.

## Eval loaders inside training

A single eval loader mirrors the train loader shape:

```yaml
eval_loader:
  name: text
  dataset:
    local: ${variables.data_local}
    remote: ${variables.data_remote}
    split: val
    shuffle: false
    max_seq_len: ${variables.max_seq_len}
  drop_last: false
  num_workers: 8
```

Multiple eval loaders are supplied as a list and each item needs `label`:

```yaml
eval_loader:
  - label: validation_short
    name: text
    dataset:
      local: <data-local>
      split: val_short
      max_seq_len: ${variables.max_seq_len}
    drop_last: false
    num_workers: 4
```

`icl_tasks` can be supplied for in-training ICL evaluation, but the detailed task schema belongs to evaluation. Do not use ICL evaluation with `hf_t5` training configs.

## Optimizer and scheduler sections

Registry entries observed in the installed package include these optimizers: `adalr_lion`, `clip_lion`, `decoupled_adamw`, `decoupled_lionw`, `no_op`.

Schedulers include: `constant_with_warmup`, `cosine_with_warmup`, `inv_sqrt_with_warmup`, `linear_decay_with_warmup`.

Example:

```yaml
scheduler:
  name: cosine_with_warmup
  t_warmup: 100ba
  alpha_f: 0.1

optimizer:
  name: decoupled_adamw
  lr: 6.0e-4
  betas: [0.9, 0.95]
  eps: 1.0e-8
  weight_decay: 0.0
```

Optimizer configs may include `disable_grad` or `param_groups` to freeze or group parameters. Do not include a `params` key; LLM Foundry extracts parameters from the model.

## Algorithms

Training examples commonly enable gradient clipping:

```yaml
algorithms:
  gradient_clipping:
    clipping_type: norm
    clipping_threshold: 1.0
```

Installed algorithm names include `alibi`, `gated_linear_units`, `gradient_clipping`, and `low_precision_layernorm`. Model architecture settings may be a better location than algorithms for some features; route registry/API extension questions to package-apis-configuration.

## Precision and optional kernels

Common values:

- `precision: fp32` for CPU or conservative smoke runs.
- `precision: amp_bf16` for A100/H100-style GPU training.
- `precision: amp_fp8` only when TransformerEngine layers are installed and enabled.

Flash Attention patterns:

```yaml
model:
  attn_config:
    attn_impl: flash
```

or for some HF models:

```yaml
model:
  name: hf_causal_lm
  attn_implementation: flash_attention_2
```

Flash Attention, TransformerEngine, and MegaBlocks/MoE settings are optional-backend dependent. Fall back to `attn_impl: torch`, CPU-sized model dimensions, and `precision: fp32` for smoke checks when the GPU stack is not available.

## FSDP configuration

Common FSDP block:

```yaml
fsdp_config:
  sharding_strategy: FULL_SHARD
  mixed_precision: PURE
  activation_checkpointing: true
  activation_checkpointing_reentrant: false
  activation_cpu_offload: false
  limit_all_gathers: true
```

Notes:

- If world size is one, LLM Foundry warns and disables FSDP/TP behavior.
- `init_device: meta` without FSDP is reverted to CPU; `init_device: mixed` without FSDP is an error.
- For very large checkpoints, `state_dict_type: sharded` can reduce rank-0 pressure and changes default latest-checkpoint naming.
- Activation checkpointing and smaller microbatches reduce memory but may reduce throughput.

## Tensor parallel configuration

`tp_config` is optional and must include both:

```yaml
tp_config:
  strategy: <strategy-name>
  tensor_parallel_degree: <degree>
```

Tensor parallelism is not supported for MoE models in the inspected package logic. TP strategy names and deep registry details belong to package-apis-configuration.

## Batch-size fields

Prefer:

```yaml
global_train_batch_size: 256
device_train_microbatch_size: 16
device_eval_batch_size: 16
```

LLM Foundry computes:

- `device_train_batch_size = global_train_batch_size / world_size`;
- `device_train_grad_accum = ceil(device_train_batch_size / device_train_microbatch_size)` unless microbatching is `auto`;
- `device_train_microbatch_size` is reduced if it exceeds per-device batch size.

Rules of thumb:

- `global_train_batch_size` must be divisible by the effective data-parallel world size.
- `device_train_microbatch_size: auto` can help find a fit, but FSDP auto microbatching can be less predictable.
- For OOM, reduce `device_train_microbatch_size` first, then enable activation checkpointing, then consider CPU offload as a last resort.
- Keep `device_eval_batch_size` small for ICL tasks and long contexts.

## Checkpoint fields at a glance

See [checkpointing-and-callbacks.md](checkpointing-and-callbacks.md) for details. Common fields:

```yaml
save_folder: <save-folder>
save_interval: 500ba
save_num_checkpoints_to_keep: 1
save_overwrite: false
load_path: <load-checkpoint>
load_weights_only: true
autoresume: false
```

If `run_name`, `save_folder`, and default latest checkpoint names are set, LLM Foundry can default autoresume behavior to true when overwrite and weights-only saving are not requested.

## Config-probe checklist

Before training, verify:

- required top-level fields exist;
- `model.name`, `tokenizer.name`, `optimizer.name`, and `scheduler.name` are present;
- `train_loader.name` is `text` or `finetuning` and has an appropriate dataset shape;
- MDS loader paths have `local`, optional `remote`, and `split`;
- local JSON fine-tuning has `hf_name: json`, `hf_kwargs.data_dir`, and either prompt/response data or `preprocessing_fn`;
- `max_seq_len` is consistent across top-level, tokenizer, model, train loader, and eval loader;
- `global_train_batch_size` is compatible with planned world size;
- `precision`, `attn_impl`, FSDP, and TP match the backend;
- save/load paths and credentials are intentional;
- smoke runs override `max_duration`, `eval_interval`, and save behavior.

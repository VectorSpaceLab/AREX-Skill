# Training and fine-tuning workflows

This reference shows how to create and adapt LLM Foundry training YAMLs without depending on a source checkout. Use placeholders such as `<config.yaml>`, `<data-local>`, `<data-remote>`, `<save-folder>`, `<load-checkpoint>`, and `<hf-model>`.

## Common launch pattern

LLM Foundry exposes a public training CLI:

```bash
llmfoundry train <config.yaml> [overrides...]
```

Overrides are OmegaConf/Composer dotlist values merged on top of the YAML:

```bash
llmfoundry train <config.yaml> \
  max_duration=10ba \
  eval_interval=0 \
  variables.data_local=<data-local> \
  train_loader.dataset.split=train_small \
  eval_loader.dataset.split=val_small \
  save_folder=<save-folder>
```

Use shell quoting when values contain spaces, brackets, braces, commas that the shell interprets, or colons in ambiguous contexts:

```bash
llmfoundry train <config.yaml> \
  'model.config_overrides.attn_config.attn_impl=flash' \
  'callbacks.speed_monitor.window_size=10' \
  'loggers.wandb={}'
```

Run the bundled probe before the real launch:

```bash
python scripts/llmfoundry_config_probe.py <config.yaml> max_duration=2ba eval_interval=0
```

The probe is static. It is useful for catching missing top-level sections and suspicious path/batch/checkpoint settings, but it cannot prove that model weights, tokenizers, CUDA kernels, remote storage, or datasets are available.

## Pretraining from MDS text data

Pretraining and continued pretraining normally use a `text` dataloader reading MDS/StreamingDataset shards. A minimal shape is:

```yaml
variables:
  data_local: <data-local>
  data_remote: null
  max_seq_len: 2048
  global_seed: 17

max_seq_len: ${variables.max_seq_len}
run_name: <run-name>

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

tokenizer:
  name: EleutherAI/gpt-neox-20b
  kwargs:
    model_max_length: ${variables.max_seq_len}

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

eval_loader:
  name: text
  dataset:
    local: ${variables.data_local}
    remote: ${variables.data_remote}
    split: val
    shuffle: false
    max_seq_len: ${variables.max_seq_len}
    shuffle_seed: ${variables.global_seed}
  drop_last: false
  num_workers: 8

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

algorithms:
  gradient_clipping:
    clipping_type: norm
    clipping_threshold: 1.0

max_duration: 4800ba
eval_interval: 500ba
global_train_batch_size: 256
seed: ${variables.global_seed}
device_eval_batch_size: 16
device_train_microbatch_size: 16
precision: amp_bf16
fsdp_config:
  sharding_strategy: FULL_SHARD
  mixed_precision: PURE
  activation_checkpointing: false
  activation_checkpointing_reentrant: false
  activation_cpu_offload: false
  limit_all_gathers: true
callbacks:
  speed_monitor: {window_size: 10}
  lr_monitor: {}
  memory_monitor: {}
  runtime_estimator: {}
```

Adapt the data path without editing the YAML when possible:

```bash
llmfoundry train <pretrain.yaml> \
  variables.data_local=<data-local> \
  variables.data_remote=<data-remote> \
  train_loader.dataset.split=train_small \
  eval_loader.dataset.split=val_small
```

If `remote` is blank, the MDS split folders must already exist under `local`. If `remote` is an object store URI, `local` should be a writable cache path and credentials must be configured outside the YAML.

## Supervised or instruction fine-tuning

SFT uses `train_loader.name: finetuning`. The dataset can come from the Hugging Face Hub, a local JSON/JSONL dataset loaded through HF `datasets`, or pre-converted MDS streams.

Local JSON/JSONL pattern:

```yaml
max_seq_len: 512
model:
  name: hf_causal_lm
  pretrained_model_name_or_path: <hf-model>
  pretrained: true

tokenizer:
  name: <hf-model>
  kwargs:
    model_max_length: ${max_seq_len}

train_loader:
  name: finetuning
  dataset:
    hf_name: json
    hf_kwargs:
      data_dir: <data-local>
    preprocessing_fn: <python.module>:<function>
    split: train
    shuffle: true
    max_seq_len: ${max_seq_len}
    decoder_only_format: true
  drop_last: true
  num_workers: 8

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
max_duration: 1ep
global_train_batch_size: 8
device_eval_batch_size: 8
device_train_microbatch_size: 8
precision: fp32
```

If your data already has `prompt` and `response` fields, `preprocessing_fn` can often be omitted. If not, route data-format conversion and prompt/response policy to data-preparation before launching training.

MDS fine-tuning pattern:

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
    max_seq_len: ${max_seq_len}
    decoder_only_format: true
```

## Domain adaptation and sequence-length adaptation

Treat domain adaptation and sequence-length adaptation as continued pretraining unless the data is labeled prompt/response data. This means:

- use `train_loader.name: text` with MDS shards;
- set tokenizer and `train_loader.dataset.max_seq_len` to the adaptation length;
- set the top-level `max_seq_len` and model override consistently;
- choose a shorter bounded duration for exploratory runs and scale only after data and memory are validated.

Example override set:

```bash
llmfoundry train <domain-adapt.yaml> \
  variables.data_local=<data-local> \
  variables.data_remote=<data-remote> \
  variables.max_seq_len=4096 \
  max_seq_len=4096 \
  model.config_overrides.max_seq_len=4096 \
  train_loader.dataset.max_seq_len=4096 \
  eval_loader.dataset.max_seq_len=4096 \
  max_duration=100ba
```

Only use overrides that match your YAML interpolation structure. If the YAML already routes `model.config_overrides.max_seq_len` through `${variables.max_seq_len}`, overriding the variable is enough.

## CPU smoke configurations

A CPU smoke run should be intentionally tiny:

```yaml
model:
  name: mpt_causal_lm
  init_device: cpu
  d_model: 16
  n_heads: 4
  n_layers: 4
  expansion_ratio: 5
  max_seq_len: 128
  vocab_size: 50368
  attn_config:
    attn_impl: torch
  loss_fn: torch_crossentropy
precision: fp32
max_duration: 2ba
eval_interval: 0
global_train_batch_size: 8
device_train_microbatch_size: 1
device_eval_batch_size: 1
```

For CPU smoke tests:

- use `attn_impl: torch`, not `flash`;
- use `precision: fp32` unless your CPU stack is known to support lower precision;
- avoid `init_device: meta` unless FSDP is actually enabled by a distributed launch;
- use tiny local MDS or JSONL data that is already prepared;
- set `save_folder` only if you intend to write a checkpoint.

## GPU, multi-GPU, and multi-node scale

Large examples usually use A100/H100-class GPUs, CUDA-specific optional packages, FSDP, mixed precision, and MDS data. Scale in this order:

1. Static probe the YAML.
2. Single-process CPU or tiny GPU smoke run with `max_duration=1ba` or `2ba`, `eval_interval=0`, and no remote checkpoint upload.
3. Single-node distributed run with small split and bounded checkpointing.
4. Full data, full duration, object-store checkpoints, and monitoring.
5. Multi-node run only after the single-node recipe is stable.

For a cluster launcher, keep the LLM Foundry entrypoint as:

```bash
llmfoundry train <config.yaml> [overrides...]
```

but ensure the launcher supplies world size, node rank, master address/port, GPUs per node, and the same environment on every worker. If using a platform job YAML, adapt only the generic ideas: image, package install, command, compute GPU count, run name, and injected parameters. Treat platform examples as reference-only because cluster names, credentials, object-store paths, and account integrations are site-specific.

## Bounded smoke-run command recipes

Pretraining smoke with existing MDS:

```bash
python scripts/llmfoundry_config_probe.py <pretrain.yaml> \
  variables.data_local=<data-local> \
  train_loader.dataset.split=train_small \
  eval_loader.dataset.split=val_small \
  max_duration=2ba eval_interval=0

llmfoundry train <pretrain.yaml> \
  variables.data_local=<data-local> \
  train_loader.dataset.split=train_small \
  eval_loader.dataset.split=val_small \
  max_duration=2ba eval_interval=0 \
  save_folder=null
```

SFT smoke with local JSONL:

```bash
python scripts/llmfoundry_config_probe.py <sft.yaml> \
  train_loader.dataset.hf_kwargs.data_dir=<data-local> \
  train_loader.dataset.split=train \
  max_duration=1ba eval_interval=0

llmfoundry train <sft.yaml> \
  train_loader.dataset.hf_kwargs.data_dir=<data-local> \
  max_duration=1ba eval_interval=0 \
  save_folder=null
```

Do not treat a passing probe as permission to run a large training job. Confirm data size, backend, token/model caches, checkpoint destination, and budget first.

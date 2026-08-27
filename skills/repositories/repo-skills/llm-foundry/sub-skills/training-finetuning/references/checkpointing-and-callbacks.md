# Checkpointing, callbacks, loggers, optimizers, and schedulers

This reference covers training-loop support components owned by the training-finetuning sub-skill. It does not cover checkpoint export to Hugging Face, ONNX, or FasterTransformer formats.

## Save checkpoints

Common local or object-store checkpoint settings:

```yaml
run_name: <run-name>
save_folder: <save-folder>
save_interval: 500ba
save_num_checkpoints_to_keep: 1
save_overwrite: false
save_weights_only: false
```

Default filename behavior:

- full Composer state dict: `ep{epoch}-ba{batch}-rank{rank}.pt` and latest `latest-rank{rank}.pt`;
- sharded state dict (`fsdp_config.state_dict_type: sharded`): latest name similar to `latest-sharded-rank{rank}` unless overridden.

Use `save_num_checkpoints_to_keep: 1` for bounded disk use in smoke or early adaptation runs. Use a remote object-store `save_folder` only when credentials, write permissions, and lifecycle policy are already configured.

## Load checkpoints

Common load settings:

```yaml
load_path: <load-checkpoint>
load_weights_only: true
load_strict_model_weights: true
load_ignore_keys: null
save_ignore_keys: null
```

Use `load_weights_only: true` for fine-tuning from a pretraining checkpoint when optimizer state and scheduler state should not resume. Use `load_weights_only: false` only when truly resuming the same run state.

If architecture, tokenizer, vocab size, LoRA/PEFT settings, or model names changed, strict loading may fail. Lower strictness only after confirming the mismatch is expected.

## Autoresume

LLM Foundry can default autoresume behavior to true when these conditions are met:

- `run_name` is set;
- `save_folder` is set;
- `save_overwrite` is false;
- `save_weights_only` is false.

You can still set explicitly:

```yaml
autoresume: true
```

Use explicit `autoresume: false` for a one-off smoke run that should not pick up old state. Use `save_overwrite: true` only when replacing checkpoint contents is intentional.

## Checkpoint-only modes

Training config includes two special modes:

```yaml
only_hf_checkpoint: false
only_composer_checkpoint: false
```

`only_composer_checkpoint: true` builds the trainer and saves a Composer checkpoint without fitting. `only_hf_checkpoint: true` requires exactly one `hf_checkpointer` callback. Export/conversion details after training belong to inference-conversion.

## HF checkpointer callback

A common callback shape is:

```yaml
callbacks:
  hf_checkpointer:
    save_folder: <save-folder>
    save_interval: 1000ba
```

Use this only when the target format, model compatibility, and credentials are clear. If `only_hf_checkpoint: true` is set, there must be exactly one HF checkpointer callback, otherwise the train command raises an error.

## Monitoring callbacks

Installed callback registry entries include:

```text
early_stopper, env_logging, eval_output_logging, fdiff_metrics, generate_callback,
global_lr_scaling, hf_checkpointer, kill_loss_spike, layer_freezing,
load_checkpoint, loss_perp_v_len, lr_monitor, mbmoe_tok_per_expert,
memory_monitor, memory_snapshot, mono_checkpoint_saver, nan_monitor,
oom_observer, optimizer_monitor, run_timeout, runtime_estimator,
scheduled_gc, speed_monitor, system_metrics_monitor
```

Common safe baseline:

```yaml
callbacks:
  speed_monitor:
    window_size: 10
  lr_monitor: {}
  memory_monitor: {}
  runtime_estimator: {}
```

Useful failure-protection additions:

```yaml
callbacks:
  nan_monitor: {}
  oom_observer: {}
  run_timeout:
    timeout: <duration>
  kill_loss_spike:
    window_size: 100
    loss_cap: <loss-threshold>
```

Check constructor arguments for uncommon callbacks before adding them. Some callbacks consume the full train config internally and may have stricter requirements.

## Callbacks with train config

Installed `callbacks_with_config` include:

```text
async_eval, curriculum_learning, dataset_swap
```

These receive a copy of the train config during construction. Be careful when combining them with modified eval loaders, data swaps, object-store paths, or async eval infrastructure. Detailed ICL task and Eval Gauntlet schemas belong to evaluation.

## Loggers

Installed logger registry entries include:

```text
in_memory_logger, inmemory, mlflow, mosaicml, tensorboard, wandb
```

Common patterns:

```yaml
loggers:
  wandb:
    project: <project-name>
    entity: <entity-name>

loggers:
  tensorboard:
    log_dir: <log-folder>
```

Logger destinations may need environment variables, credentials, writable local directories, or network access. Keep secrets outside YAML files intended for reuse.

## Optimizers

Installed optimizer names include:

```text
adalr_lion, clip_lion, decoupled_adamw, decoupled_lionw, no_op
```

Baseline AdamW:

```yaml
optimizer:
  name: decoupled_adamw
  lr: 6.0e-4
  betas: [0.9, 0.95]
  eps: 1.0e-8
  weight_decay: 0.0
```

LionW examples often use lower learning rates:

```yaml
optimizer:
  name: decoupled_lionw
  lr: 5.0e-7
  betas: [0.9, 0.95]
  weight_decay: 0.0
```

Parameter grouping and freezing can be expressed in the optimizer config:

```yaml
optimizer:
  name: decoupled_adamw
  lr: 1.0e-5
  weight_decay: 0.0
  disable_grad:
    - norm
    - bias
  param_groups:
    - param_str_match: norm
      lr: 1.0e-6
      weight_decay: 0.0
```

Do not add `params`; the builder extracts parameters from the model.

## Schedulers

Installed scheduler names include:

```text
constant_with_warmup, cosine_with_warmup, inv_sqrt_with_warmup, linear_decay_with_warmup
```

Pretraining often uses:

```yaml
scheduler:
  name: cosine_with_warmup
  t_warmup: 100ba
  alpha_f: 0.1
```

SFT examples often use a linear decay schedule:

```yaml
scheduler:
  name: linear_decay_with_warmup
  t_warmup: 50ba
  alpha_f: 0
```

Make sure `max_duration`, warmup duration, and scheduler units (`ba`, `ep`, or other Composer time strings) are compatible.

## FSDP, TP, and checkpoint planners

FSDP config can include load/save planners:

```yaml
fsdp_config:
  state_dict_type: sharded
  load_planner:
    <planner-name>: {}
  save_planner:
    <planner-name>: {}
```

Only one load planner and one save planner may be specified. Planner registry details are advanced package/API territory; keep ordinary training configs simple unless a checkpoint format explicitly requires a planner.

For `tp_config`, include both `strategy` and `tensor_parallel_degree`. TP is rejected for MoE models in the inspected logic.

## Object-store and credential checklist

Before setting remote `save_folder` or `load_path`, confirm:

- the path scheme is supported in the environment;
- credentials are available on every worker;
- write permissions are granted for save targets;
- read permissions are granted for load targets;
- rank-specific checkpoint naming matches full vs sharded state dict mode;
- remote uploads will not exceed budget or quota;
- local cache and temporary disk space are adequate.

If a checkpoint upload fails after training has produced local artifacts, do not immediately rerun a large job. First inspect whether the checkpoint exists locally and whether only credentials or remote path configuration failed.

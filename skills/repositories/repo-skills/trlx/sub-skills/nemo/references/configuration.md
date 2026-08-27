# NeMo configuration reference

This reference summarizes the NeMo YAML shape and the trlX-to-NeMo mapping used by the NeMo trainers and wrappers. It is distilled from the NeMo default loaders, the NeMo trainer/model source, and the example configs.

## Default config helpers

| Helper | Loads | Notes |
| --- | --- | --- |
| `default_nemo_1_3b_config()` | `megatron_1.3b.yaml` | Canonical smaller Megatron-style template |
| `default_nemo_2b_config()` | `megatron_2b.yaml` | SentencePiece-backed variant |
| `default_nemo_20b_config()` | `megatron_20b.yaml` | Larger TP=4 template |

A separate `megatron_65b.yaml` exists as a more aggressive scaling template. Treat it as reference-only unless the hardware and backend are explicitly prepared.

## YAML shape
Every NeMo config in this family uses the same top-level shape:

```yaml
name: <model_name>
restore_from_path: null
trainer:
  ...
exp_manager:
  ...
model:
  ...
```

### `trainer`
Common fields:
- `devices`
- `num_nodes`
- `accelerator`
- `precision`
- `logger`
- `enable_checkpointing`
- `replace_sampler_ddp`
- `max_epochs`
- `max_steps`
- `log_every_n_steps`
- `val_check_interval`
- `limit_val_batches`
- `limit_test_batches`
- `accumulate_grad_batches`
- `gradient_clip_val`
- `benchmark`

### `exp_manager`
Common fields:
- `explicit_log_dir`
- `exp_dir`
- `name`
- `create_tensorboard_logger`
- `create_wandb_logger`
- `wandb_logger_kwargs`
- `resume_if_exists`
- `resume_ignore_no_checkpoint`
- `create_checkpoint_callback`
- `checkpoint_callback_params`
- `log_step_timing`
- `step_timing_kwargs`

Checkpoint callback fields that matter most:
- `monitor`
- `save_top_k`
- `mode`
- `always_save_nemo`
- `save_nemo_on_train_end`
- `filename`
- `model_parallel_size`

### `model`
Common fields fall into these groups:

#### Parallel and runtime layout
- `micro_batch_size`
- `global_batch_size`
- `tensor_model_parallel_size`
- `pipeline_model_parallel_size`
- `virtual_pipeline_model_parallel_size` when present
- `resume_from_checkpoint`

#### Architecture
- `encoder_seq_length`
- `max_position_embeddings`
- `num_layers`
- `hidden_size`
- `ffn_hidden_size`
- `num_attention_heads`
- `init_method_std`
- `hidden_dropout`
- `attention_dropout`
- `ffn_dropout`
- `kv_channels`
- `apply_query_key_layer_scaling`
- `layernorm_epsilon`
- `make_vocab_size_divisible_by`
- `pre_process`
- `post_process`
- `persist_layer_norm`
- `gradient_as_bucket_view`
- `grad_div_ar_fusion`
- `gradient_accumulation_fusion`
- `megatron_amp_O2`
- `sequence_parallel`

#### Tokenizer
- `tokenizer.library`
- `tokenizer.type`
- `tokenizer.model`
- `tokenizer.vocab_file`
- `tokenizer.merge_file`
- `tokenizer.delimiter`
- `tokenizer.sentencepiece_legacy`

#### Precision and optimization
- `native_amp_init_scale`
- `native_amp_growth_interval`
- `hysteresis`
- `fp32_residual_connection`
- `fp16_lm_cross_entropy`
- `seed`
- `use_cpu_initialization`
- `onnx_safe`
- `apex_transformer_log_level`
- `sync_batch_comm`
- `optim.name`
- `optim.lr`
- `optim.weight_decay`
- `optim.betas`
- `optim.sched.name`
- `optim.sched.warmup_steps`
- `optim.sched.constant_steps`
- `optim.sched.min_lr`

#### Data
- `data.data_prefix`
- `data.index_mapping_dir`
- `data.data_impl`
- `data.splits_string`
- `data.seq_length`
- `data.skip_warmup`
- `data.num_workers`
- `data.dataloader_type`
- `data.reset_position_ids`
- `data.reset_attention_mask`
- `data.eod_mask_loss`
- optional `data.add_bos` / `data.add_eos` in some configs

## trlX trainer-kwargs mapping
The NeMo trainers are selected from the outer trlX config, but they consume NeMo-specific kwargs.

```python
train:
  trainer: NeMoPPOTrainer  # or NeMoILQLTrainer / NeMoSFTTrainer
  trainer_kwargs:
    megatron_cfg: <yaml_name_or_omegaconf>
    pretrained_model: <checkpoint_root_or_none>
```

### Mapping from outer trlX config into NeMo fields
| trlX field | NeMo field | Behavior |
| --- | --- | --- |
| `train.batch_size` | `model.global_batch_size` | scaled by data-parallel world size |
| `train.minibatch_size` | `model.micro_batch_size` | used when present, otherwise batch size |
| `train.seed` | `model.seed` | copied directly |
| `optimizer.name` / `optimizer.kwargs` | `model.optim` | optimizer chosen from the outer config |
| `scheduler.name` / `scheduler.kwargs` | `model.optim.sched` | scheduler chosen from the outer config |
| `train.epochs` / `train.total_steps` | `trainer.max_steps` | NeMo step budget is computed then capped |
| `train.eval_interval` | `trainer.val_check_interval` | PPO disables NeMo validation and reuses trlX eval flow |
| `model.num_layers_unfrozen` | model wrapper behavior | PPO wrapper-only knob |
| `config.to_dict()` | `megatron_cfg.trlx` | the full outer trlX config is injected for NeMo-side access |

### World-size math used by the trainers
```text
world_size = trainer.num_nodes * trainer.devices
model_parallel = tensor_model_parallel_size * pipeline_model_parallel_size
dp_world = world_size / model_parallel
global_batch_size = train.batch_size * dp_world
```

Keep `exp_manager.checkpoint_callback_params.model_parallel_size` consistent with `tensor_model_parallel_size * pipeline_model_parallel_size` so checkpoint shards and rank directories line up.

## Checkpoint and log directory rules
- `exp_manager.explicit_log_dir` controls the NeMo logging/checkpoint root.
- `exp_manager.create_checkpoint_callback` must be enabled if you want NeMo checkpoint files.
- `exp_manager.resume_if_exists` controls auto-resume from the log directory.
- `restore_from_path` is the NeMo-level knob for starting from an existing `.nemo` archive.
- `resume_from_checkpoint` is the lower-level per-rank checkpoint path used by the wrappers.
- Loading from a directory expects the directory layout, not a single filename unless the wrapper explicitly points to that file.

## Tokenizer path rules
- If the tokenizer library is `sentencepiece` and `pretrained_model` is set, the PPO trainer rewrites tokenizer file paths relative to that model root.
- For non-sentencepiece tokenizers, the wrapper uses the tokenizer already exposed by the wrapped model.
- LLaMA conversion outputs must keep tokenizer files and `megatron_<name>.yaml` together under the same checkpoint root.

## Quick validation checklist
Before using a NeMo config, check:
1. `trainer.devices * trainer.num_nodes` is divisible by `tensor_model_parallel_size * pipeline_model_parallel_size`.
2. `global_batch_size` is realistic for the available VRAM.
3. The tokenizer files exist at the checkpoint root you plan to pass in `pretrained_model`.
4. `resume_from_checkpoint` / `restore_from_path` points at the checkpoint root expected by the wrapper.
5. The config you chose matches the checkpoint rank layout and tensor-parallel degree.

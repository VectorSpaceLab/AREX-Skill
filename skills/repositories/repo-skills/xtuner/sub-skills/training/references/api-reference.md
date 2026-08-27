# XTuner Training API and CLI Reference

This reference captures the XTuner V1 SFT/pretraining/MLLM launch surface most useful to future agents. It focuses on operating choices; route data schemas to `data-preparation` and backend internals to `model-backends`.

## Entrypoint contract

Installed package launch form:

```bash
python -m xtuner.v1.train.cli.sft --help
torchrun --nproc-per-node <N> -m xtuner.v1.train.cli.sft [--config <config.py> | direct TrainingArguments]
```

Implementation behavior:

1. XTuner patches Hugging Face module cache for the current process.
2. If direct `TrainingArguments` are present and `--config` is also present, it raises `ValueError: Cannot specify both \`config\` and \`arguments\`.`
3. If direct arguments are present, it builds a `TrainerConfig` with `arguments.to_trainer_config()`.
4. If direct arguments are absent, `--config` is required and XTuner loads `Config.fromfile(config)["trainer"]`.
5. It creates `Trainer.from_config(trainer_cfg)` and runs `trainer.fit()`.
6. If distributed training was initialized, it destroys the process group at exit.

## Direct `TrainingArguments` fields

Direct mode exposes these CLI groups. Use `python -m xtuner.v1.train.cli.sft --help` in the target environment to confirm any version-specific changes.

| Group | Important flags | Meaning and constraints |
|---|---|---|
| config-path | `--config` | Python config file mode. Mutually exclusive with every direct argument below. |
| model | `--load-from` | Load checkpoint/model path. In direct mode, if `--tokenizer-path` is omitted this should be a Hugging Face model path or id that `AutoConfig.from_pretrained(..., trust_remote_code=True)` accepts. |
| model | `--model-cfg` | Model config path or built-in alias. A Python config path must expose `model`; aliases are version-limited. |
| model | `--chat-template` | Required in direct mode. Verified choices include `internlm2`, `qwen3`, `gpt-oss`, `deepseek-v3`, `glm5.2`. |
| model | `--tokenize-fn` | `openai` or `ftdp`; default `openai`. Detailed tokenization behavior belongs to `data-preparation`. |
| model | `--tokenizer-path` | Explicit tokenizer path. Usually same as `--load-from`; useful when `--load-from` is not an HF snapshot. |
| dataset | `--dataset` | Dataset config `.py`, JSONL file, directory of JSONLs, or glob. Non-`.py` inputs are expanded to `.jsonl` files. |
| dataset | `--dataset-config-list` | Nested dataloader dataset config input exposed by the parser; for complex lists, prefer Python config mode. |
| dataset | `--collator` | Choices include `sft_llm_collator`, `intern_s1_vl_sft_collator`, `qwen3_vl_sft_collator`, `fake_collator`. |
| dataset | `--pack-to-max-length` / `--no-pack-to-max-length` | Enable/disable packing to max length. If disabled, `torch_compile` may need to be disabled in model/FSDP config. |
| dataset | `--pack-level` | Choices include `soft`, `none`, `__legacy`, `hard`, `mllm_hybrid`, `preset`. `preset` requires pack/sampler config paths. |
| dataset | `--pack-max-length`, `--pack-chunk-size`, `--pack-workers` | Packing shape/performance controls. |
| dataset | `--global-pack`, `--group-by-length`, `--sampler-type` | Sampling/packing balance controls. |
| dataset | `--pack-config-path`, `--sampler-config-path` | Required for preset packing/sampling. |
| dataset | `--cache-dir`, `--cache-tag` | Dataset preprocessing cache. Detailed cache correctness belongs to `data-preparation`. |
| dataset | `--max-length` | Max single sequence length for tokenization; default direct-mode value is 4096. |
| optimizer | `--lr`, `--optim` | Learning rate and optimizer type. `--optim` choices include `AdamW`, `Muon`; default `AdamW`. |
| lr-scheduler | `--scheduler-type`, `--warmup-ratio`, `--lr-min` | Scheduler choices include `cosine`, `linear`, `constant`; default direct mode is cosine with warmup ratio 0.03. |
| loss | `--loss-config.ignore-idx`, `--loss-config.mode`, `--loss-config.chunk-size`, `--loss-config.loss-reduction` | Cross-entropy loss controls. `chunk` mode is useful for memory reduction; `liger` depends on optional backend availability. |
| training | `--total-step`, `--epoch-num` | Only one may be set. If neither is set, direct conversion defaults to one epoch. |
| training | `--work-dir` | Work directory; direct default is `work_dir`. |
| training | `--global-batch-size` | Global training batch size. If omitted, `Trainer` defaults to data-parallel mesh size times intra-layer micro-batch. |
| checkpoint | `--async-checkpoint` | Enables async DCP checkpoint saving. |
| checkpoint | `--load-model`, `--load-optimizer-states`, `--load-optimizer-args`, `--load-dataset`, `--load-scheduler` | Exposed by help. In the inspected version, direct conversion does not build an explicit `LoadCheckpointConfig`; use Python config mode for reliable resume policy. |
| fsdp-parallel | `--fsdp-config.tp-size`, `--fsdp-config.ep-size`, `--fsdp-config.hsdp-sharding-size` | Tensor/expert/hybrid sharding sizes. Must be compatible with world size. HSDP currently requires `ep_size == 1`. |
| fsdp-parallel | `--fsdp-config.cpu-offload` | CPU offload for memory pressure. Slower and version/model sensitive; validate on target PyTorch/model combination. |
| fsdp-parallel | `--fsdp-config.recompute-ratio`, `--fsdp-config.vision-recompute-ratio` | Activation checkpoint/recompute controls for LLM/vision modules. |
| fsdp-parallel | `--fsdp-config.param-dtype`, `--fsdp-config.reduce-dtype` | Dtype controls; defaults are bfloat16. |
| fsdp-parallel | `--fsdp-config.torch-compile` / `--fsdp-config.no-torch-compile` | Model compilation toggle. Disable when debugging dynamic shapes or when `pack_to_max_length=False` conflicts with compile. |
| fsdp-parallel | `--float8-config.scaling-granularity-gemm`, `--float8-config.scaling-granularity-grouped-gemm` | FP8 knobs. Route backend feasibility and kernels to `model-backends`. |

## `TrainingArguments.to_trainer_config()` mapping

Direct arguments are transformed approximately as follows:

| Direct input | TrainerConfig result |
|---|---|
| `--dataset` JSONL/file/dir/glob | Builds a list of `{"dataset": DatasetConfig(...), "tokenize_fn": ...}` entries. Directories and globs are filtered to `.jsonl`. |
| `--tokenize-fn openai` | Uses `OpenaiTokenizeFunctionConfig(chat_template=<chat_template>, max_length=<max_length>)`. |
| `--tokenize-fn ftdp` | Uses `FTDPTokenizeFnConfig(chat_template=<chat_template>, max_length=<max_length>)`. |
| `--optim AdamW` | Uses `AdamWConfig(lr=<lr>, foreach=False)`. |
| `--optim Muon` | Uses `MuonConfig(lr=<lr>)`. |
| scheduler flags | Build `LRConfig(lr_type=<scheduler_type>, warmup_ratio=<warmup_ratio>, lr_min=<lr_min>)`. |
| `--model-cfg <file>.py` | Loads config and requires top-level `model`. |
| `--model-cfg <alias>` | Resolves through XTuner's model alias registry. |
| no `--model-cfg`, with `--load-from` | Requires `--load-from` to parse as a Hugging Face model path and uses `get_model_config_from_hf`. |
| `--float8-config ...` | Sets `model_cfg.float8_cfg`. Backend validation belongs to `model-backends`. |
| both `--total-step` and `--epoch-num` | Raises `ValueError: Only one of \`total_step\` or \`epoch_num\` should be set.` |
| neither `--total-step` nor `--epoch-num` | Defaults `epoch_num` to 1. |

## `TrainerConfig` fields for config mode

Config mode is the recommended path for advanced training. The verified `TrainerConfig` field surface includes:

| Field | Purpose |
|---|---|
| `model_cfg` | XTuner model config object. Required. |
| `load_from` | HF model path, model weights, or supported checkpoint source. Required for normal fine-tuning; omit for true scratch/pretraining. |
| `tokenizer_path` | Tokenizer path. If omitted, Trainer uses a toy UTF-8 byte tokenizer, which is only appropriate for tiny smoke/scratch cases. |
| `dataset_cfg` | Deprecated compatibility field. Prefer `dataloader_cfg.dataset_config_list`. |
| `dataloader_cfg` | `DataloaderConfig` or other base dataloader config. Required. |
| `optim_cfg` | `AdamWConfig`, `MuonConfig`, or compatible optimizer config. Required. |
| `lr_cfg` | `LRConfig`. Required. |
| `loss_cfg` | `CELossConfig`; default mode may differ by context. `chunk` can reduce memory. |
| `fsdp_cfg` | `FSDPConfig` or `None`. `None` is normalized to default `FSDPConfig`. |
| `global_batch_size` | Global batch size. If `None`, computed from data-parallel mesh and micro-batch. |
| `work_dir` | Experiment output root. `None` resolves to current directory. |
| `log_dir` | Override log directory; otherwise under the experiment directory. |
| `sp_size` | Sequence-parallel size. |
| `total_step`, `total_epoch` | Exactly one required after dataloader resolution. |
| `auto_resume` | Use latest checkpoint recorded in `.xtuner` when present. |
| `load_checkpoint_cfg` | `LoadCheckpointConfig` controlling explicit checkpoint path and restored states. |
| `strict_load` | Strict model load behavior. |
| `checkpoint_interval`, `checkpoint_maxkeep` | DCP checkpoint cadence and retention. `-1` means save at the end; `None` disables. |
| `async_hf_export`, `hf_interval`, `hf_max_keep` | HF-format save/export controls. Valid only when model can save in HF format. |
| `skip_checkpoint_validation` | Suggested for very large FSDP sizes when checkpoint validation is expensive. |
| `patch_for_dcp_finish` | Torch-version-specific DCP finish patch. |
| `async_checkpoint` | Asynchronous DCP checkpoint saving. |
| `snapshot_interval` | Snapshot checkpoint cadence. |
| `check_health_interval` | Periodic health checks. |
| `exp_tracker` | `jsonl` or `tensorboard`. Direct SFT uses `jsonl` through `TrainerConfig` defaults. |
| `profile_step`, `profile_time`, `profile_memory` | Profiling controls. |
| `intra_layer_micro_batch` | Micro-batch factor used in global batch calculation. |
| `seed`, `dist_backend`, `debug`, `debug_skip_save` | Runtime/debug controls. |
| `prober_list`, `internal_metrics_cfg`, `hooks_config` | Advanced hooks and internal metrics. |

## Checkpoint and resume config classes

`LoadCheckpointConfig` fields:

| Field | Meaning |
|---|---|
| `checkpoint_path` | Explicit XTuner DCP checkpoint directory. Complete checkpoints include `weights/`, dataloader state, scheduler state, and `train_state.json`. |
| `load_optimizer_states` | Restore optimizer states. Disable only for partial fine-tune restart, not exact resume. |
| `load_optimizer_args` | Restore optimizer hyperparameters from checkpoint. |
| `load_dataset` | Restore dataloader position and consumed token/time offsets. |
| `load_scheduler` | Restore LR scheduler state. |
| `offload_optimizer_first_step` | Temporarily offload optimizer states to CPU before the first resumed optimizer step to reduce resume memory pressure. |

`ResumeConfig` exists but is deprecated in favor of `auto_resume` and `load_checkpoint_cfg`.

## FSDPConfig fields

| Field | Default | Operating note |
|---|---:|---|
| `tp_size` | 1 | Tensor parallel size. World size must be divisible by the combined mesh dimensions used by the target model. |
| `ep_size` | 1 | Expert parallel size. MoE-specific feasibility belongs to `model-backends`. |
| `reshard_after_forward` | True | Memory saving vs communication trade-off. |
| `recompute_ratio` | 1.0 | LLM activation checkpointing ratio; lower to reduce recompute cost, raise for memory pressure. |
| `vision_recompute_ratio` | 1.0 | Vision-module checkpointing ratio for MLLM. |
| `checkpoint_preserve_rng_state` | True | Preserve RNG in checkpointed layers. |
| `mtp_checkpoint_use_reentrant` | True | MTP checkpoint implementation toggle. |
| `cpu_offload` | False | Try for OOM only after reducing batch/length/recompute. Can be slower and version-sensitive. |
| `param_dtype`, `reduce_dtype` | bfloat16 | Serialized/deserialized from strings such as `torch.bfloat16`, `bfloat16`, `float16`, `float32`. |
| `fp32_lm_head` | False | Use fp32 LM head. |
| `torch_compile` | True | Disable for debugging compile/recompile or dynamic-shape conflicts. |
| `mesh_prefix` | `default` | Device mesh prefix. |
| `requires_grad` | True | Freeze/training toggle at FSDP config layer. |
| `hsdp_sharding_size` | None | HSDP sharding size. HSDP currently asserts `ep_size == 1`. |

## Optimizer, LR, and loss configs

| Config | Important fields |
|---|---|
| `OptimConfig` | `lr`, `max_grad_norm`, `skip_grad_norm_threshold`. |
| `AdamWConfig` | `lr`, `max_grad_norm`, `weight_decay`, `betas`, `eps`, `foreach`, `swap_optimizer`. Direct mode constructs AdamW with `foreach=False`. |
| `MuonConfig` | Selected by direct `--optim Muon`; use only when the installed package supports the intended model/backend. |
| `LRConfig` | `lr_type` (`cosine`, `linear`, `constant`), `warmup_ratio`, `lr_min`. |
| `CELossConfig` | `ignore_idx`, `mode` (`eager`, `chunk`, `liger`), `chunk_size`, `loss_reduction` (`token`, `sample`, `square`). `chunk` is the safe memory-reduction default in many examples. |

## Log field reference

XTuner V1 training step lines may include:

| Field | Interpretation |
|---|---|
| `Epoch`, `Step current/total` | Progress. Missing or stalled step increments indicate startup/data/distributed failure. |
| `data_time` | Time waiting for data. High values imply data loading, cache, media, storage, or packing bottlenecks. |
| `lr` | Current scheduler LR. Check warmup/decay shape. |
| `time` | Model + optimizer step time. High values with normal `data_time` imply compute/communication/compile/pack imbalance. |
| `text_tokens`, `seqlen_tokens`, `img_tokens` | Per-rank token workload. Zeros or extreme imbalance can explain throughput drops. |
| `total_loss`, `local_loss`, `reduced_llm_loss`, custom loss keys | Loss signals. Non-finite or explosive loss needs LR/data/loss investigation. |
| `grad_norm` | Gradient health and clipping signal. Spikes can indicate instability or bad batches. |
| `max_memory`, `reserved_memory` | Peak allocated and reserved memory. Reserved much higher than allocated can indicate fragmentation. |
| `tgs`, `seqlen_tgs`, `exp_tgs` | Tokens/GPU/second metrics. First step is usually a cold-start outlier. |
| `eta` | Estimated remaining time. |

Use `scripts/summarize_xtuner_log.py` for quick aggregation and warning detection.

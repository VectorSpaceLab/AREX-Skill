# AReaL Experiment Config API

This reference distills the AReaL config objects needed to plan GRPO, PPO, SFT, DPO,
and reward-model (RW) experiments. It is written for safe pre-launch planning: validate
configs and overrides first, then launch with the family-specific command template in
`experiment-workflows.md`.

## Family map

| Family | Trainer | Config class | Required high-level sections | Dataset type |
|---|---|---|---|---|
| GRPO | `PPOTrainer` | `GRPOConfig` | `rollout`, `gconfig`, `actor`, optional `ref` | `rl` |
| PPO | `PPOTrainer` | `PPOConfig` | `rollout`, `gconfig`, `actor`, `critic`, optional `ref` | `rl` |
| SFT | `SFTTrainer` | `SFTConfig` | `actor` | `sft` |
| DPO | `DPOTrainer` | `DPOConfig` | `actor`, `ref` | `dpo` |
| RW | `RWTrainer` | `RWConfig` | `actor` with `is_critic: true` | `rw` |

`GRPOConfig` is a compatibility subclass of `PPOConfig`; the distinction is whether the
experiment uses a critic. GRPO omits `critic`, while PPO provides a `critic` section and
uses value-function advantages.

## Common experiment fields

All families inherit `BaseExperimentConfig`:

| Field | Planning notes |
|---|---|
| `experiment_name` | Required. Keep path-safe; AReaL rejects `/` and expects no `_`. |
| `trial_name` | Required. Keep path-safe; AReaL rejects `/` and expects no `-`. |
| `cluster.n_nodes`, `cluster.n_gpus_per_node` | Physical GPU budget used by local/Ray/Slurm schedulers. In separation mode, the colocation-aware sum of per-engine backends should equal `n_nodes * n_gpus_per_node`. |
| `cluster.fileroot` | Shared root for logs/checkpoints. For multi-node runs, use storage visible to every worker. |
| `cluster.name_resolve` | Distributed name store. The common NFS mode uses `type: nfs` and an `nfs_record_root` under shared storage. |
| `scheduler.type` | Recommended direct-script choices are `local`, `ray`, or `slurm`. YAMLs may leave this `null` and require a CLI override before launch. |
| `total_train_epochs` | Must be positive. `total_train_steps` and `total_train_n_seqs` can bound a run for smoke or benchmarking. |
| `tokenizer_path` | Usually `${actor.path}`. VLM scripts also pass this as processor path. |
| `train_dataset`, `valid_dataset` | Use matching `type`; common fields are `path`, `split`, `batch_size`, `shuffle`, `pin_memory`, `num_workers`, `drop_last`, `max_length`, `dataset_kwargs`. |
| `saver`, `recover`, `evaluator` | Timer-like configs with `freq_epochs`, `freq_steps`, and `freq_secs`. |
| `stats_logger` | Owns W&B/SwanLab/TensorBoard/Trackio logging. `wandb.mode: disabled` is the safest default when credentials are unknown. |
| `perf_tracer`, `memory_profiler` | Optional. Enable only when the user wants detailed traces/snapshots. |

`allocation_mode` is deprecated for user experiment configs. Prefer separate per-engine
`backend` fields such as `rollout.backend`, `actor.backend`, `critic.backend`, and
`ref.backend`.

## Backend string and scheduling fields

Every train or inference engine requires an explicit backend prefix:

| Example | Meaning for planning |
|---|---|
| `fsdp:d4` | FSDP actor/critic/ref using data parallel size 4. |
| `fsdp:d4p1t1` | FSDP with data/pipeline/tensor components explicitly set. |
| `megatron:d4t2p1` | Megatron training with DP 4, TP 2, PP 1. |
| `archon:d8` | Archon training across 8 ranks. |
| `sglang:d4p1t1` | SGLang rollout backend with DP 4, PP 1, TP 1. |
| `vllm:d2t4` | vLLM rollout backend with DP 2 and TP 4. |

Do not use legacy `+` combined allocation strings inside a single per-engine `backend`
field. Each role gets its own backend string. Use `scheduling_strategy` for sharing:

```yaml
rollout:
  backend: sglang:d2
  scheduling_strategy:
    type: colocation
    target: actor

actor:
  backend: fsdp:d2
```

`SchedulingStrategy.type` is `separation` or `colocation`. `target` names the role to
share with. `fork: true` means a separate process is spawned on the target's GPUs.

`scheduling_spec` must contain one or two `SchedulingSpec` objects. One spec is used for
both worker and engine. Two specs mean first worker, then engine. Common fields are
`task_type`, `port_count`, `gpu`, `cpu`, `mem`, `cmd`, `env_vars`, plus Slurm-only image
and container options. CLI overrides can target list items, e.g.
`+actor.scheduling_spec.0.env_vars.MY_ENV=value`.

## Shared train-engine fields

`TrainEngineConfig` backs `actor`, `critic`, `ref`, DPO actors, SFT actors, and RW
actors.

| Field | Important constraints |
|---|---|
| `backend` | Required; must start with `fsdp:`, `megatron:`, or `archon:` for training roles. |
| `path` | Hugging Face model id or local checkpoint. If `init_from_scratch: false`, leave no ambiguity about this path. |
| `attn_impl` | Built-in transformer attention backend or a Hugging Face kernels repo id. |
| `use_kernels` | Enables Hugging Face kernelization after model creation. |
| `init_from_scratch` | Incompatible with `fsdp.memory_efficient_load: true`. |
| `disable_dropout` | Strongly recommended for DPO/reference-style log-prob computations. |
| `gradient_checkpointing` | Saves memory at extra compute cost. |
| `dtype` | `float32`, `bfloat16`, or `float16` (aliases such as `bf16` are canonicalized). |
| `optimizer_dtype` | `float32` or `bfloat16`; FSDP-only storage/optimizer-state dtype. |
| `optimizer` | `null` means frozen/no training. References usually set this to `null`. |
| `logprobs_chunk_size` | Must be positive; default is `1024`. |
| `mb_spec` | Micro-batch split controls. `max_tokens_per_mb` is the most practical safety knob. |
| `weight_update_mode` | `xccl`, `disk`, or `awex`; `awex` is only for Megatron actor + SGLang rollout colocation. |
| `offload` | Per-role offload flag. Any colocation/offload path also requires top-level `enable_offload: true`. |
| `use_lora` | Supported on FSDP actors. Keep actor and rollout LoRA settings aligned. |
| `_version` | `v1` or `v2`. For GRPO/PPO, `actor._version` and `rollout._version` must match. Recovery is not supported with v2 train controllers. |

### `MicroBatchSpec`

| Field | Notes |
|---|---|
| `n_mbs` | Number of micro-batches, or minimum number when token limit is set. |
| `granularity` | Adjacent sequence grouping. DPO requires `2` because chosen/rejected responses are paired. |
| `max_tokens_per_mb` | Caps tokens per forward pass; lower this for OOM triage. |
| `n_mbs_divisor` | Forces final number of micro-batches to divide by this value. |
| `packing_algorithm` | `ffd` default; `kk` is available for stronger balance on variable sequence lengths. |

## GRPO/PPO-specific config

`PPOConfig` / `GRPOConfig` adds:

| Section | Notes |
|---|---|
| `gconfig` | `GenerationHyperparameters`: `n_samples`, `max_new_tokens`, `max_tokens`, `temperature`, `top_p`, stop settings, beam search, and `lora_name`. |
| `eval_gconfig` | Optional evaluation generation config; if omitted, copies `gconfig`. |
| `rollout` | `InferenceEngineConfig` for SGLang/vLLM rollout workers. |
| `actor` | `PPOActorConfig` for policy training. |
| `critic` | `PPOCriticConfig`; present for PPO, omitted for GRPO. |
| `ref` | Optional frozen reference for KL penalty; normally `optimizer: null` and colocated with actor. |
| `dynamic_bs` | Allows dynamic batch sizing in rollout collection. |

### `PPOActorConfig` knobs

| Knob | Use |
|---|---|
| `ppo_n_minibatches`, `eps_clip`, `eps_clip_higher`, `c_clip` | PPO/GRPO update and clipping. `eps_clip_higher` enables asymmetric clipping. |
| `reward_norm`, `adv_norm` | `NormConfig` for rewards and advantages. Group reward normalization should use `group_size >= 2`. |
| `reward_scaling`, `reward_bias`, `reward_clip` | Task reward shaping. |
| `kl_ctl`, `kl_estimator` | KL penalty against `ref`, with estimators `k1`, `k2`, or `k3`. |
| `recompute_logprob`, `use_decoupled_loss` | Off-policy/async training controls. `use_decoupled_loss` implies proximal log-prob handling. |
| `rejection_sampling` | Staleness filtering; replaces removed `behave_imp_weight_*` keys. |
| `importance_sampling_level` | `token` for PPO/GRPO, `sequence` for GSPO-style ratios. |
| `prox_logp_method` | `recompute`, `loglinear`, `metrics`, or `reuse_train_logp`; `reuse_train_logp` requires one minibatch. |
| `use_sapo_loss` | SAPO surrogate; incompatible with `use_decoupled_loss: true`. |
| `use_cispo_loss` | CISPO surrogate; requires token-level importance sampling and positive `eps_clip_higher`. |

### `NormConfig`

`mean_level` and `std_level` are `batch`, `group`, or `null`. `mean_leave1out` enables
RLOO-style baselines. `std_unbiased` defaults to `true`; `eps` defaults to `1e-5`.
Group-level normalization uses rollout group metadata when available and falls back to
fixed `group_size`.

### `RejectionSamplingConfig`

Fields: `level` (`token` or `sequence`), `action` (`mask` or `clamp`), `metric`
(`ratio`, `kl_k1`, `kl_k2`, `kl_k3`; some recipe docs also use `binary_kl` for KPop),
`agg` (`sum`, `mean`, `max`), `upper`, and optional `lower`.

Always run the bundled validator for KPop/binary-KL configs. Some AReaL builds document
`binary_kl` recipes while their dataclass validation still rejects the metric; if so,
do not launch until the package version or config is reconciled.

Validation rules:
- `ratio.upper` must be greater than `1.0`.
- `ratio.lower`, when set, must be positive.
- `kl_k2`/`kl_k3.upper` must be positive.
- `action: clamp` supports only `metric: ratio` and defaults `lower` to `0.0`.
- `agg` is ignored for token-level filtering.

Migration from removed keys:

```yaml
# old: behave_imp_weight_mode: disabled
rejection_sampling: null

# old: token_mask with cap X
rejection_sampling:
  level: token
  action: mask
  metric: ratio
  upper: X

# old: token_truncate with cap X
rejection_sampling:
  level: token
  action: clamp
  metric: ratio
  upper: X
```

## SFT-specific config

`SFTConfig` is `BaseExperimentConfig` plus a single `actor: TrainEngineConfig`. It has
no rollout, ref, or critic requirement. Use `train_dataset.type: sft`. For VLM SFT,
load a processor as well as a tokenizer in the entrypoint and pass both into dataset
loading.

## DPO-specific config

`DPOConfig` has `actor: DPOEngineConfig` and `ref: DPOEngineConfig`.

Required/recommended rules:
- `actor.is_critic` must be `false`.
- `actor.disable_dropout: true` is required for stable log-prob comparisons.
- `actor.mb_spec.granularity: 2` keeps chosen/rejected pairs together.
- `actor.beta` controls the KL penalty. Typical DPO ranges are small, e.g. `0.05`–`0.5`.
- `actor.loss_type` is `sigmoid` or `ipo`.
- `ref.optimizer: null`; `ref.path` usually matches actor path or an SFT checkpoint.
- Colocate `ref` with `actor` unless the user deliberately allocates separate GPUs.

DPO metrics use a `dpo/` prefix and include loss, chosen/rejected implicit reward,
reward accuracy, and reward margin.

## RW-specific config

`RWConfig` uses a single `actor: TrainEngineConfig` as a reward model. It validates that
`actor.is_critic: true`. Use `train_dataset.type: rw` and preference-pair data.

## Rollout/inference config fields

`InferenceEngineConfig` backs GRPO/PPO rollout roles and rollout teachers.

| Field | Notes |
|---|---|
| `backend` | Required; `sglang:` or `vllm:` for rollout. |
| `max_concurrent_rollouts`, `queue_size`, `consumer_batch_size` | Async rollout throughput and queue controls. |
| `max_head_offpolicyness` | `0` makes RL synchronous; values such as `2`–`8` allow async overlap. |
| `enable_rollout_tracing`, `dump_to_file` | Debug and trajectory-dump controls. Use only when storage overhead is acceptable. |
| `check_trajectory_format` | Debug custom workflow output; leave `false` during full RL training. |
| `use_lora`, `lora_name` | Must agree with actor LoRA settings; usually derive adapter name from `gconfig.lora_name`. |
| `return_routed_experts` | SGLang-only MoE diagnostic. Disable for vLLM. |
| `_version` | Match actor `_version` in GRPO/PPO. |

Common SGLang fields: `model_path`, `dtype`, `context_length`, `mem_fraction_static`,
`max_running_requests`, `attention_backend`, `enable_multimodal`, `enable_lora`,
`max_lora_rank`, `max_loaded_loras`.

Common vLLM fields: `model`, `dtype`, `max_model_len`, `gpu_memory_utilization`,
`disable_sliding_window`, `enforce_eager`, `enable_lora`, `max_lora_rank`, `max_loras`.

## Saver, recovery, logging

| Config | Key fields | Notes |
|---|---|---|
| `SaverConfig` | `mode`, `freq_epochs`, `freq_steps`, `freq_secs` | Saves Hugging Face-format checkpoints. `mode: async` is Archon-only; other engines fall back to sync. |
| `RecoverConfig` | `mode`, `retries`, `no_save_optim`, `no_load_optim`, timer fields | `mode: on` or `auto` resumes from recover metadata when present. Use the same model/backend/parallelism layout. Not supported with v2 train controllers. |
| `EvaluatorConfig` | timer fields, `eval_before_train` | Controls periodic validation. |
| `StatsLoggerConfig` | `wandb`, `swanlab`, `tensorboard`, `trackio` | Rank-0 logging. Safest credential-free mode is all disabled unless the user requests a tracker. |
| `PerfTracerConfig` | `enabled`, `save_interval`, `profile_steps`, optional `session_tracer` | Useful for perf debugging; avoid enabling by default. |

Log and checkpoint path patterns are derived from `fileroot`, `experiment_name`, and
`trial_name`:

```text
logs:        <fileroot>/logs/<user>/<experiment_name>/<trial_name>
checkpoints: <fileroot>/checkpoints/<user>/<experiment_name>/<trial_name>
recover:     <checkpoints>/<model-name>/recover_checkpoint plus recover_info metadata
```

## Hydra-style overrides

AReaL training entrypoints use `load_expr_config(argv, ConfigClass)` and Hydra-style
CLI overrides.

Rules:
- `--config <yaml>` is required by the config loader.
- Override existing keys with dotted paths: `actor.path=Qwen/Qwen3-1.7B`.
- Add keys not present in YAML with `+`: `+sglang.attention_backend=triton`.
- Use `null` for YAML null: `valid_dataset=null` or `actor.adv_norm.std_level=null`.
- List/tuple elements use zero-based numeric segments: `+actor.scheduling_spec.0.env_vars.KEY=value`.
- Quote values in the shell when they contain spaces, commas, brackets, or characters the shell may expand.

Common override bundles:

```bash
# Local smoke launch plan
scheduler.type=local stats_logger.wandb.mode=disabled

# Multi-node Ray/Slurm plan
scheduler.type=ray cluster.n_nodes=<N> cluster.n_gpus_per_node=<G> cluster.fileroot=<shared-root>

# Async RL behavior
rollout.max_head_offpolicyness=2 actor.use_decoupled_loss=true actor.recompute_logprob=true

# Equivalent to the old token-mask importance-weight cap 5.0
+actor.rejection_sampling.level=token +actor.rejection_sampling.action=mask +actor.rejection_sampling.metric=ratio +actor.rejection_sampling.upper=5.0
```

## Safe validator

Before launch, run the bundled helper:

```bash
python3 scripts/validate_experiment_config.py --kind <grpo|ppo|sft|dpo|rw> --config <yaml> [hydra overrides...]
```

The helper imports AReaL, merges YAML with overrides, instantiates the selected config
class, checks high-value family invariants, prints allocation/logging/recovery summaries,
and exits without starting workers, services, downloads, or training.

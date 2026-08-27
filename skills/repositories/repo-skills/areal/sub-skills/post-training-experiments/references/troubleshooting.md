# Experiment Troubleshooting

Use this guide after `scripts/validate_experiment_config.py` reports an error/warning,
or when a planned AReaL experiment fails before meaningful training begins. If the
problem moves into distributed engine internals, route to `../distributed-engines-backends/`.
If it is about dataset/reward/workflow implementation, route to
`../custom-data-rewards-workflows/`. If it is about v2 service lifecycle, sessions,
routers, or gateways, route to `../services-cli-operations/`.

## Config loader and Hydra override issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `--config` missing or config file not found | AReaL entrypoints require a YAML path. | Pass `--config <yaml>` before Hydra overrides. |
| Override ignored or rejected | The key is not already present in YAML and was added without `+`. | Use `+new.path=value` for keys absent from the original YAML. |
| Shell expands brackets/commas/spaces | Value was not quoted for the user's shell. | Quote complex values, e.g. `actor.target_modules='[all-linear]'`. |
| `valid_dataset` should be disabled | The optional section is still present. | Use `valid_dataset=null` if the trainer/workflow allows no validation set. |
| Legacy `allocation_mode` confusion | New configs use per-engine `backend` fields. | Move to `rollout.backend`, `actor.backend`, `critic.backend`, `ref.backend`. |
| A list/tuple env override fails | Numeric index missing in dotted path. | Use zero-based segments, e.g. `+actor.scheduling_spec.0.env_vars.KEY=value`. |

## Family mismatch issues

| Symptom | Likely cause | Fix |
|---|---|---|
| GRPO config launches as PPO or needs a critic | Family was selected as PPO but no `critic` is present. | Use `--kind grpo` in the validator, or add a `critic` section for PPO. |
| PPO run has no value-function learning | Missing `critic` section. | Add `critic` with backend, path, optimizer, and micro-batch settings. |
| SFT config mentions rollout/ref/critic | Mixed RL and SFT config fragments. | Remove rollout/ref/critic for SFT; SFT uses only `actor`. |
| DPO trainer complains about critic mode | `actor.is_critic: true` was copied from RW. | Set DPO `actor.is_critic=false` or remove the field. |
| RW config validation fails | `RWConfig` requires `actor.is_critic: true`. | Set `actor.is_critic=true` and use `train_dataset.type=rw`. |
| DPO pairs split incorrectly | `actor.mb_spec.granularity` is not `2`. | Set `actor.mb_spec.granularity=2` so chosen/rejected sequences stay paired. |
| Dataset loader returns wrong sample shape | `train_dataset.type` does not match the family. | Use `rl`, `sft`, `dpo`, or `rw` as appropriate; route custom schema work to `../custom-data-rewards-workflows/`. |

## PPO-family algorithm and normalization issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `Found removed config key(s) behave_imp_weight_*` | Old staleness-filter keys were removed. | Replace with `actor.rejection_sampling`; see `config-api.md` migration table. |
| Warning: `use_decoupled_loss=True with rejection_sampling=None` | Async/off-policy loss is enabled but no stale-sample filter is active. | Add token mask config: `level=token`, `action=mask`, `metric=ratio`, `upper=5.0`, or intentionally keep it disabled. |
| Warning: singleton group centering erases reward | `reward_norm.mean_level=group` and `group_size=1`. | Disable mean centering with `mean_level=null`, or use `group_size >= 2`. |
| KPop `binary_kl` config rejected | Recipe docs and package validation are inconsistent in this build. | Do not launch; either use a supported rejection-sampling metric or confirm the package version/patch that accepts `binary_kl`. |
| `gconfig.reward_normalization` conflicts with `actor.reward_norm` | Rollout-time and training-time reward normalization both active. | Enable only one normalization layer. |
| SAPO validation fails | `actor.use_sapo_loss=true` with `actor.use_decoupled_loss=true`. | Disable decoupled loss for SAPO. |
| CISPO validation fails | Missing positive `eps_clip_higher` or non-token importance sampling. | Set positive `actor.eps_clip_higher` and `actor.importance_sampling_level=token`. |
| `prox_logp_method=reuse_train_logp` changes minibatches | Reuse mode requires one minibatch. | Set `actor.ppo_n_minibatches=1` or use a recompute method. |
| Reward/advantage stats look wrong | `adv_norm`/`reward_norm` level not intended for task. | Check `mean_level`, `std_level`, `mean_leave1out`, and `group_size`. |

## Backend allocation and scheduler planning issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Backend parse error | Missing explicit prefix or using a combined legacy string. | Use one role per field, e.g. `actor.backend=fsdp:d4`, `rollout.backend=sglang:d4`. |
| GPU budget mismatch | Backend world sizes do not match `cluster.n_nodes * cluster.n_gpus_per_node`. | Adjust backend strings or cluster fields. In colocation, count a shared group once through the target role. |
| Ray/Slurm workers cannot see files | `cluster.fileroot` or name-resolution root is not shared. | Put `cluster.fileroot` and `cluster.name_resolve.nfs_record_root` on shared storage. |
| `enable_offload must be True` | Colocation scheduling or train-engine offload is active. | Set top-level `enable_offload=true`, or remove colocation/offload. |
| Colocation rejects `xccl` | Actor/rollout colocation requires disk/AWEX handoff. | Set `actor.weight_update_mode=disk`, or `awex` only for Megatron actor + SGLang rollout. |
| `weight_update_mode='awex' requires Megatron actor` | AWEX selected with FSDP/Archon actor. | Use `actor.backend=megatron:...` or choose `disk`/`xccl` as appropriate. |
| `weight_update_mode='awex' requires SGLang rollout` | AWEX selected with vLLM rollout. | Switch rollout to SGLang or do not use AWEX. |
| `actor._version` and `rollout._version` mismatch | v1/v2 controller versions differ. | Set both to `v1` or both to `v2`. |
| Recovery fails with v2 training controller | `RecoverHandler` does not support GatewayTrainController v2. | Disable `recover.mode`, or use v1 controller versions. |
| `return_routed_experts` rejected with vLLM | Routed expert indices are SGLang-only. | Disable `rollout.return_routed_experts` or switch to SGLang. |
| Megatron + LoRA + SGLang rejected | RL trainer does not support this combination. | Use vLLM rollout, disable LoRA, or use FSDP actor. |
| SGLang/vLLM package import fails | Runtime install variant does not match the selected rollout backend. | Confirm the environment has the selected backend installed; route detailed environment repair to the root install/backend skill. |
| NCCL hang, OOM, FP8, LoRA backend failure | Engine-level runtime issue, not a post-training command-shape issue. | Route to `../distributed-engines-backends/`. |

## DPO and RW training issues

| Symptom | Likely cause | Fix |
|---|---|---|
| DPO loss starts far from expected behavior | Actor/ref checkpoints, beta, or data pairing may be wrong. | Check `actor.path`, `ref.path`, `actor.beta`, `actor.loss_type`, and `actor.mb_spec.granularity=2`. |
| DPO metrics missing `dpo/` prefix | Wrong trainer or dataset type was used. | Use `DPOTrainer`, `DPOConfig`, and `train_dataset.type=dpo`. |
| DPO reference receives optimizer steps | `ref.optimizer` was copied from actor. | Set `ref.optimizer=null`. |
| DPO dropout instability | Dropout not disabled. | Set `actor.disable_dropout=true` and normally `ref.disable_dropout=true`. |
| RW loss/data shape issues | Data is not preference-pair style or `actor.is_critic` is false. | Use RW dataset contract and `actor.is_critic=true`; route custom preprocessing to `../custom-data-rewards-workflows/`. |

## Logging, checkpoints, and recovery

| Symptom | Likely cause | Fix |
|---|---|---|
| No tracker logs appear | All tracker modes disabled, or rank is not 0. | For local files, set `stats_logger.tensorboard.path`; for W&B/SwanLab/Trackio, enable only with user-approved credentials. |
| W&B asks for login or blocks | `stats_logger.wandb.mode` is online/shared without credentials. | Use `stats_logger.wandb.mode=disabled` or `offline`, or have the user configure credentials outside the skill. |
| Checkpoints not written | `saver.freq_*` timers all disabled or run ended before a trigger. | Set one of `saver.freq_epochs`, `saver.freq_steps`, or `saver.freq_secs`. |
| Async save warning on non-Archon engine | `saver.mode=async` was requested for FSDP/Megatron. | Use `saver.mode=auto` or `sync`; async saves are Archon-specific. |
| Recovery does not resume | `recover.mode` disabled/off, mismatched experiment/trial/fileroot, or incompatible backend layout. | Set `recover.mode=auto` or `on`, keep the same `experiment_name`, `trial_name`, `fileroot`, model roles, and parallelism. |
| Recovery checkpoint cannot load optimizer | Megatron distributed optimizer or changed optimizer state layout. | Consider `recover.no_load_optim=true`; for some Megatron cases also use `no_save_optim=true` intentionally. |
| Logs/checkpoints hard to locate | `fileroot`, experiment, or trial changed. | Use patterns from `config-api.md`: logs under `<fileroot>/logs/<user>/<experiment>/<trial>`, checkpoints under `<fileroot>/checkpoints/<user>/<experiment>/<trial>`. |
| Successful step not recognized | Looking for the wrong progress marker. | Standard trainer progress includes `Epoch ... Step ... Train step ... done.` |

## Safe triage order

1. Re-run the config validator with the exact command overrides.
2. Fix family/dataset/trainer mismatches before touching backend settings.
3. Fix backend string and GPU-budget mismatches before launching workers.
4. Disable external trackers unless credentials are explicitly available.
5. Decide whether recovery is disabled or v1-compatible before long runs.
6. Only then launch a small bounded run (`total_train_steps=1` if suitable) before a
   full expensive experiment.

Never start a long training job, service, or model download just to diagnose a config
shape issue. Use the validator and bundled references first.

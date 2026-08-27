# `train_ppo_ray` CLI Reference

This reference covers RL-agent-training flags only. Use data-preparation for dataset field semantics and operations-and-utilities for installation, Ray startup, NCCL/CUDA setup, reward-model serving, Slurm, Docker, and checkpoint conversion.

## Entry point

```bash
python -m openrlhf.cli.train_ppo_ray [flags]
```

Ray job submission is common for distributed runs, but the training entry point and flags are the same.

## Resource placement

| Flag | Purpose |
| --- | --- |
| `--ref.num_nodes`, `--ref.num_gpus_per_node` | reference model Ray actor resources |
| `--actor.num_nodes`, `--actor.num_gpus_per_node` | actor/policy model resources |
| `--critic.num_nodes`, `--critic.num_gpus_per_node` | critic resources; omitted internally for non-`gae` estimators |
| `--reward.num_nodes`, `--reward.num_gpus_per_node` | reward model resources when using a model reward |
| `--train.colocate_actor_ref` | share actor/reference GPUs |
| `--train.colocate_critic_reward` | share critic/reward GPUs |
| `--train.colocate_all` | colocate all DeepSpeed models and, in synchronous mode, vLLM engines |

When `--train.colocate_all` and `--train.async_enable` are both set, OpenRLHF warns that async RLHF only colocates DeepSpeed models.

## vLLM generation and sync

| Flag | Purpose |
| --- | --- |
| `--vllm.num_engines` | number of vLLM engines; set to `0` to disable vLLM |
| `--vllm.tensor_parallel_size` | tensor parallel size per vLLM engine |
| `--vllm.sync_backend nccl` | DeepSpeed-to-vLLM weight sync backend; NCCL is the performance path |
| `--vllm.enable_prefix_caching` | enable vLLM prefix caching |
| `--vllm.enforce_eager` | disable CUDA graph in vLLM |
| `--vllm.enable_sleep` | sleep vLLM memory when colocating models in synchronous hybrid engine |
| `--vllm.gpu_memory_utilization` | vLLM memory fraction |

`--vllm.enable_sleep` is disabled unless `--train.colocate_all` is set and is incompatible with async training.

## Async and off-policy flags

| Flag | Purpose |
| --- | --- |
| `--train.async_enable` | run async sampler/trainer pipeline |
| `--train.async_queue_size` | queue depth between sampler and trainer |
| `--train.partial_rollout_enable` | use vLLM pause/resume for partial rollout overlap |
| `--rollout.vllm_generate_batch_size` | vLLM generation batch size; can exceed rollout batch only in async mode |
| `--algo.advantage.is_correction_enable` | enable vLLM importance-sampling correction |
| `--algo.advantage.is_correction_type` | `tis`, `icepop`, or `seq-mask-tis` |
| `--algo.advantage.is_correction_threshold` | low/high truncation thresholds |

Validation rules:

- `--train.partial_rollout_enable` requires `--train.async_enable`.
- `--rollout.vllm_generate_batch_size > --rollout.batch_size` requires `--train.async_enable`.
- Async training cannot use `--vllm.enable_sleep`.

## PPO and rollout sizing

| Flag | Purpose |
| --- | --- |
| `--rollout.batch_size` | number of prompts for experience generation |
| `--rollout.micro_batch_size` | rollout micro-batch size |
| `--train.batch_size` | global training batch size |
| `--train.micro_batch_size` | per-GPU training micro-batch size |
| `--train.max_epochs` | PPO epochs over collected rollout data |
| `--data.max_len` | max prompt plus response tokens |
| `--rollout.max_new_tokens` | max response tokens; if omitted, computed from remaining max length |
| `--rollout.n_samples_per_prompt` | responses per prompt |
| `--rollout.temperature`, `--rollout.top_p` | vLLM sampling controls |
| `--train.dynamic_batch_enable` | dynamic token batch sizing |
| `--rollout.max_tokens_per_gpu`, `--train.max_tokens_per_gpu` | token budgets for dynamic batching |

`--train.dynamic_batch_enable` recommends or enables packing in text-only paths. Packing requires vLLM and flash-attention-style attention.

## Algorithm and KL flags

| Flag | Purpose |
| --- | --- |
| `--algo.advantage.estimator` | `gae`, `reinforce`, `rloo`, `reinforce_baseline`, `group_norm`, or `dr_grpo` |
| `--algo.advantage.lambd`, `--algo.advantage.gamma` | PPO GAE parameters |
| `--actor.eps_clip`, `--actor.eps_clip_low_high` | PPO actor clipping |
| `--actor.dual_clip` | dual-clip PPO |
| `--critic.value_clip` | critic value clipping |
| `--algo.kl.init_coef` | initial KL penalty coefficient |
| `--algo.kl.target`, `--algo.kl.horizon` | adaptive KL controls |
| `--algo.kl.estimator` | `k1`, `k2`, or `k3` |
| `--algo.kl.use_loss` | use KL as loss for GRPO-style training |
| `--algo.advantage.no_std_norm` | mean normalize advantages without std division |
| `--actor.policy_loss_type` | `ppo` or `gspo` |

Validation rules:

- `rloo`, `reinforce_baseline`, `group_norm`, and `dr_grpo` require `--rollout.n_samples_per_prompt > 1`.
- Non-`gae` estimators do not use a critic model.
- If `--algo.kl.use_loss` is set, prefer `--algo.kl.estimator k2` or `k3`.
- If KL is not used as loss, prefer `--algo.kl.estimator k1`.

## Reward and agent flags

| Flag | Purpose |
| --- | --- |
| `--reward.model_name_or_path` | model reward path/name when using a reward model |
| `--reward.remote_url` | local Python reward file, HTTP endpoint, or comma-separated endpoints |
| `--train.agent_func_path` | Python file exporting `AgentExecutor` |
| `--data.label_key` | dataset label field passed as `labels` to rewards/agents |
| `--algo.dynamic_filtering_enable` | filter samples by reward score range |
| `--algo.dynamic_filtering_range` | score range for dynamic filtering |
| `--reward.clip_range` | reward clipping range |
| `--reward.normalize_enable` | reward normalization |
| `--reward.overlong_buffer_len` | DAPO-style overlong buffer length |
| `--reward.overlong_penalty_factor` | DAPO overlong penalty factor |
| `--reward.stop_properly_penalty_coef` | ProRL-style truncation/finish penalty |

Validation rules:

- Setting `--train.agent_func_path` makes OpenRLHF use agent-based reward handling internally.
- Dynamic filtering requires `--reward.remote_url` or `--train.agent_func_path`.
- Dynamic filtering requires `--rollout.n_samples_per_prompt > 1`.

## VLM flags

| Flag | Purpose |
| --- | --- |
| `--data.image_key` | dataset field containing image paths/URLs |
| `--data.max_images_per_prompt` | max images per prompt; `0` means text-only |
| `--actor.freeze_visual_encoder` | freeze vision encoder and sync only trainable language parameters |

Validation rules:

- If `--data.max_images_per_prompt > 0`, critic training is unsupported. Use a non-`gae` estimator.
- If `--data.max_images_per_prompt > 0`, do not use `--ds.packing_samples`.

## Checkpointing and evaluation

| Flag | Purpose |
| --- | --- |
| `--ckpt.path` | checkpoint save/load path |
| `--ckpt.output_dir` | final output directory |
| `--ckpt.save_hf` | save Hugging Face format |
| `--ckpt.save_steps`, `--ckpt.max_num`, `--ckpt.max_mem` | checkpoint cadence and retention |
| `--ckpt.load_enable` | resume loading |
| `--ckpt.best_metric_key` | metric key for best checkpoint |
| `--eval.dataset`, `--eval.split` | evaluation dataset |
| `--eval.temperature`, `--eval.n_samples_per_prompt` | evaluation sampling |

Evaluation with `--eval.dataset` requires either a remote reward URL or an agent function path so eval samples can be scored.

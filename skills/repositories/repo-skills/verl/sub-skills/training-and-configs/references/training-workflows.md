# Training Workflows

This reference distills current verl PPO-like RL, GRPO, SFT, and on-policy distillation command patterns into self-contained guidance. Commands are templates: replace dataset/model paths and resource counts for the target environment.

## Common PPO-like Entry Point

RL-style training uses Hydra through:

```bash
python -m verl.trainer.main_ppo \
  data.train_files=/data/gsm8k/train.parquet \
  data.val_files=/data/gsm8k/test.parquet \
  actor_rollout_ref.model.path=Qwen/Qwen2.5-0.5B-Instruct \
  trainer.logger=console
```

`main_ppo` loads `ppo_trainer` config, validates the resolved config, initializes Ray if needed, then runs the legacy or V1 PPO task runner. It can serve PPO, GRPO-like algorithms, and on-policy distillation by changing Hydra overrides rather than changing the Python module.

### Minimum Override Groups

- **Data**: `data.train_files`, `data.val_files`, `data.train_batch_size`, `data.max_prompt_length`, `data.max_response_length`, `data.filter_overlong_prompts`, `data.truncation`.
- **Actor model**: `actor_rollout_ref.model.path`, `actor_rollout_ref.model.use_remove_padding`, `actor_rollout_ref.model.enable_gradient_checkpointing`, optional LoRA fields.
- **Actor optimizer/update**: `actor_rollout_ref.actor.optim.lr`, `actor_rollout_ref.actor.ppo_mini_batch_size`, micro-batch or dynamic-batch settings, `ppo_max_token_len_per_gpu`.
- **Rollout**: `actor_rollout_ref.rollout.name`, `tensor_model_parallel_size`, `gpu_memory_utilization`, `n`, log-prob batch sizing.
- **Trainer**: `trainer.n_gpus_per_node`, `trainer.nnodes`, `trainer.logger`, `trainer.project_name`, `trainer.experiment_name`, `trainer.save_freq`, `trainer.test_freq`, `trainer.total_epochs`.

## PPO Pattern

Use PPO when training an actor plus critic with GAE/value estimates.

```bash
PYTHONUNBUFFERED=1 python -m verl.trainer.main_ppo \
  algorithm.adv_estimator=gae \
  data.train_files=/data/gsm8k/train.parquet \
  data.val_files=/data/gsm8k/test.parquet \
  data.train_batch_size=256 \
  data.max_prompt_length=512 \
  data.max_response_length=512 \
  actor_rollout_ref.model.path=Qwen/Qwen2.5-0.5B-Instruct \
  actor_rollout_ref.actor.optim.lr=1e-6 \
  actor_rollout_ref.actor.ppo_mini_batch_size=64 \
  actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=4 \
  actor_rollout_ref.rollout.name=vllm \
  actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
  actor_rollout_ref.rollout.gpu_memory_utilization=0.4 \
  actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=4 \
  critic.model.path=Qwen/Qwen2.5-0.5B-Instruct \
  critic.optim.lr=1e-5 \
  critic.ppo_micro_batch_size_per_gpu=4 \
  algorithm.kl_ctrl.kl_coef=0.001 \
  trainer.logger=console \
  trainer.n_gpus_per_node=1 \
  trainer.nnodes=1 \
  trainer.val_before_train=False \
  trainer.save_freq=10 \
  trainer.test_freq=10 \
  trainer.total_epochs=15
```

PPO-specific reminders:

- Include critic overrides (`critic.model.path`, `critic.optim.lr`, critic micro-batch/dynamic-batch settings). GRPO examples intentionally omit critic overrides.
- `algorithm.kl_ctrl.kl_coef` controls in-reward KL when that mechanism is enabled; `actor_rollout_ref.actor.use_kl_loss` controls actor KL loss.
- Micro-batch knobs limit memory per forward/backward pass and should not change intended algorithmic convergence behavior.

## GRPO Pattern

Use GRPO when you want critic-less grouped rollouts.

```bash
python -m verl.trainer.main_ppo \
  algorithm.adv_estimator=grpo \
  algorithm.use_kl_in_reward=False \
  data.train_files='["/data/gsm8k/train.parquet","/data/math/train.parquet"]' \
  data.val_files='["/data/gsm8k/test.parquet","/data/math/test.parquet"]' \
  data.train_batch_size=1024 \
  data.max_prompt_length=1024 \
  data.max_response_length=2048 \
  data.filter_overlong_prompts=True \
  data.truncation=error \
  actor_rollout_ref.model.path=Qwen/Qwen3-8B \
  actor_rollout_ref.model.use_remove_padding=True \
  actor_rollout_ref.model.enable_gradient_checkpointing=True \
  actor_rollout_ref.actor.optim.lr=1e-6 \
  actor_rollout_ref.actor.ppo_mini_batch_size=256 \
  actor_rollout_ref.actor.use_dynamic_bsz=True \
  actor_rollout_ref.actor.ppo_max_token_len_per_gpu=24576 \
  actor_rollout_ref.actor.use_kl_loss=True \
  actor_rollout_ref.actor.kl_loss_coef=0.001 \
  actor_rollout_ref.actor.kl_loss_type=low_var_kl \
  actor_rollout_ref.rollout.name=vllm \
  actor_rollout_ref.rollout.tensor_model_parallel_size=2 \
  actor_rollout_ref.rollout.gpu_memory_utilization=0.6 \
  actor_rollout_ref.rollout.n=5 \
  actor_rollout_ref.ref.log_prob_use_dynamic_bsz=True \
  trainer.logger='["console","wandb"]' \
  trainer.n_gpus_per_node=8 \
  trainer.nnodes=1 \
  trainer.total_epochs=15
```

GRPO-specific reminders:

- Set `actor_rollout_ref.rollout.n` greater than 1 for group sampling.
- Set `algorithm.adv_estimator=grpo` and typically `actor_rollout_ref.actor.use_kl_loss=True` with `algorithm.use_kl_in_reward=False`.
- Loss aggregation defaults to `token-mean`; DrGRPO-style behavior uses `actor_rollout_ref.actor.loss_agg_mode=seq-mean-token-sum-norm`, `algorithm.norm_adv_by_std_in_grpo=False`, and usually disables KL loss.
- DAPO-style dynamic sampling uses `data.gen_batch_size`, `algorithm.filter_groups.enable=True`, `algorithm.filter_groups.metric`, and `algorithm.filter_groups.max_num_gen_batches`.

## SFT Pattern

SFT uses a different module and usually launches with `torchrun`:

```bash
torchrun --standalone --nnodes=1 --nproc_per_node=8 \
  -m verl.trainer.sft_trainer \
  data.train_files=/data/gsm8k/train.parquet \
  data.val_files=/data/gsm8k/test.parquet \
  data.messages_key=messages \
  data.micro_batch_size_per_gpu=4 \
  optim.lr=1e-4 \
  engine=fsdp \
  engine.ulysses_sequence_parallel_size=1 \
  model.path=Qwen/Qwen2.5-0.5B-Instruct \
  model.use_remove_padding=true \
  trainer.default_local_dir=/checkpoints/sft \
  trainer.project_name=gsm8k-sft \
  trainer.experiment_name=qwen2_5_0_5b \
  trainer.logger='["console","wandb"]' \
  trainer.total_epochs=1
```

SFT-specific reminders:

- `sft_trainer` config defaults include `model`, `engine`, `optim`, and `profiler`; `engine=fsdp` is the common FSDP path.
- Multi-turn SFT uses `data.messages_key`, optional `tools_key`, `enable_thinking_key`, and `ignore_input_ids_mismatch` if tokenizer chat-template concatenation differs from whole-message templating.
- LoRA/PEFT-style SFT examples add `model.lora_rank`, `model.lora_alpha`, and `model.target_modules`.

## On-policy Distillation Pattern

Distillation reuses `main_ppo` and enables teacher-model inference under the `distillation` config.

```bash
python -m verl.trainer.main_ppo \
  algorithm.adv_estimator=grpo \
  algorithm.use_kl_in_reward=False \
  data.train_files='["/data/gsm8k/train.parquet","/data/math/train.parquet"]' \
  data.val_files='["/data/gsm8k/test.parquet","/data/math/test.parquet"]' \
  data.train_batch_size=128 \
  data.max_prompt_length=1024 \
  data.max_response_length=2048 \
  actor_rollout_ref.model.path=Qwen/Qwen3-8B \
  actor_rollout_ref.rollout.name=vllm \
  actor_rollout_ref.rollout.tensor_model_parallel_size=2 \
  actor_rollout_ref.rollout.max_model_len=3073 \
  distillation.enabled=True \
  distillation.n_gpus_per_node=4 \
  distillation.nnodes=1 \
  distillation.teacher_models.teacher_model.model_path=Qwen/Qwen3-32B \
  distillation.teacher_models.teacher_model.inference.name=vllm \
  distillation.teacher_models.teacher_model.inference.tensor_model_parallel_size=2 \
  distillation.teacher_models.teacher_model.inference.gpu_memory_utilization=0.4 \
  distillation.teacher_models.teacher_model.inference.max_model_len=3073 \
  distillation.distillation_loss.loss_mode=k1 \
  distillation.distillation_loss.topk=64 \
  distillation.distillation_loss.use_task_rewards=False \
  distillation.distillation_loss.use_policy_gradient=True \
  trainer.n_gpus_per_node=8 \
  trainer.nnodes=1 \
  trainer.total_epochs=15
```

Distillation-specific reminders:

- Teacher resources are separate from trainer resources: `distillation.n_gpus_per_node * distillation.nnodes` must equal the sum of teacher `num_replicas * inference.data_parallel_size * inference.tensor_model_parallel_size * inference.pipeline_model_parallel_size` after resolution.
- A single default `teacher_model` can occupy the whole teacher pool; for multiple teachers, use added keys like `+distillation.teacher_models.teacher_model1...` and include each teacher `key`, `model_path`, `num_replicas`, and `inference.*` fields.
- Teacher inference needs room for student prompt plus full student response plus one generated token; keep teacher `inference.max_model_len >= data.max_prompt_length + data.max_response_length + 1`.

## One-GPU Debug Adaptation

For a fast sanity command adapted from larger examples, reduce resources and memory pressure rather than preserving production batch sizes:

```bash
python -m verl.trainer.main_ppo \
  algorithm.adv_estimator=grpo \
  data.train_files=/data/tiny/train.parquet \
  data.val_files=/data/tiny/test.parquet \
  data.train_batch_size=8 \
  data.max_prompt_length=256 \
  data.max_response_length=256 \
  actor_rollout_ref.model.path=Qwen/Qwen2.5-0.5B-Instruct \
  actor_rollout_ref.actor.ppo_mini_batch_size=8 \
  actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=1 \
  actor_rollout_ref.actor.use_dynamic_bsz=True \
  actor_rollout_ref.actor.use_kl_loss=True \
  actor_rollout_ref.rollout.name=vllm \
  actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
  actor_rollout_ref.rollout.gpu_memory_utilization=0.35 \
  actor_rollout_ref.rollout.n=2 \
  actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=1 \
  trainer.logger=console \
  trainer.n_gpus_per_node=1 \
  trainer.nnodes=1 \
  trainer.val_before_train=False \
  trainer.save_freq=-1 \
  trainer.test_freq=1 \
  trainer.total_epochs=1
```

This is still GPU-expensive if the model/backend is large. For CPU-only algorithm verification, prefer CPU unit tests that exercise core algorithms rather than launching `main_ppo`.

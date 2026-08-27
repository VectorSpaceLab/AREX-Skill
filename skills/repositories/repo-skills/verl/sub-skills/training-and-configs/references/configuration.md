# Configuration Reference

verl training is primarily configured with Hydra overrides layered on YAML defaults. This reference summarizes the fields a coding agent most often needs when assembling or modifying training commands.

## Hydra Basics

- `python -m verl.trainer.main_ppo` uses config name `ppo_trainer` from `verl/trainer/config`.
- `torchrun -m verl.trainer.sft_trainer` uses the SFT trainer config with defaults for `model`, `engine`, `optim`, and `profiler`.
- Override syntax is `section.key=value`; use quotes around JSON-like lists: `trainer.logger='["console","wandb"]'`.
- Use `+new.key=value` only when adding a key not present in the base config, such as extra Ray init values or additional distillation teachers.
- Flattened generated configs are reference material for humans; do not treat generated `_generated_*.yaml` files as the launch config.

## Data Fields

- `data.train_files` and `data.val_files` accept a single path or a list-like string. verl reads training data into memory, so avoid huge unsharded inputs.
- `data.prompt_key` defaults to `prompt` for RL-style data; SFT commonly uses `data.messages_key=messages`.
- `data.max_prompt_length` and `data.max_response_length` control token budgets for RL rollouts.
- `data.truncation=error` fails on overlong prompts; `left`, `right`, and `middle` truncate instead.
- `data.filter_overlong_prompts=True` filters before training and is useful for examples that mix GSM8K/MATH.
- `data.custom_cls.path` and `data.custom_cls.name` support custom dataset classes; keep this outside the training-and-configs scope unless the task is only wiring the config.

## Actor, Reference, Rollout, and Critic

- `actor_rollout_ref.model.path` is the policy model path/name. PPO usually also sets `critic.model.path`.
- `actor_rollout_ref.model.use_remove_padding=True` improves efficiency for many examples.
- `actor_rollout_ref.model.enable_gradient_checkpointing=True` reduces memory for actor FSDP paths.
- `actor_rollout_ref.actor.ppo_mini_batch_size` is global; `ppo_micro_batch_size_per_gpu` or dynamic-batch token limits control memory.
- `actor_rollout_ref.rollout.name` selects rollout backend such as `vllm`, `sglang`, `trtllm`, or `hf` when supported by the environment.
- `actor_rollout_ref.rollout.tensor_model_parallel_size` should fit available accelerator count and model size.
- `actor_rollout_ref.rollout.gpu_memory_utilization` is a backend memory cap; lowering it can avoid allocation failures but may reduce throughput.
- Reference policy is required when KL loss or in-reward KL requires it; `main_ppo` decides via config validation helpers.
- PPO needs critic fields; GRPO/RLOO-style critic-less algorithms typically omit critic overrides and set the relevant advantage estimator.

## Algorithms

- PPO default: `algorithm.adv_estimator=gae`; include critic overrides.
- GRPO: `algorithm.adv_estimator=grpo`, `actor_rollout_ref.rollout.n>1`, `actor_rollout_ref.actor.use_kl_loss=True`, and usually `algorithm.use_kl_in_reward=False`.
- KL reward penalty: `algorithm.use_kl_in_reward=True`, `algorithm.kl_penalty`, and `algorithm.kl_ctrl.*`.
- KL actor loss: `actor_rollout_ref.actor.use_kl_loss=True`, `kl_loss_coef`, and `kl_loss_type`.
- DAPO-style dynamic sampling: `data.gen_batch_size`, `algorithm.filter_groups.enable=True`, `algorithm.filter_groups.metric`, and `max_num_gen_batches`.
- Loss aggregation: `actor_rollout_ref.actor.loss_agg_mode` supports token- and sequence-oriented options; examples generally use `token-mean` unless reproducing a specific recipe.

## Backend Strategy Switches

### FSDP and FSDP2

- Default `ppo_trainer` uses `model_engine=dp`, which resolves actor/ref/critic config groups from the data-parallel engine set. FSDP-style fields live under `actor_rollout_ref.actor.fsdp_config`, `actor_rollout_ref.ref.fsdp_config`, and `critic.fsdp` or backend-specific nested names in examples.
- FSDP engine config supports `strategy=fsdp` or `strategy=fsdp2`, parameter/optimizer offload, `fsdp_size`, `reshard_after_forward`, `model_dtype`, `use_orig_params`, and `ulysses_sequence_parallel_size`.
- Use micro-batches, dynamic batching, offload, gradient checkpointing, and lower rollout memory before increasing hardware assumptions.

### Megatron

- Switch RL training with `model_engine=megatron`.
- Important fields include `actor_rollout_ref.actor.megatron.tensor_model_parallel_size`, `pipeline_model_parallel_size`, and matching reference/critic Megatron sizes.
- Megatron examples often export `CUDA_DEVICE_MAX_CONNECTIONS=1` and use vLLM rollout.
- LoRA under Megatron uses `actor_rollout_ref.model.lora.*` and requires Megatron-Bridge support; FSDP-specific LoRA keys are not equivalent.

### VeOmni and TorchTitan

- Switch reference configs with `model_engine=veomni` or `model_engine=torchtitan` when the environment supports those engines.
- VeOmni engine config includes offload, FSDP/full-shard, Ulysses/expert parallelism, init device, attention implementation, and related distributed settings.
- TorchTitan engine config includes data/tensor/expert/pipeline/context parallel sizes, FSDP-like offload and reshard controls, dtype, attention type, and compile flags.
- Generated reference YAMLs for these engines show resolved field names but are not meant to be manually edited.

## LoRA and PEFT

FSDP/FSDP2 RL LoRA uses Hugging Face PEFT-style keys:

```bash
actor_rollout_ref.model.lora_rank=32 \
actor_rollout_ref.model.lora_alpha=32 \
actor_rollout_ref.model.target_modules=all-linear \
actor_rollout_ref.rollout.load_format=safetensors
```

Useful FSDP LoRA additions include `actor_rollout_ref.model.use_shm=True` and `actor_rollout_ref.rollout.layered_summon=True` for large models or limited memory. SGLang currently requires merged LoRA adapters when using that path.

Megatron LoRA uses nested `actor_rollout_ref.model.lora.*` fields such as `rank`, `alpha`, `target_modules`, `merge`, and adapter settings.

## Trainer and Logging

- `trainer.logger=console` is best for minimal debug. Use `trainer.logger='["console","wandb"]'`, `trainer.project_name`, and `trainer.experiment_name` for experiment tracking.
- `trainer.val_before_train=False` skips initial validation for quick debug.
- `trainer.save_freq=-1` disables periodic checkpoint saving; set positive frequencies for real runs.
- Default local checkpoints resolve under `checkpoints/${trainer.project_name}/${trainer.experiment_name}` unless overridden.
- `trainer.use_v1=True` selects the V1 trainer path; otherwise the legacy trainer path emits a deprecation warning.

## Reference-only Repo Scripts

- `print_cfg.py` is a Hydra config printer used by maintainers to inspect resolved configs.
- `generate_trainer_config.sh` regenerates flattened reference YAML files and checks that they match git diff.
- Treat both as evidence and maintenance utilities, not as runtime dependencies for generated skills.

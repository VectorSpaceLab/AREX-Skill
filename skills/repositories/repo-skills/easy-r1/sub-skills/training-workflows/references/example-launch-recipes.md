# Example launch recipes

These recipes are distilled from EasyR1 training configurations and shell launch patterns. They are intentionally written as self-contained commands against a user-owned YAML file. Replace model IDs, local model directories, dataset identifiers, reward function paths, and logger choices with assets available in the target runtime.

All commands are dry plans until you run them yourself. They require a full CUDA EasyR1 runtime with Ray, vLLM, flash-attn, compatible PyTorch, model weights, datasets, and enough GPUs.

## Preflight before any full training run

1. Confirm the training package can be imported in the intended runtime:

```bash
python -c "import verl, ray, vllm; print('EasyR1 runtime import OK')"
```

2. Confirm GPU and Ray resources:

```bash
nvidia-smi
ray status
```

3. Lint the YAML without starting training:

```bash
python scripts/easyr1_config_lint.py /path/to/easyr1_config.yaml --strict
```

4. Build a shell-quoted command before executing it:

```bash
python scripts/easyr1_command_builder.py /path/to/easyr1_config.yaml \
  --override worker.actor.model.model_path=Qwen/Qwen2.5-7B-Instruct \
  --override trainer.n_gpus_per_node=8 \
  --multiline
```

## Minimal command shape

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  worker.actor.model.model_path=Qwen/Qwen2.5-7B-Instruct \
  trainer.experiment_name=my_easy_r1_run
```

Use CLI overrides for run-specific values. Keep stable defaults in YAML.

## Text GRPO, 7B-style full fine-tuning

Use this shape for a text dataset with the default GRPO-style estimator.

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=hiyouga/math12k@train \
  data.val_files=hiyouga/math12k@test \
  worker.actor.model.model_path=Qwen/Qwen2.5-7B-Instruct \
  trainer.experiment_name=qwen2_5_7b_math_grpo \
  trainer.n_gpus_per_node=8
```

Notes:

- GRPO requires `worker.rollout.n > 1`; the canonical YAML uses grouped rollouts.
- Keep `worker.actor.model.trust_remote_code=false` unless the target model requires custom code and the runtime owner has approved it.

## Qwen3 4B text GRPO with LoRA

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.max_response_length=2048 \
  worker.actor.model.model_path=Qwen/Qwen3-4B \
  worker.actor.model.lora.rank=64 \
  worker.actor.model.lora.alpha=64 \
  worker.actor.optim.lr=1e-5 \
  worker.rollout.tensor_parallel_size=1 \
  trainer.experiment_name=qwen3_4b_math_grpo_lora \
  trainer.n_gpus_per_node=1
```

LoRA reduces training memory, but full training still requires vLLM LoRA support and a GPU runtime. Use the config linter to catch suspicious VL LoRA settings.

## Vision-language GRPO on Geometry3K-style data

7B VL shape:

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=hiyouga/geometry3k@train \
  data.val_files=hiyouga/geometry3k@test \
  worker.actor.model.model_path=Qwen/Qwen2.5-VL-7B-Instruct \
  trainer.experiment_name=qwen2_5_vl_7b_geo_grpo \
  trainer.n_gpus_per_node=8
```

3B/4B VL shape on fewer GPUs:

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=hiyouga/geometry3k@train \
  data.val_files=hiyouga/geometry3k@test \
  worker.actor.model.model_path=Qwen/Qwen3-VL-4B-Instruct \
  trainer.experiment_name=qwen3_vl_4b_geo_grpo \
  trainer.n_gpus_per_node=2
```

32B/30B-style VL shape uses BF16 and larger tensor parallelism:

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=hiyouga/geometry3k@train \
  data.val_files=hiyouga/geometry3k@test \
  worker.actor.model.model_path=Qwen/Qwen3-VL-30B-A3B-Instruct \
  worker.actor.fsdp.torch_dtype=bf16 \
  worker.actor.optim.strategy=adamw_bf16 \
  worker.rollout.tensor_parallel_size=8 \
  trainer.experiment_name=qwen3_vl_30b_geo_grpo \
  trainer.n_gpus_per_node=8
```

VL-specific cautions:

- If image features and image tokens do not match, increase `data.max_prompt_length` or reduce `data.max_pixels`.
- Avoid `worker.actor.ulysses_size > 1` for VLMs unless that runtime has explicitly validated it.
- Use `worker.rollout.limit_images` for multi-image tasks so vLLM receives a bounded image count per prompt.

## Vision-language LoRA GRPO

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=hiyouga/geometry3k@train \
  data.val_files=hiyouga/geometry3k@test \
  worker.actor.model.model_path=Qwen/Qwen3-VL-4B-Instruct \
  worker.actor.model.lora.rank=64 \
  worker.actor.model.lora.alpha=64 \
  worker.actor.model.lora.exclude_modules='.*visual.*' \
  worker.rollout.tensor_parallel_size=1 \
  trainer.experiment_name=qwen3_vl_4b_geo_grpo_lora \
  trainer.n_gpus_per_node=2
```

Why the visual exclusion matters: the distilled EasyR1 configuration warns that vLLM does not support ViT LoRA for Qwen-VL-style models, so exclude visual modules when applying LoRA to VL models.

## DAPO-style Geometry3K online filtering

DAPO-style runs are expressed as GRPO-like training with online filtering and asymmetric clipping.

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=hiyouga/geometry3k@train \
  data.val_files=hiyouga/geometry3k@test \
  data.mini_rollout_batch_size=128 \
  worker.actor.model.model_path=Qwen/Qwen2.5-VL-7B-Instruct \
  worker.actor.clip_ratio_low=0.2 \
  worker.actor.clip_ratio_high=0.28 \
  algorithm.disable_kl=True \
  algorithm.online_filtering=True \
  trainer.experiment_name=qwen2_5_vl_7b_geo_dapo \
  trainer.n_gpus_per_node=8
```

Check before launching:

- `algorithm.filter_key` must name a reward metric emitted by the reward function.
- `algorithm.filter_low < algorithm.filter_high`.
- `trainer.max_try_make_batch` should be finite unless the operator accepts potentially long regeneration loops.

## Long-response DAPO17k-style text run

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=Saigyouji-Yuyuko1000/dapo17k@train \
  data.val_files=Saigyouji-Yuyuko1000/dapo17k@test \
  data.format_prompt=/path/to/dapo_prompt.jinja \
  data.max_prompt_length=2048 \
  data.max_response_length=20480 \
  data.rollout_batch_size=512 \
  data.mini_rollout_batch_size=256 \
  worker.actor.ulysses_size=8 \
  worker.actor.model.model_path=Qwen/Qwen3-14B-Base \
  worker.actor.fsdp.torch_dtype=bf16 \
  worker.actor.optim.strategy=adamw_bf16 \
  worker.actor.optim.weight_decay=0.1 \
  worker.actor.optim.lr_warmup_steps=10 \
  worker.actor.global_batch_size=32 \
  worker.actor.clip_ratio_low=0.2 \
  worker.actor.clip_ratio_high=0.28 \
  worker.actor.clip_ratio_dual=10.0 \
  worker.rollout.n=16 \
  worker.rollout.max_num_batched_tokens=22528 \
  worker.rollout.val_override_config='{"n":16,"temperature":1.0,"top_p":0.7}' \
  worker.rollout.gpu_memory_utilization=0.8 \
  worker.rollout.tensor_parallel_size=4 \
  worker.reward.reward_function=/path/to/dapo_reward.py:compute_score \
  worker.reward.reward_function_kwargs='{"max_response_length":20480,"overlong_buffer_length":4096,"overlong_penalty_factor":1.0}' \
  algorithm.disable_kl=True \
  algorithm.online_filtering=True \
  algorithm.filter_key=accuracy_normalized \
  algorithm.filter_low=0.01 \
  algorithm.filter_high=0.99 \
  trainer.total_epochs=10 \
  trainer.max_try_make_batch=10 \
  trainer.experiment_name=qwen3_14b_dapo17k_dapo \
  trainer.n_gpus_per_node=8
```

This recipe is memory- and time-intensive. Verify `worker.rollout.max_num_batched_tokens > data.max_prompt_length + data.max_response_length`; here, `22528 > 2048 + 20480`.

## Reinforce++

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=hiyouga/geometry3k@train \
  data.val_files=hiyouga/geometry3k@test \
  worker.actor.model.model_path=Qwen/Qwen2.5-VL-7B-Instruct \
  algorithm.adv_estimator=reinforce_plus_plus \
  trainer.experiment_name=qwen2_5_vl_7b_geo_reinforce_plus_plus \
  trainer.n_gpus_per_node=8
```

Use the exact value `reinforce_plus_plus`.

## GSPO, CISPO, and SAPO policy-loss variants

GSPO token variant:

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=hiyouga/geometry3k@train \
  data.val_files=hiyouga/geometry3k@test \
  worker.actor.model.model_path=Qwen/Qwen2.5-VL-7B-Instruct \
  worker.actor.loss_type=gspo_token \
  worker.actor.loss_avg_mode=seq \
  worker.actor.clip_ratio_low=3e-4 \
  worker.actor.clip_ratio_high=4e-4 \
  algorithm.disable_kl=True \
  trainer.experiment_name=qwen2_5_vl_7b_geo_gspo \
  trainer.n_gpus_per_node=8
```

CISPO:

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=hiyouga/geometry3k@train \
  data.val_files=hiyouga/geometry3k@test \
  worker.actor.model.model_path=Qwen/Qwen2.5-VL-7B-Instruct \
  worker.actor.loss_type=cispo \
  worker.actor.clip_ratio_low=0 \
  worker.actor.clip_ratio_high=4 \
  trainer.experiment_name=qwen2_5_vl_7b_geo_cispo \
  trainer.n_gpus_per_node=8
```

SAPO:

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=hiyouga/geometry3k@train \
  data.val_files=hiyouga/geometry3k@test \
  worker.actor.model.model_path=Qwen/Qwen2.5-VL-7B-Instruct \
  worker.actor.loss_type=sapo \
  algorithm.disable_kl=True \
  trainer.experiment_name=qwen2_5_vl_7b_geo_sapo \
  trainer.n_gpus_per_node=8
```

## Multi-image VL debugging

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=hiyouga/journeybench-multi-image-vqa@train \
  data.val_files=hiyouga/journeybench-multi-image-vqa@test \
  data.rollout_batch_size=256 \
  worker.actor.model.model_path=Qwen/Qwen2.5-VL-7B-Instruct \
  worker.rollout.limit_images=2 \
  trainer.experiment_name=qwen2_5_vl_7b_multi_image_debug \
  trainer.n_gpus_per_node=8
```

Treat multi-image test-split examples as debugging patterns, not as production dataset recommendations. Dataset schema and prompt-template details belong to `data-and-rewards`.

## Android GUI number-game training shape

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=yuehua-s/numbergame@train \
  data.val_files=yuehua-s/numbergame@test \
  data.max_prompt_length=3072 \
  data.max_response_length=64 \
  data.rollout_batch_size=32 \
  data.val_batch_size=60 \
  data.format_prompt=/path/to/android_gui_prompt.jinja \
  data.seed=42 \
  data.filter_overlong_prompts=false \
  algorithm.kl_coef=4.0e-2 \
  worker.actor.global_batch_size=32 \
  worker.actor.max_grad_norm=0.1 \
  worker.actor.model.model_path=Qwen/Qwen2.5-VL-3B-Instruct \
  worker.actor.model.trust_remote_code=true \
  worker.actor.optim.lr=1.0e-5 \
  worker.actor.optim.weight_decay=1.0e-1 \
  worker.actor.optim.lr_warmup_ratio=0.05 \
  worker.actor.optim.lr_scheduler_type=constant \
  worker.rollout.n=8 \
  worker.rollout.temperature=0.9 \
  worker.rollout.top_p=0.95 \
  worker.rollout.limit_images=1 \
  worker.rollout.gpu_memory_utilization=0.75 \
  worker.rollout.tensor_parallel_size=1 \
  worker.reward.reward_function=/path/to/android_gui_reward.py:compute_score \
  trainer.total_epochs=3 \
  trainer.project_name=easy_r1 \
  trainer.experiment_name=qwen2_5_vl_3b_android_gui_grpo \
  trainer.logger='["console","wandb"]' \
  trainer.n_gpus_per_node=2 \
  trainer.nnodes=1 \
  trainer.val_freq=2 \
  trainer.val_generations_to_log=10 \
  trainer.save_freq=10
```

This is only the training-launch shape. Android device, game-service, prompt, and reward details are handled by `data-and-rewards`.

## R1-V-style baselines

Clevr-style counting:

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=BUAADreamer/clevr_count_70k@train \
  data.val_files=BUAADreamer/clevr_count_70k@test \
  data.format_prompt=/path/to/r1v_prompt.jinja \
  worker.actor.model.model_path=Qwen/Qwen2.5-VL-3B-Instruct \
  worker.rollout.tensor_parallel_size=1 \
  worker.reward.reward_function=/path/to/r1v_reward.py:compute_score \
  trainer.experiment_name=qwen2_5_vl_3b_clevr \
  trainer.n_gpus_per_node=2
```

GeoQA-style:

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  data.train_files=leonardPKU/GEOQA_8K_R1V@train \
  data.val_files=leonardPKU/GEOQA_8K_R1V@test \
  data.format_prompt=/path/to/r1v_prompt.jinja \
  worker.actor.model.model_path=Qwen/Qwen2.5-VL-3B-Instruct \
  worker.rollout.tensor_parallel_size=1 \
  worker.reward.reward_function=/path/to/r1v_reward.py:compute_score \
  trainer.experiment_name=qwen2_5_vl_3b_geoqa8k \
  trainer.n_gpus_per_node=8
```

## Logger variants

Default config can use file and hosted loggers. For a local first pass:

```bash
trainer.logger='["console","file"]'
```

For SwanLab:

```bash
trainer.logger='["console","swanlab"]'
```

For Weights & Biases:

```bash
trainer.logger='["console","wandb"]'
```

Hosted loggers need credentials in the runtime environment. If credentials are missing, switch to `console` or `file`.

## Save, resume, and validation-only patterns

Frequent checkpointing with retention:

```bash
trainer.save_freq=5 \
trainer.save_limit=3 \
trainer.save_model_only=false
```

Explicit resume:

```bash
trainer.load_checkpoint_path=/path/to/checkpoints/easy_r1/my_exp/global_step_100
```

Automatic latest-checkpoint resume under the save directory:

```bash
trainer.find_last_checkpoint=True
```

Validation-only pass:

```bash
trainer.val_before_train=True \
trainer.val_only=True
```

Short GPU smoke after full runtime preparation:

```bash
trainer.max_steps=1 \
trainer.val_before_train=false \
trainer.save_freq=-1
```

A short smoke still starts Ray/vLLM and uses CUDA; it is not a CPU test.

## Multi-node launch pattern

Start the head node:

```bash
ray start --head --port=6379 --dashboard-host=0.0.0.0
```

Start workers:

```bash
ray start --address=<head_node_ip>:6379
```

Check cluster resources:

```bash
ray status
```

Launch training on the head node only:

```bash
python -m verl.trainer.main \
  config=/path/to/easyr1_config.yaml \
  trainer.nnodes=2 \
  trainer.n_gpus_per_node=8 \
  worker.rollout.tensor_parallel_size=8 \
  worker.actor.model.model_path=/path/to/local_or_cached_model \
  trainer.experiment_name=multi_node_easy_r1
```

The Ray resource pool uses `[trainer.n_gpus_per_node] * trainer.nnodes`. If the cluster does not report that many GPUs, training fails before workers initialize.

## Useful environment variables

```bash
export PYTHONUNBUFFERED=1
export USE_MODELSCOPE_HUB=1        # if using ModelScope instead of Hugging Face Hub
export HF_ENDPOINT=https://hf-mirror.com  # if the runtime owner uses that mirror
export RAY_PROFILING=1             # only when collecting a Ray timeline
```

Set `trainer.ray_timeline=/path/to/timeline.json` to write a Ray timeline after training when profiling is enabled.

# RLHF, GRPO, GKD, Sampling, and Rollout Workflows

This reference covers advanced `swift rlhf`, `swift sample`, and `swift rollout` work. It intentionally omits full dataset schemas; use the data-model-customization sibling for detailed field conversion and template/data registration.

## Algorithm Selection

| Goal | `--rlhf_type` | Typical Inputs | Notes |
| --- | --- | --- | --- |
| Group-relative outcome RL | `grpo` | prompts plus reward columns needed by reward functions | Requires `num_generations >= 2`; reward std of zero gives no learning signal for that prompt group. |
| Generalized distillation | `gkd` | student data, teacher model or teacher API | Uses JSD/KL style loss; `teacher_model_server` requires `gkd_logits_topk`. |
| Classical RLHF with value model | `ppo` | prompts, reward model, value model/ref model choices | More moving parts than GRPO; watch rollout batch size and reward whitening. |
| Preference pairs | `dpo`, `cpo`, `simpo`, `orpo` | prompt + chosen + rejected | Use when the dataset already has pairwise preference labels. |
| Binary desirability | `kto` | prompt + response + label | Tune desirable/undesirable weights for imbalanced labels. |
| Reward model training | `rm` | prompt + chosen + rejected, optional margin | Produces reward/value-head weights for later stages. |

## GRPO Command Pattern

A safe starting shape for a single-node GRPO run is:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 \
swift rlhf \
  --rlhf_type grpo \
  --model <model-id-or-path> \
  --dataset <dataset-id-or-path> \
  --num_generations 8 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 8 \
  --steps_per_generation 8 \
  --max_length 4096 \
  --max_completion_length 1024 \
  --reward_funcs accuracy format \
  --use_vllm true \
  --vllm_mode colocate \
  --vllm_gpu_memory_utilization 0.6 \
  --sleep_level 1 \
  --offload_model true \
  --offload_optimizer true
```

Key checks:

- `generation_batch_size` must be divisible by `num_generations`. If omitted, ms-swift derives it from the global train batch and `steps_per_generation`.
- For GRPO, `per_device_train_batch_size` is completion-level, not prompt-level. Prompt count is completion count divided by `num_generations`.
- `beta 0` disables the reference-model KL term; the default GRPO beta is small (`0.04`) when not set.
- `loss_type` can be `grpo`, `bnpo`, `dr_grpo`, `dapo`, `cispo`, `sapo`, `real`, or `fipo` in the standard trainer; advanced choices may impose extra parameter constraints.
- `importance_sampling_level sequence` enables GSPO-style sequence-level importance sampling; `sequence_token` combines sequence and token forms where supported.
- `advantage_estimator rloo` or `reinforce_plus_plus` changes the baseline and typically pairs with `kl_in_reward true` and different reward scaling defaults.

Use `scripts/build_rlhf_command.py --mode swift-grpo` to generate a non-executing skeleton and adjust model, dataset, and GPU count.

## Advanced GRPO Options

| Feature | Main Arguments | When Useful | Watch For |
| --- | --- | --- | --- |
| DAPO-style filtering | `--loss_type dapo`, `--overlong_filter true`, `--dynamic_sample true`, `--soft_cache_length N` | Long reasoning where truncated completions add noise | `soft_overlong` reward requires `soft_cache_length < soft_max_length`. |
| CISPO | `--loss_type cispo`, `--epsilon_high <value>` | Clip importance weights directly | Confirm the desired upper clipping behavior. |
| SAPO | `--loss_type sapo`, `--tau_pos`, `--tau_neg` | Smooth off-policy attenuation | Token-level importance sampling is expected; avoid combining blindly with GSPO. |
| FIPO | `--loss_type fipo`, `--fipo_decay_rate`, `--fipo_clip_range` | Token credit assignment using future-KL signal | Validate stability with short runs first. |
| REAL | `--loss_type real` | Monotonic bounded gradient weighting | Requires batch/group constraints; Megatron requires `micro_batch_size` multiple of `num_generations`. |
| Off-policy diagnostics | `--log_rollout_offpolicy_metrics true` | Observe rollout/training mismatch | Does not correct mismatch unless a correction mode is enabled. |
| Mismatch correction | `--rollout_importance_sampling_mode token_truncate|token_mask|sequence_truncate|sequence_mask` | vLLM policy drift or async/server rollout mismatch | Requires usable rollout logprobs; monitor effective sample size and KL. |
| Sequence masking | `--off_policy_sequence_mask_delta <float>` | Drop negative-advantage sequences with high policy shift | Can reduce learning signal if threshold is too low. |
| Multi-reward scaling | `--scale_rewards gdpo`, `--reward_weights ...` | Multiple reward functions with different scales | GDPO does not support `kl_in_reward true`. |

## Reward Functions and Plugins

Built-in outcome rewards include `accuracy`, `format`, `cosine`, `repetition`, and `soft_overlong`. Custom rewards are loaded via `--external_plugins <plugin.py>` and registered into `swift.rewards.orms`.

Minimal synchronous reward pattern:

```python
from swift.rewards import ORM, orms

class SolutionPresenceReward(ORM):
    def __call__(self, completions, solution, **kwargs):
        return [1.0 if str(sol).strip() and str(sol).strip() in text else 0.0
                for text, sol in zip(completions, solution)]

orms['solution_presence'] = SolutionPresenceReward
```

Minimal async reward pattern for API/database scoring:

```python
from swift.rewards import AsyncORM, orms

class AsyncJudgeReward(AsyncORM):
    async def __call__(self, completions, **kwargs):
        return [0.0 for _ in completions]

orms['async_judge'] = AsyncJudgeReward
```

Practical reward checks:

- The reward `__call__` receives `completions`, dataset columns that survived preprocessing, `trainer_state`, token IDs where applicable, and other keyword arguments. Always accept `**kwargs` so future columns do not break the plugin.
- If a reward needs a column such as `solution`, declare it explicitly or read `kwargs.get('solution')`; missing columns usually indicate data preprocessing or `vllm_server_pass_dataset` issues, not reward math issues.
- For multi-task reward functions, return `None` for samples outside the reward's task when combining task-specific rewards.
- Reward model loading inside a reward function can conflict with DeepSpeed/ZeRO-3 initialization; prefer an external service, a lightweight rule, or an async API reward for heavyweight judges.

## GRPO Rollout Modes

### Colocate Mode

`swift rlhf --use_vllm true --vllm_mode colocate` starts vLLM inside the training job. This is simpler but shares GPU memory with training.

Common memory controls:

- Lower `--vllm_gpu_memory_utilization`.
- Enable `--sleep_level 1` or `2` so vLLM frees memory while training steps run.
- Set `--offload_model true` and `--offload_optimizer true` to move training state during rollout.
- Use `--vllm_tensor_parallel_size` for large rollout models.
- For LoRA training, set `--vllm_enable_lora true` and match `--vllm_max_lora_rank` on rollout servers to the training `lora_rank`.
- For multimodal ViT LoRA sync, pass `--vllm_engine_kwargs '{"enable_tower_connector_lora": true}'` where the vLLM/model combination supports it.

### Server Mode

Start a rollout server, then point training at it:

```bash
CUDA_VISIBLE_DEVICES=4,5 swift rollout \
  --model <model-id-or-path> \
  --vllm_tensor_parallel_size 2 \
  --vllm_data_parallel_size 1 \
  --port 8000

CUDA_VISIBLE_DEVICES=0,1,2,3 swift rlhf \
  --rlhf_type grpo \
  --model <model-id-or-path> \
  --dataset <dataset> \
  --use_vllm true \
  --vllm_mode server \
  --vllm_server_host 127.0.0.1 \
  --vllm_server_port 8000 \
  --reward_funcs <reward-name>
```

Server-mode checks:

- Use `--vllm_server_base_url http://host:port` instead of host/port pairs when that is simpler.
- For multi-turn/env training, set `--vllm_server_pass_dataset true` on the trainer so dataset columns such as `env_config` reach the rollout server.
- `async_generate true` improves throughput but uses the previous update's policy and does not support multi-turn scenarios.
- If vLLM errors with data-parallel-only async engine placement, try both TP and DP, or upgrade vLLM.
- `SWIFT_UPDATE_WEIGHTS_BUCKET_SIZE` controls flattened weight-sync bucket size in MB for full-parameter server-mode sync.

## Multi-Turn and Gym-Style GRPO

Use multi-turn rollout when each sample is a trajectory rather than a single completion. Register custom schedulers in an external plugin:

```python
from swift.rollout.multi_turn import MultiTurnScheduler, multi_turns

class ToolScheduler(MultiTurnScheduler):
    def step(self, infer_request, response_choice, current_turn):
        infer_request.messages.append({'role': 'user', 'content': 'next observation'})
        return {'infer_request': infer_request, 'rollout_infos': {'turn': current_turn}}

multi_turns['tool_scheduler'] = ToolScheduler
```

Use `--multi_turn_scheduler tool_scheduler --max_turns <n>` on `swift rollout` for server mode or on `swift rlhf` for colocate mode. The scheduler can return `response_token_ids`, `response_loss_mask`, and `rollout_logprobs` when it modifies response text or needs precise loss masking.

Use gym-style environments when the environment itself returns step rewards:

```python
from swift.rollout.gym_env import Env, envs

class MyEnv(Env):
    async def reset(self, config):
        return 'initial observation', {}, 'system prompt'
    async def step(self, messages):
        return 'next observation', 0.0, False, {}
    async def close(self):
        pass

envs['my_env'] = MyEnv
```

Launch with `--multi_turn_scheduler gym_scheduler --gym_env my_env --use_gym_env true`. In server mode, also pass `--vllm_server_pass_dataset true` to the trainer. The gym reward is appended as a reward column, so if you also pass `--reward_funcs`, provide `--reward_weights` for both plugin rewards and the gym total reward.

## GKD Patterns

Basic GKD with a local teacher:

```bash
swift rlhf \
  --rlhf_type gkd \
  --model <student-model> \
  --teacher_model <teacher-model> \
  --dataset <dataset> \
  --beta 0.5 \
  --lmbda 0.5 \
  --max_completion_length 512
```

GKD with external teacher logprobs:

```bash
swift rlhf \
  --rlhf_type gkd \
  --model <student-model> \
  --teacher_model_server http://localhost:8000 \
  --gkd_logits_topk 64 \
  --dataset <dataset>
```

GKD checks:

- `beta` interpolates between forward KL (`0.0`), symmetric JSD (`0.5`), and reverse KL (`1.0`).
- `lmbda` controls student on-policy generation probability. On-policy generation needs vLLM in Megatron GKD and is usually faster with an optimized rollout engine.
- `seq_kd true` means teacher-generated sequences conceptually, but Megatron GKD currently falls back to off-policy mode; pre-generate teacher responses when this is required.
- `gkd_logits_topk` reduces memory and is required with `teacher_model_server` because API logprobs are top-k.

## Sampling and RFT Data Generation

`swift sample` creates candidate completions and can filter them with PRM/ORM scoring:

```bash
swift sample \
  --model <model-id-or-path> \
  --sampler_engine vllm \
  --num_return_sequences 8 \
  --n_best_to_keep 2 \
  --dataset <dataset> \
  --orm_model math
```

For memory-limited PRM/ORM filtering, split sampling into two passes:

```bash
swift sample --model <model> --sampler_engine vllm --num_return_sequences 8 --dataset <dataset>
swift sample --sampler_engine no --cache_files <sample-output.jsonl> --dataset <same-dataset> --orm_model <orm-name>
```

Custom sampling PRM/ORM objects are also registered through plugins. For API distillation, use `--sampler_type distill --sampler_engine client --engine_kwargs '{"base_url":"..."}'` and provide credentials through environment variables, not skill content.

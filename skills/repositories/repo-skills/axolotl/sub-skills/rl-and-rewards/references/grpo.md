# GRPO, vLLM, and Async Online RL

GRPO in Axolotl generates completions online, scores them with reward functions or environment rewards, computes group-relative advantages, and updates the policy. Use it when the task has a verifiable reward signal such as math correctness, code tests, tool success, format compliance, or an external environment score.

## Minimal Config Shape

A GRPO run needs three pieces:

1. A config YAML with `rl: grpo`.
2. One or more importable reward functions or reward model identifiers in `trl.reward_funcs`.
3. A generation backend. For most Axolotl GRPO runs, use `axolotl vllm-serve config.yaml` plus `trl.use_vllm: true`.

Core YAML fields:

```yaml
rl: grpo
chat_template: tokenizer_default
adapter: lora

trl:
  use_vllm: true
  vllm_server_host: 0.0.0.0
  vllm_server_port: 8000
  vllm_server_timeout: 300
  vllm_lora_sync: true
  num_generations: 4
  max_completion_length: 512
  temperature: 0.7
  reward_funcs:
    - rewards.accuracy_reward
  reward_weights:
    - 1.0

vllm:
  host: 0.0.0.0
  port: 8000
  gpu_memory_utilization: 0.85
  max_model_len: 2048
```

Operational sequence:

```bash
axolotl vllm-serve config.yaml
axolotl train config.yaml
```

Use separate terminals or a process supervisor. The vLLM server must keep running for the full training run and must serve the same `base_model` as the trainer.

## Reward and Dataset Flow

- Dataset transforms for GRPO should produce a `prompt` field and keep any columns needed by rewards, such as `answer`, `metadata`, or test fixtures.
- Reward functions receive a batch of completions and may also receive dataset columns through keyword arguments.
- `reward_weights` must align one-to-one with `reward_funcs` when specified.
- For multiple reward signals with different scales, consider `multi_objective_aggregation: normalize_then_sum`; the default style sums first, then normalizes.
- `reward_num_workers` is useful when a reward depends on libraries that require a process main thread, such as math verification using alarms.

## vLLM Serving Choices

Server mode is the normal choice:

```yaml
trl:
  use_vllm: true
  vllm_mode: server
  vllm_server_host: 0.0.0.0
  vllm_server_port: 8000

vllm:
  host: 0.0.0.0
  port: 8000
  tensor_parallel_size: 1
```

Colocate mode can be used for small single-GPU experiments, but generation and training time-share the same device and are slower:

```yaml
trl:
  use_vllm: true
  vllm_mode: colocate
  vllm_enable_sleep_mode: true
```

For LoRA or QLoRA online RL, prefer `trl.vllm_lora_sync: true`. It syncs adapter weights to vLLM instead of repeatedly pushing merged full-model weights. Restart vLLM between experiments, after crashes, and whenever the base model changes; stale vLLM server state can make training appear to run while rewards never improve.

## Async Pipeline Features

Use async features when generation is the bottleneck and the setup can tolerate slightly stale rollout weights:

```yaml
trl:
  use_data_producer: true
  async_prefetch: true
  prefetch_depth: 1
  vllm_sync_interval: 3
  vllm_importance_sampling_correction: true
  importance_sampling_level: token
  off_policy_mask_threshold: 0.5
```

Important behavior:

- `use_data_producer: true` selects the data-producer path used by async GRPO and some integrations.
- `async_prefetch: true` generates the next rollout while training on the current rollout.
- `vllm_sync_interval` trades freshness for sync overhead; unset intervals behave like sync-every-step in async sync paths.
- Token-level importance sampling is the safer default with fused or chunked GRPO loss implementations.
- `streaming_partial_batch: true` scores prompt groups incrementally and can reduce peak memory.
- `skip_zero_advantage_batches: true` skips micro-batches where every completion in a group gets the same reward.
- `replay_buffer_size` caches high-signal rollout groups; keep `replay_recompute_logps: true` unless you intentionally accept stale log-probabilities.
- Deferred re-roll can reintroduce initially zero-signal prompts later with `reroll_start_fraction` and `reroll_max_groups`.

Do not combine async GRPO with sequence/context parallel settings that select sequence parallel GRPO; Axolotl rejects `sequence_parallel` plus async GRPO because those trainer paths are incompatible.

## NeMo Gym and Environment Rewards

Use NeMo Gym when rewards come from verified environments, multi-turn tool use, or `/verify` services. The plugin adds Axolotl config fields and reward functions rather than requiring custom reward code for the common paths.

Typical single-turn shape:

```yaml
rl: grpo
plugins:
  - axolotl.integrations.nemo_gym.NemoGymPlugin

trl:
  use_vllm: true
  reward_funcs:
    - axolotl.integrations.nemo_gym.rewards.reward_nemo_gym_verify

nemo_gym_enabled: true
nemo_gym_auto_start: false
nemo_gym_head_port: 11000
nemo_gym_datasets:
  - path: data/reasoning.jsonl
    server_name: reasoning_gym
```

Typical multi-turn shape:

```yaml
trl:
  use_vllm: true
  use_data_producer: true
  async_prefetch: true
  vllm_lora_sync: true
  reward_funcs:
    - axolotl.integrations.nemo_gym.rewards.reward_env

nemo_gym_multi_turn: true
nemo_gym_run_timeout: 300
```

Multi-turn mode delegates rollouts to an agent `/run` service and returns rollout tensors plus rewards to Axolotl. It still depends on matching the policy model served by vLLM and the model used by the trainer.

## Hatchery-Style RL Hooks

Hatchery-style configs use a nested `hatchery:` block for backend connection, sampling, remote loss, and optional reward functions:

```yaml
plugins:
  - axolotl.integrations.hatchery.HatcheryPlugin

hatchery:
  backend: tinker
  loss_fn: importance_sampling
  max_sample_tokens: 256
  sample_temperature: 1.0
  num_samples: 4
  reward_funcs:
    - rewards.score_completion
```

Treat remote backend keys, API keys, and project IDs as runtime secrets. Do not write credentials into reusable skill content, examples, logs, or review artifacts.

## Health Signals

During GRPO, look for:

- `rewards/*/mean` moving above a task-appropriate baseline after early steps.
- `reward_std` non-zero on most prompt groups; all-zero rewards mean no advantage signal.
- `entropy` not collapsing toward zero.
- `grad_norm` not exploding; zero can be normal when zero-advantage skips fire.
- vLLM health endpoint reachable before training starts and after any server restart.

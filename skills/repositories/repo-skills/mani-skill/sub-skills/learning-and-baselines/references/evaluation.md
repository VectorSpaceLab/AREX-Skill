# Evaluation

This reference captures the ManiSkill evaluation contract used across the RL and IL baseline docs.

## Fair evaluation contract

1. **Do not use partial resets.** Set `ignore_terminations=True` so episodes do not reset early on success/failure.
2. **Reconfigure on reset.** Use `reconfiguration_freq=1` for benchmark evaluation so randomized objects are re-sampled consistently.
3. **Record metrics.** Set `record_metrics=True` and read the `episode` metrics from `info` / `final_info`.
4. **Collect complete episodes only.** In vector evaluation, wait for `truncated` and then aggregate `final_info`.
5. **Match backend and control mode when fairness depends on it.** If training used a specific backend, say so instead of silently changing it at evaluation time.

## Recommended wrapper pattern

### GPU / vectorized evaluation

```python
import gymnasium as gym
from mani_skill.vector.wrappers.gymnasium import ManiSkillVectorEnv

env = gym.make(env_id, num_envs=num_eval_envs, reconfiguration_freq=1, **env_kwargs)
env = ManiSkillVectorEnv(env, ignore_terminations=True, record_metrics=True)
```

### CPU / vectorized evaluation

```python
import gymnasium as gym
from mani_skill.utils.wrappers import CPUGymWrapper

def make_env():
    env = gym.make(env_id, reconfiguration_freq=1, **env_kwargs)
    env = CPUGymWrapper(env, ignore_terminations=True, record_metrics=True)
    return env
```

## Metrics to watch

- `success_once` — the main success metric for demo-based baselines.
- `success_at_end` — useful when the task should still be solved at the final step.
- `fail_once` / `fail_at_end` — present on tasks with failure criteria.
- `return` — total episode reward.
- `episode_len` and `reward` — wrapper-side convenience metrics.

## `RecordEpisode`

- `RecordEpisode` supports both single and vectorized environments.
- For a single environment it can save videos and trajectories on reset.
- For vectorized environments use a fixed `max_steps_per_video` so video flushing is unambiguous.
- This wrapper is useful for evaluation rollouts and for saving benchmark videos, but it is not a substitute for the metric contract above.

## Common mistakes

- Using `env.render()` as the observation source. In ManiSkill, observations come from `reset()` and `step()`.
- Forgetting to read `final_info` after vector rollouts.
- Evaluating with a different backend, control mode, or demo source than the one used for training without calling out the mismatch.
- Reporting only return when the benchmark expects success-based metrics.
- Letting auto-reset behavior silently change the evaluation protocol.

## Family-specific notes

- For IL, `success_once` is usually the headline metric.
- For RL, the official docs also track reward/return and success/failure metrics together.
- TD-MPC2 checkpoints are particularly sensitive to `num_eval_envs` and `control_mode` matching the training setup.

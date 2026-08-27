# RLlib Workflows

These workflows favor config validation and tiny local runs before distributed training. They distill Ray RLlib documentation and source examples into self-contained patterns that avoid heavy Atari, MuJoCo, PettingZoo, or long PPO training unless explicitly requested.

## Install RLlib Narrowly

```bash
pip install "ray[rllib]" torch
```

Use this as the default RLlib install shape. `ray[rllib]` supplies RLlib dependencies such as Gymnasium; PyTorch is commonly required by PPO examples and the current default PPO stack. Add optional packages only for the target environment family:

- Atari: Gymnasium Atari extras, accepted ROM license support, and ROM assets.
- MuJoCo: MuJoCo-compatible Gymnasium extras and system/runtime dependencies.
- Box2D: Box2D-compatible Gymnasium extras and native build/runtime packages.
- PettingZoo: Multi-agent third-party environment dependencies.

Do not recommend `ray[all]` as a default installation path.

## Config-Only Validation

Use this before training, checkpointing, or launching Tune sweeps:

```python
from ray.rllib.algorithms.ppo import PPOConfig

config = (
    PPOConfig()
    .environment("CartPole-v1")
    .env_runners(num_env_runners=0)
    .training(train_batch_size_per_learner=128, minibatch_size=64, num_epochs=1)
)
config.validate()
```

This confirms the config object, builder chain, and many compatibility checks without collecting thousands of environment steps. For custom envs, instantiate the env once locally and call `reset()` and `step()` before `config.validate()`.

The bundled helper follows this model:

```bash
python scripts/rllib_config_smoke.py --validate
```

It imports RLlib, defines a tiny Gymnasium env, registers it through Tune, validates the PPO config, and exits without long training by default.

## Custom Gymnasium Env

A single-agent custom env must subclass `gymnasium.Env`, define spaces, and follow the Gymnasium tuple API:

```python
import gymnasium as gym
import numpy as np

class TinyCorridor(gym.Env):
    def __init__(self, config=None):
        config = config or {}
        self.end_pos = int(config.get("corridor_length", 5))
        self.cur_pos = 0
        self.observation_space = gym.spaces.Box(0.0, float(self.end_pos), (1,), np.float32)
        self.action_space = gym.spaces.Discrete(2)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.cur_pos = 0
        return np.array([self.cur_pos], dtype=np.float32), {}

    def step(self, action):
        if action == 1:
            self.cur_pos += 1
        elif self.cur_pos > 0:
            self.cur_pos -= 1
        terminated = self.cur_pos >= self.end_pos
        truncated = False
        reward = 1.0 if terminated else -0.1
        return np.array([self.cur_pos], dtype=np.float32), reward, terminated, truncated, {}
```

Sanity-check spaces and tuple shapes locally:

```python
env = TinyCorridor({"corridor_length": 3})
obs, info = env.reset(seed=0)
next_obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
assert env.observation_space.contains(obs)
assert env.observation_space.contains(next_obs)
assert env.action_space.contains(0)
```

## Register Custom Env For RLlib Workers

Due to Ray's distributed actor model, use Tune registration for custom env factories that remote EnvRunner actors must create:

```python
from ray.tune.registry import register_env
from ray.rllib.algorithms.ppo import PPOConfig

register_env("tiny_corridor", lambda env_config: TinyCorridor(env_config))

config = (
    PPOConfig()
    .environment("tiny_corridor", env_config={"corridor_length": 5})
    .env_runners(num_env_runners=0)
)
config.validate()
```

Use the env class directly only when the class is importable in the worker runtime and you do not need a factory. Prefer registration in examples meant to survive remote execution.

## PPO Build, Train, Evaluate, Checkpoint

Use a tiny iteration count first:

```python
from pprint import pprint
from ray.rllib.algorithms.ppo import PPOConfig

config = (
    PPOConfig()
    .environment("CartPole-v1")
    .env_runners(num_env_runners=0)
    .training(train_batch_size_per_learner=256, minibatch_size=64, num_epochs=1)
    .evaluation(
        evaluation_interval=1,
        evaluation_duration=1,
        evaluation_duration_unit="episodes",
        evaluation_num_env_runners=0,
    )
)

config.validate()
algo = config.build_algo()
try:
    result = algo.train()
    pprint(result)
    checkpoint_path = algo.save_to_path()
    print(checkpoint_path)
finally:
    algo.stop()
```

Increase `num_env_runners`, `train_batch_size_per_learner`, and evaluation duration only after a local smoke run succeeds. Keep `algo.stop()` in `finally` blocks so failed experiments release actors.

## EnvRunner And Learner Scaling

Start with correctness, then scale:

```python
config = (
    PPOConfig()
    .environment("CartPole-v1")
    .env_runners(
        num_env_runners=2,
        num_envs_per_env_runner=4,
        num_cpus_per_env_runner=1,
    )
    .learners(num_learners=0)  # local learner for small CPU jobs
)
```

Guidelines:

- `num_env_runners=0` keeps collection local and is useful for smoke tests.
- Increase `num_env_runners` to parallelize sampling across Ray actors.
- Increase `num_envs_per_env_runner` when vectorized inference improves throughput.
- Use `remote_worker_envs=True` only when individual sub-environments are expensive enough to justify extra process overhead.
- Multi-agent setups are not generally vectorizable in the same way as single-agent Gymnasium envs.
- Use `learners(...)` for larger training workloads; do not reserve GPUs unless the backend and cluster can satisfy them.

For generic Ray placement, resource labels, runtime envs, or blocked object refs, use `../core-runtime/SKILL.md`.

## Tune Sweep Integration

RLlib online algorithms can run as Tune trainables:

```python
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig

config = (
    PPOConfig()
    .environment("CartPole-v1")
    .env_runners(num_env_runners=0)
    .training(lr=tune.grid_search([1e-4, 5e-5]))
)

results = tune.Tuner(
    config.algo_class,
    param_space=config,
    tune_config=tune.TuneConfig(
        metric="env_runners/episode_return_mean",
        mode="max",
        num_samples=1,
        max_concurrent_trials=1,
    ),
    run_config=tune.RunConfig(stop={"training_iteration": 1}),
).fit()

best = results.get_best_result(metric="env_runners/episode_return_mean", mode="max")
print(best.config)
```

Tune notes:

- Each trial builds a separate RLlib Algorithm and needs enough CPUs/GPUs for its EnvRunners and Learners.
- Keep `max_concurrent_trials` low when each trial reserves workers.
- Stop criteria and best-result metrics must match keys that RLlib reports for the chosen run length and API stack.
- For generic Tune scheduler/searcher/storage details, use `../train-tune/SKILL.md`.

## Checkpoint Restore And Inference

For a running algorithm:

```python
module = algo.get_module()  # default policy/module
```

For a Tune-selected checkpoint, restore the module from the checkpoint's RLModule subtree and run batched inference:

```python
from pathlib import Path
import numpy as np
import torch
from ray.rllib.core.rl_module import RLModule

module = RLModule.from_checkpoint(
    Path(best_checkpoint.path) / "learner_group" / "learner" / "rl_module" / "default_policy"
)
obs, info = env.reset()
outputs = module.forward_inference({"obs": torch.from_numpy(obs).unsqueeze(0)})
params = outputs["action_dist_inputs"][0].detach().numpy()

action = int(np.argmax(params))  # discrete action space
```

For continuous action spaces, use the distribution parameters appropriate for the module output and clip the action to `env.action_space.low` and `env.action_space.high`.

## Multi-Agent And Offline Notes

For multi-agent workloads:

- Use RLlib multi-agent env interfaces and `.multi_agent(...)` policy/module mapping.
- Keep policy ids stable and serializable.
- Validate action and observation spaces for every policy mapping.
- Avoid vectorization assumptions from single-agent Gymnasium envs.

For offline RL workloads:

- Confirm the selected algorithm supports offline data and Tune integration.
- Use `.offline_data(...)` for RLlib-specific offline settings.
- Route generic Ray Data ingestion, transforms, and file IO to `../data-pipelines/SKILL.md`.

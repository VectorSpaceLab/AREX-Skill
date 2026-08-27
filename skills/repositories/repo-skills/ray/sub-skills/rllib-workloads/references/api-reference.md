# RLlib API Reference

This reference distills the RLlib `AlgorithmConfig` and `PPOConfig` surfaces used most often by agents configuring, validating, and running reinforcement-learning workloads. The repository evidence shows Ray's source version is in the Ray 3 development line while inspected installed APIs verified imports for `ray.rllib`, `PPOConfig(algo_class=None)`, and `AlgorithmConfig(algo_class=None)`.

## Core Objects

| Object | Use | Notes |
| --- | --- | --- |
| `AlgorithmConfig(algo_class=None)` | Base builder for RLlib algorithms. | Holds environment, training, EnvRunner, Learner, evaluation, checkpointing, offline-data, reporting, and multi-agent settings. |
| `PPOConfig(algo_class=None)` | PPO-specific `AlgorithmConfig`. | Defaults include `lr=5e-5`, `rollout_fragment_length="auto"`, `train_batch_size=4000`, and `num_env_runners=2`; many smoke checks override these lower. |
| `Algorithm` | Runtime object built from a config. | Owns EnvRunner/Learner workers, training loop, checkpoints, and modules; call `stop()` when finished. |
| `RLModule` | Policy/model module used for inference and checkpoint restore patterns. | Retrieve from an algorithm with `algo.get_module()` or restore module-only checkpoints for inference. |
| `EnvRunner` | Actor/process that samples experience from environments. | Scale with `env_runners(num_env_runners=..., num_envs_per_env_runner=...)`. |
| `Learner` / `LearnerGroup` | Learner workers that update model weights. | Scale with `learners(...)` for workloads large enough to need distributed learning. |

## Builder Lifecycle

1. Import an algorithm-specific config, usually `from ray.rllib.algorithms.ppo import PPOConfig`.
2. Chain config methods such as `.environment(...)`, `.env_runners(...)`, `.training(...)`, `.evaluation(...)`, and `.learners(...)`.
3. Call `config.validate()` for fast config and env-shape checks where possible.
4. Call `config.build_algo()` to create an `Algorithm`, or pass the config to Tune for trial execution.
5. Run short loops with `algo.train()`, inspect result dictionaries, save checkpoints with `algo.save_to_path()` or `algo.save()`, and always call `algo.stop()`.

`config.build()` appears in examples and source comments, but `build_algo()` is the explicit builder documented for the current API stack. Prefer `build_algo()` in new guidance unless matching an existing codebase that already uses `build()`.

## Common `AlgorithmConfig` Methods

| Method | Primary purpose | Common parameters and guidance |
| --- | --- | --- |
| `.environment(env, env_config=..., observation_space=..., action_space=..., disable_env_checking=...)` | Selects the RL environment. | Use a Gymnasium ID string, a `gymnasium.Env` subclass, or a Tune-registered name. Add spaces explicitly when RLlib cannot infer them. |
| `.env_runners(num_env_runners=..., num_envs_per_env_runner=..., remote_worker_envs=..., num_cpus_per_env_runner=..., num_gpus_per_env_runner=...)` | Scales sample collection. | Use `num_env_runners=0` for cheap local smoke checks. Increase actors and vectorized env copies only after correctness is proven. |
| `.learners(num_learners=..., num_cpus_per_learner=..., num_gpus_per_learner=...)` | Scales learning/update workers. | Keep local CPU smoke checks simple; add GPUs only when the selected algorithm/model and cluster can use them. |
| `.training(...)` | Sets generic and algorithm-specific training options. | For PPO, set `lr`, `gamma`, `train_batch_size_per_learner`, `num_epochs`, `minibatch_size`, clipping, entropy, KL, and model settings. |
| `.evaluation(evaluation_interval=..., evaluation_duration=..., evaluation_duration_unit=..., evaluation_num_env_runners=..., evaluation_config=...)` | Adds separate evaluation workers/settings. | Evaluation is off by default; keep durations small for tests and document metric keys used by Tune. |
| `.framework(framework="torch")` | Selects backend framework. | Current PPO new-stack defaults to PyTorch; TensorFlow support is limited or old-stack-dependent. |
| `.multi_agent(policies=..., policy_mapping_fn=..., policies_to_train=...)` | Configures multi-agent policy/module mapping. | Use stable policy ids and keep mapping functions serializable for workers. |
| `.offline_data(...)` | Configures offline RL input. | Offline algorithms may need additional Ray Data/Tune work; route generic data-pipeline issues to `../data-pipelines/SKILL.md`. |
| `.resources(...)` | Configures main process and placement behavior. | Prefer `env_runners(...)` and `learners(...)` for RLlib-specific scaling; use Core guidance for generic resource semantics. |
| `.reporting(...)` | Adjusts metric smoothing and reporting behavior. | Tune stop criteria must match reported metric paths. |
| `.checkpointing(...)` | Configures algorithm checkpoint behavior. | Tune checkpoint retention belongs mostly to Tune `RunConfig`/`CheckpointConfig`. |
| `.to_dict()` | Converts to a legacy config dictionary. | Useful for APIs expecting plain dicts; keep builder-object configs where supported. |
| `.copy()` / `.freeze()` | Copies or makes configs immutable. | Copy before mutating shared base configs for sweeps or evaluation overrides. |
| `.validate()` | Checks config consistency. | Run before expensive builds or sweeps; combine with tiny custom env checks. |

## PPOConfig Defaults And Training Knobs

Source defaults for PPO include:

- `lr = 5e-5`
- `rollout_fragment_length = "auto"`
- `train_batch_size = 4000`
- `num_env_runners = 2`
- `use_critic = True`, `use_gae = True`, `lambda_ = 1.0`
- `num_epochs = 30`, `minibatch_size = 128`, `shuffle_batch_per_epoch = True`
- `use_kl_loss = True`, `kl_coeff = 0.2`, `kl_target = 0.01`
- `entropy_coeff = 0.0`, `clip_param = 0.3`, `vf_clip_param = 10.0`

For smoke checks, override defaults to avoid accidental long jobs:

```python
config = (
    PPOConfig()
    .environment("CartPole-v1")
    .env_runners(num_env_runners=0)
    .training(train_batch_size_per_learner=128, minibatch_size=64, num_epochs=1)
)
config.validate()
```

## Environment Forms

| Form | Pattern | When to use |
| --- | --- | --- |
| Gymnasium ID | `.environment("CartPole-v1")` | Standard registered Farama Gymnasium envs available on every worker. |
| Env class | `.environment(MyEnv, env_config={...})` | Simple local scripts and tests where the class is importable by workers. |
| Tune-registered env | `register_env("name", lambda config: MyEnv(config)); .environment("name")` | Preferred for custom env factories in distributed RLlib runs because Ray actors need a serializable registry entry. |
| Multi-agent env | `.environment(MyMultiAgentEnv).multi_agent(...)` | Workloads with multiple agents and policy mapping. |
| Offline data | `.offline_data(...)` with offline algorithms | Batch/offline RL workflows; verify algorithm support before assuming Tune compatibility. |

Gymnasium single-agent envs must expose `observation_space` and `action_space`, return `(obs, info)` from `reset`, and return `(obs, reward, terminated, truncated, info)` from `step`.

## Tune Integration

Online RLlib algorithms can be used as Tune trainables. A common pattern is:

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
    tune_config=tune.TuneConfig(metric="env_runners/episode_return_mean", mode="max"),
    run_config=tune.RunConfig(stop={"training_iteration": 1}),
).fit()
```

Each Tune trial builds its own Algorithm, consumes its own resources, and reports RLlib metrics. If a metric path is unavailable for a short run, inspect one `algo.train()` result or a small Tune trial before setting production stop criteria.

## Checkpoints And Inference

- Use `algo.save_to_path()` or `algo.save()` to create an algorithm checkpoint after training.
- Use Tune `ResultGrid.get_best_result(...).checkpoint` to retrieve the selected trial checkpoint.
- For model-only inference, restore an `RLModule` from the checkpoint's module path and call `forward_inference({"obs": obs_batch})`.
- For an active algorithm, call `algo.get_module()` or `algo.get_module("default_policy")`.
- For discrete actions, use argmax over action logits. For continuous actions, select and clip continuous distribution parameters according to the environment action space.
- Stop active algorithms with `algo.stop()` to release Ray actors and worker resources.

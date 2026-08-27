# RLlib Troubleshooting

Use this matrix when RLlib imports, config validation, custom environments, PPO runs, Tune sweeps, or checkpoints fail. Prefer config-only validation before long training loops.

## Missing Dependencies

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: ray.rllib` | Installed Ray without RLlib extra. | Install `ray[rllib]`; keep extras narrow. |
| `ModuleNotFoundError: gymnasium` | RLlib/Gymnasium dependencies missing or mismatched. | Reinstall `ray[rllib]` in the active environment. |
| Torch import or PPO build failure | PPO default/new-stack examples commonly require PyTorch. | Install a compatible `torch`; choose CPU or CUDA build intentionally. |
| Atari/MuJoCo/Box2D/PettingZoo import errors | Optional env family not installed. | Add only the selected environment package extras and native dependencies; do not default to heavy extras. |
| Python version failure | Ray family requires Python `>=3.10`. | Use a supported Python version. |

## Custom Env Registration

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Env works locally but remote workers cannot create it | Env was registered only in Gymnasium's local registry or defined in a non-importable scope. | Use `ray.tune.registry.register_env("name", creator)` and `.environment("name")`; keep creator serializable. |
| `TypeError` constructing env | Env constructor does not accept the config argument RLlib passes. | Define `__init__(self, config=None)` or a Tune creator that adapts config. |
| Remote env has different behavior per worker unexpectedly | Env uses process-local globals, random seeds, or worker-specific config incorrectly. | Use the config object fields such as worker/vector indexes deliberately and seed in `reset(seed=...)`. |
| Logging from env is missing | Logging was configured before Ray workers started. | Configure logging inside worker/env code through Ray/RLlib loggers. |

## Gymnasium API Tuple Returns

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `reset` unpacking errors | Returning only `obs` instead of `(obs, info)`. | Return `return obs, {}`. |
| `step` unpacking errors | Old Gym API returns four values. | Return `(obs, reward, terminated, truncated, info)`. |
| Observation validation fails | Observation dtype/shape outside `observation_space`. | Use `env.observation_space.contains(obs)` in a local smoke test; set NumPy dtype explicitly. |
| Episode never ends | `terminated` and `truncated` are never true. | Add termination logic and bounded test steps. |

## Action And Observation Space Mismatch

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Algorithm rejects environment | Algorithm does not support the env's action space type. | Check algorithm compatibility with discrete vs continuous spaces; try a compatible algorithm or wrapper. |
| Policy output cannot be applied | Discrete/continuous inference handling is wrong. | Use argmax over logits for discrete spaces; clip continuous actions to the env space. |
| Env crashes after sampled action | `action_space` does not reflect what `step` accepts. | Assert `env.action_space.contains(action)` and adapt/wrap the env. |
| Multi-agent policy mismatch | Policy mapping returns a policy whose spaces do not match that agent. | Define per-policy spaces/specs and verify mapping for every agent id. |

Run `config.validate()` after setting `.environment(...)`, `.multi_agent(...)`, and major training settings. For difficult envs, instantiate and step the env locally before building the Algorithm.

## Algorithm And Env Compatibility

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| TensorFlow/new-stack error for PPO | Current PPO new-stack path expects PyTorch. | Use default PyTorch or explicitly set a supported framework. |
| Offline algorithm cannot run in Tune as expected | Offline RL algorithms may require additional Tune/Ray Data integration. | Verify algorithm support and route generic Data/Tune setup to the relevant sub-skills. |
| Multi-agent vectorization fails | Multi-agent setups are not generally vectorizable like single-agent Gymnasium envs. | Remove vectorization settings or use a supported multi-agent pattern. |
| Atari/MuJoCo env initialization fails | Missing system/display/assets/license requirements. | Install the specific env family requirements and use headless-compatible settings. |

## Expensive Training Or Hung Runs

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Smoke test takes too long | PPO defaults collect thousands of samples with multiple EnvRunners. | Set `num_env_runners=0`, small `train_batch_size_per_learner`, small `minibatch_size`, and `num_epochs=1`. |
| Tune launches too many actors | Each trial builds its own Algorithm with EnvRunners/Learners. | Reduce `max_concurrent_trials`, EnvRunners, Learners, and per-worker resources. |
| Ray reports insufficient CPUs/GPUs | Requested resources exceed local or cluster capacity. | Lower `num_env_runners`, `num_cpus_per_env_runner`, Learner resources, or Tune concurrency. |
| Training appears idle | Env reset/step blocks or remote workers are waiting on resources. | Reproduce with `num_env_runners=0`, add bounded env steps, then scale gradually. |

## Cleanup With `algo.stop()`

Always stop active algorithms:

```python
algo = config.build_algo()
try:
    result = algo.train()
finally:
    algo.stop()
```

If a script starts Ray explicitly, also call `ray.shutdown()` at process end. Leaked algorithms can leave actors alive, hold resources, and interfere with later Tune trials.

## Tune Metric And Resource Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `get_best_result` cannot find metric | Metric key does not exist for the run/API stack. | Inspect one result dictionary and use the exact key, such as `env_runners/episode_return_mean` when present. |
| Stop criterion never triggers | Stop key or threshold is wrong for reported RLlib metrics. | Use `training_iteration` for smoke tests; switch to reward metrics after verifying output. |
| Trial directories or checkpoints missing | RunConfig/checkpoint settings or storage path are wrong. | Use Tune guidance in `../train-tune/SKILL.md` for storage/checkpoint retention. |
| Trials run sequentially unexpectedly | Resource requests consume all available CPUs/GPUs. | Lower per-trial EnvRunner/Learner resources or increase cluster capacity. |

## Config-Only First Response Pattern

When debugging user code, ask for or construct a minimal repro that does not train for long:

```python
config = (
    PPOConfig()
    .environment(env_name_or_class, env_config=env_config)
    .env_runners(num_env_runners=0)
    .training(train_batch_size_per_learner=128, minibatch_size=64, num_epochs=1)
)
config.validate()
```

Only after this passes should the agent build an Algorithm, run one iteration, checkpoint, or launch a Tune sweep.

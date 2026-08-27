# Environment reference

This page summarizes the DI-engine environment layer that turns user envs into
collector/evaluator-ready objects.

## Core helpers

| Helper | Signature shape | Purpose |
| --- | --- | --- |
| `DingEnvWrapper` | `DingEnvWrapper(env=None, cfg=None, seed_api=True, caller='collector', is_gymnasium=False)` | normalize Gym/Gymnasium environments into DI-engine timesteps |
| `BaseEnvManager` | `BaseEnvManager(env_fn, cfg={})` | simple local environment manager |
| `BaseEnvManagerV2` | `BaseEnvManagerV2(env_fn, cfg={})` | newer manager used by many framework recipes |
| `EnvSupervisor` | `EnvSupervisor(type_=ChildType.PROCESS, env_fn=None, retry_type='reset', max_try=None, max_retry=None, auto_reset=True, reset_timeout=None, step_timeout=None, retry_waiting_time=None, episode_num=inf, shared_memory=True, copy_on_get=True, **kwargs)` | child-process or child-thread supervision |
| `create_env_manager` | `create_env_manager(manager_cfg, env_fn)` | build the configured manager backend |
| `get_vec_env_setting` | `get_vec_env_setting(cfg, collect=True, eval_=True)` | derive env factory callables plus collector/evaluator config lists |

## Wrapper behavior

`DingEnvWrapper` is the first stop for environment onboarding. It handles:

- observation and action normalization
- collector/evaluator config generation
- Gym vs Gymnasium compatibility
- random-action helpers
- replay saving for evaluation workflows

Important methods used throughout the repo include:

- `reset()`
- `step(action)`
- `random_action()`
- `create_collector_env_cfg(cfg)`
- `create_evaluator_env_cfg(cfg)`

## Representative environment families

Use these as the default examples when explaining how to add or debug a new env:

- `dizoo/classic_control/cartpole/`
- `dizoo/classic_control/pendulum/`
- `dizoo/classic_control/acrobot/`
- `dizoo/classic_control/mountain_car/`
- `dizoo/bitflip/`
- `dizoo/frozen_lake/`
- `dizoo/league_demo/`

## Environment-manager choices

- `BaseEnvManager` is the simplest local manager.
- `BaseEnvManagerV2` is the more common modern choice in the framework recipes.
- `EnvSupervisor` is useful when the workflow needs explicit restart, timeout,
  or child-type control.
- `SyncSubprocessEnvManager` and `AsyncSubprocessEnvManager` are useful when a
  subprocess-backed manager is needed.

## Onboarding pattern

1. Define or wrap the raw env class.
2. Register the env in the package's import surface.
3. Add a config pair under the chosen `dizoo/` family.
4. Verify the wrapper can reset, step, and sample random actions.
5. Route the new env into the training pipeline or framework recipe.

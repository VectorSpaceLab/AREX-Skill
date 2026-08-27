# Task registration reference

Evidence used: `humanoid/envs/__init__.py`, `humanoid/utils/task_registry.py`, `humanoid/envs/base/base_task.py`, and the README code-structure guidance.

## Registry contract

- `task_registry.register(name, task_class, env_cfg, train_cfg)` stores the task class and instantiated config objects.
- `get_cfgs(name)` returns the registered env/train configs and copies the training seed into the env config.
- `make_env(name, args=None, env_cfg=None)` resolves the registered task, applies CLI overrides, seeds RNG, parses sim parameters, and instantiates the environment class.
- `make_alg_runner(...)` belongs to the training/evaluation boundary; this sub-skill only needs the fact that the registered env/train pair must be valid when the runner later consumes it.

## Baseline registration

The shipped task map contains one public entry:

| Task id | Environment class | Env config | Train config |
|---|---|---|---|
| `humanoid_ppo` | `XBotLFreeEnv` | `XBotLCfg()` | `XBotLCfgPPO()` |

## Safe way to add a new robot or environment

1. Create a new config pair by subclassing `LeggedRobotCfg` and `LeggedRobotCfgPPO`.
2. Create a new env class by subclassing `LeggedRobot` or `XBotLFreeEnv` if you want the same reference-action and observation structure.
3. Register the new task under a new id, for example `task_registry.register("mybot_ppo", MyBotEnv, MyBotCfg(), MyBotCfgPPO())`.
4. Import the module that performs the registration so the call runs during package import.
5. Leave `humanoid_ppo` untouched. Treat it as the baseline contract consumed by the training/evaluation workflow.

## What usually breaks registration

- the new module is never imported, so the `register(...)` call never runs
- the task name is misspelled or still uses the default helper task id
- a mutable registered config object was edited in place after registration
- the new env class expects different joint/body names than the asset provides

## Minimal rule for reuse

If you want a second environment that shares XBot-L observations but changes terrain, rewards, or randomization, register a new task id instead of branching the baseline one in place. That keeps command-line lookup and checkpoint paths stable for `humanoid_ppo`.

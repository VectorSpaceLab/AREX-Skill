# High-Level Experiment Troubleshooting

Use this guide when high-level builders fail before training, create unexpected files, render unexpectedly, choose an unwanted device, or hide a lower-level Tianshou mismatch behind builder abstractions.

## Install and Import Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: tianshou` | Package is not installed in the active environment. | Install Tianshou and rerun a minimal `import tianshou; print(tianshou.__version__)` check. |
| `ModuleNotFoundError: gymnasium` or `torch` | Core runtime dependencies are missing or environment is mismatched. | Verify the active interpreter/package environment; do not leak local paths into generated instructions. |
| `AttributeError` for high-level modules | Older Tianshou version or stale code snippet. | Confirm version is Tianshou 2.0.1 and import from `tianshou.highlevel.*`. |
| `pip check`-style dependency conflicts | Mixed package versions. | Recreate or repair the environment before blaming builder code. |

## API-v2 Migration Confusion

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Builder constructor rejects old seed kwargs | Older examples or snippets passed `training_seed`/`test_seed` to env factories. | In Tianshou 2.0.1, prefer `ExperimentConfig(seed=...)`; `EnvFactoryRegistered` accepts Gymnasium creation kwargs and Tianshou seeds during environment creation. |
| User expects `policy`, `trainer`, or `collector` objects in the snippet | They are asking for procedural API internals. | Route to `../procedural-training/SKILL.md` unless a build-only high-level `Experiment` is enough. |
| `collection_step_num_env_steps` and `collection_step_num_episodes` both set | Training config invariant violation. | Set exactly one collection-count mode. For most high-level smokes, keep `collection_step_num_env_steps` and leave episodes as `None`. |
| `num_training_envs=-1` creates too many envs | Default expands to CPU count. | Set a small explicit count in examples and tests. |
| `Experiment.run()` errors on directory collision | Persistence run name already exists. | Use unique `.with_name(...)`, disable persistence for smokes, or intentionally call `run(..., raise_error_on_dirname_collision=False)` for resume-like flows. |

## Optional Environment Dependencies

High-level builders do not install optional Gymnasium environment families. They only wire Tianshou around whatever environments are importable and registered.

| Task family | Common failure | Fix |
| --- | --- | --- |
| Classic control, e.g. `CartPole-v1` | Usually available with Gymnasium basics. | Use for portable smoke tests. |
| MuJoCo | Missing `mujoco`/Gymnasium extras or system runtime issues. | Ask the user to install/verify MuJoCo support; route detailed env setup to envs-and-vectorization. |
| Atari | Missing Atari ROMs/wrappers/ale-py or preprocessing extras. | Do not run Atari high-level examples unless extras are installed; use them as conceptual references. |
| Box2D | Missing Box2D/SWIG dependencies. | Install the correct Gymnasium Box2D extras outside runtime skill content. |
| EnvPool | Missing `envpool` or incompatible task. | Use `VectorEnvType.DUMMY` unless the user intentionally selected EnvPool. |
| Ray | Missing Ray or process initialization limitations. | Avoid `VectorEnvType.RAY` for generated smokes. |

If `gymnasium.error.NameNotFound` or registration errors appear, first validate the task id with plain Gymnasium. If plain Gymnasium cannot create the env, the issue is outside high-level Tianshou wiring.

## Persistence, Logging, and Watch Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Unexpected `log/` directory appears | `persistence_enabled=True` is the default. | Set `ExperimentConfig(persistence_enabled=False)` for examples and checks. |
| `log.txt` is still expected but missing | `log_file_enabled=False` or persistence disabled. | Explain that file logs require persistence and `log_file_enabled=True`. |
| Run fails because a directory already exists | Same experiment name/run name with persistence enabled. | Use a unique name or disable persistence. |
| Headless display/render error after training | `watch=True` default created a watch env and rendered. | Set `watch=False`; only enable watch when display/render mode is available. |
| Watch env creation fails although training env works | `render_mode_watch="human"` may require support unavailable for the task or environment. | Set `watch=False` or provide compatible render settings. |
| Wandb/logger resume confusion | `logger_run_id` or logger factory state is wrong. | For simple scripts, use default logging and persistence disabled; customize loggers only on user request. |

## GPU Default Device Surprises

`ExperimentConfig.device` defaults to CUDA when PyTorch reports CUDA availability. This can surprise users in notebooks, shared GPU boxes, CI, or machines with a broken CUDA stack.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CUDA out-of-memory during a small example | Builder default selected GPU. | Set `ExperimentConfig(device="cpu", ...)` for debug/smoke runs. |
| Device mismatch between loaded policy and model | Restored policy directory was created under different assumptions or tensors move unexpectedly. | Pass the intended `device` explicitly and verify restore compatibility. |
| CUDA initialization error before training | PyTorch sees CUDA but runtime is unavailable. | Force CPU in `ExperimentConfig`; investigate CUDA separately. |

## Parameter Misconfiguration Symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| DQN on continuous action env fails | `DQNExperimentBuilder` expects discrete action spaces. | Use a continuous-control builder such as `SACExperimentBuilder`, `PPOExperimentBuilder`, `DDPGExperimentBuilder`, or `TD3ExperimentBuilder`. |
| SAC/PPO action scaling behaves oddly | Continuous actor output/bounding/scaling assumptions do not match environment. | Review `SACParams` action scaling and actor factory settings; route deep custom policy work to procedural. |
| No exploration and DQN does not learn | `eps_training=0.0` default is greedy. | Set a nonzero `eps_training` or DQN epsilon callback. |
| Target network has no effect | `target_update_freq=0` disables target-network updates for DQN-style params. | Use a positive update frequency when target-network stabilization is desired. |
| Training updates too many or too few times | Off-policy `update_step_num_gradient_steps_per_sample` misunderstood. | Remember gradient steps are approximately `round(value * collected_samples)`. |
| Early stop never triggers | Threshold too high, no test episodes, or callback uses `env.spec.reward_threshold` where none exists. | Provide an explicit threshold and ensure `num_test_envs`/`test_step_num_episodes` are positive. |
| Assertion about collection steps/episodes | Both or neither collection-count fields set. | Keep one of `collection_step_num_env_steps` or `collection_step_num_episodes`. |

## Workflow Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Build succeeds but `run()` fails during collector/trainer setup | Environment space, algorithm family, or training counts mismatch. | Run a small construction check first, then route to procedural/data-collection if low-level wiring is needed. |
| `build_and_run(num_experiments>1)` fails under parallel launcher | Launcher/process dependencies unavailable or object not serializable. | Use `launcher="sequential"` first; only parallelize after a single run succeeds. |
| Rliable analysis fails after multi-run | Analysis dependencies or display/filesystem assumptions missing. | Set `perform_rliable_analysis=False` for bounded runs. |
| Custom factory cannot be pickled/restored | High-level experiments are designed around serializable config/factory objects. | Keep factories lightweight and top-level; use procedural API for highly dynamic components. |
| A short smoke test takes too long | Counts copied from full examples. | Reduce `max_epochs`, `epoch_num_steps`, env counts, and disable watch/persistence; for construction checks, call `.build()` instead of `.run()`. |

## Minimal Debug Order

1. Confirm `import tianshou` and version are correct.
2. Confirm plain `gymnasium.make(task)` works for the task id and extras.
3. Build `EnvFactoryRegistered(..., VectorEnvType.DUMMY)` with `ExperimentConfig(device="cpu", persistence_enabled=False, log_file_enabled=False, watch=False)`.
4. Call `.build()` before `.run()`.
5. If `.build()` fails, fix builder/config/params names.
6. If `.run()` fails, reduce training counts and inspect whether the failure belongs to environment setup, data collection, trainer configuration, or custom factories.

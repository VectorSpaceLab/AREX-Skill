# Cross-Cutting Troubleshooting

## Import and Version Errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: tianshou` | Package is not installed in the active Python environment. | Install `tianshou`, then run `python -c "import tianshou; print(tianshou.__version__)"`. |
| Tianshou imports but examples fail with old parameter names | Code was written for pre-v2 APIs. | Route to `sub-skills/highlevel-experiments/SKILL.md` or `sub-skills/procedural-training/SKILL.md` and rewrite around v2 `Algorithm`/`Policy` separation. |
| High-level imports fail on evaluation modules | Evaluation dependencies such as `joblib`, `scipy`, `rliable`, or related packages are missing. | Install the documented evaluation extra or the narrow packages required for the requested evaluation path. |
| `pip check` reports dependency conflicts | Mixed package versions or broad extras changed dependency pins. | Resolve conflicts before running examples; avoid installing every optional extra unless required. |

## Optional Environment Backends

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| MuJoCo, Atari, Box2D, VizDoom, robotics, or EnvPool import errors | Optional environment engine is not installed. | Install only the needed extra and any external engine/assets; then route to `sub-skills/envs-and-vectorization/SKILL.md`. |
| `SubprocVectorEnv` works differently from `DummyVectorEnv` | Env factory captures non-picklable state or relies on fork-only globals. | Use top-level importable factories/classes and validate with the env vectorization smoke before training. |
| PettingZoo mask/action errors | Observation/action spaces differ across agents, or masks are not routed to the policy. | Validate `PettingZooEnv` output contract, then route policy and collector handling to the env/data/procedural sub-skills. |
| Headless render or display errors | Watch/render enabled in a non-GUI environment. | Disable watch/render for smokes; enable rendering only in an environment with display support. |

## Data and Collector Issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Batch` slicing or concatenation fails | Inconsistent leading dimensions, object arrays of tensors, or missing nested keys. | Route to `sub-skills/data-collection/SKILL.md`; normalize shapes and validate with the bundled data smoke. |
| Replay buffer samples malformed batches | Required rollout keys are absent or vector buffers are incorrectly sized. | Confirm `obs`, `act`, `rew`, termination/truncation, `obs_next`, and `info` fields; use `VectorReplayBuffer` for vector envs. |
| Collector never stops or collects wrong counts | Mixed `n_step`/`n_episode` expectations or reset state confusion. | Use one stopping mode at a time and reset before first collection. |
| NaNs appear in buffer or losses | Env emits invalid observations/rewards, model output is unstable, or hooks mutate batches. | Enable collector/buffer validation where available, isolate env smoke, and reduce update counts. |

## API Misuse

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Discrete policy receives continuous action space | Algorithm/policy does not match Gymnasium action space. | Re-select algorithm family: DQN-style for discrete, SAC/DDPG/TD3/PPO variants for continuous as appropriate. |
| Continuous actions exceed environment bounds | `action_scaling` or `action_bound_method` is missing/mismatched. | Check policy params and actor output range in `sub-skills/procedural-training/SKILL.md`. |
| High-level experiment unexpectedly writes logs | Persistence/logging defaults were not overridden. | Use `ExperimentConfig(persistence_enabled=False, log_file_enabled=False, watch=False)` for smokes. |
| Training is unexpectedly long | Default epoch/env counts are too large for a smoke. | Override epoch, step, env, batch, and buffer settings to tiny values first. |

## Evaluation and Benchmark Safety

- Do not run benchmark scripts as smoke tests.
- Reduce multi-seed plans to one tiny env and one seed before enabling `JoblibExpLauncher`.
- Use rliable analysis only after experiment directories contain comparable logged results.
- Keep dataset downloads and benchmark output directories explicit.

See `references/evaluation-and-benchmarks.md` and `sub-skills/offline-and-specialized-rl/SKILL.md` for evaluation-specific guidance.

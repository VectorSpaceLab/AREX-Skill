# Offline and Specialized RL Troubleshooting

Use this page before starting long offline training, imitation learning, multi-agent runs, or benchmark/evaluation jobs.

## Install And Import Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: numpy`, `torch`, or `gymnasium` while importing Tianshou | Running outside an environment with the package and core dependencies installed. | Activate/install a valid Tianshou environment, then rerun the smoke helper. Do not document local environment paths in runtime output. |
| `ModuleNotFoundError: joblib`, `rliable`, `scipy`, or plotting packages from `tianshou.evaluation` | Evaluation extras are optional. | Install only the evaluation extras needed for the request, or skip evaluation imports and use algorithm-only smoke checks. |
| `ModuleNotFoundError: d4rl`, Atari/ALE, MuJoCo, EnvPool, PettingZoo, robotics, or VizDoom | Dataset/environment examples rely on optional engines. | Avoid downloading/launching optional datasets by default. Use a tiny local buffer or route environment setup to `../envs-and-vectorization/SKILL.md`. |
| Top-level algorithm import works but a deeper class import fails | Some helpers are not exported from `tianshou.algorithm`. | Import from the owning module, such as `tianshou.algorithm.imitation.bcq.BCQPolicy` or `tianshou.algorithm.modelbased.psrl.PSRLPolicy`. |

## Offline Dataset And Buffer Schema

| Check | Why it matters | Failure mode |
| --- | --- | --- |
| All arrays have identical leading length | Offline updates sample aligned transitions. | Shape mismatch, bad samples, or silent wrong transitions. |
| Required keys exist: `obs`, `act`, `rew`, terminal flags, `obs_next` | Offline algorithms compute TD targets from next observations and terminal masks. | Missing attribute errors or invalid returns. |
| `act` matches action space | Continuous algorithms expect action vectors; discrete algorithms expect integer action ids. | Critic/action gather failures, discriminator shape errors, or invalid env evaluation. |
| Values are finite | Offline algorithms are sensitive to NaNs/Infs in fixed data. | Exploding losses, NaN buffers, or meaningless evaluation. |
| `done`, `terminated`, and `truncated` semantics are consistent | Tianshou accepts done-style data but Gymnasium splits termination/truncation. | Incorrect bootstrap targets around episode boundaries. |
| Expert buffer matches policy buffer for GAIL | Discriminator compares expert and policy state-action pairs. | Concatenation dimension errors or discriminator learning a schema artifact. |

For buffer creation, slicing, HDF5 loading, pickle loading, vector buffers, or collector-created buffers, use `../data-collection/SKILL.md`.

## Algorithm Configuration Misuse

| Area | Common mistake | Fix |
| --- | --- | --- |
| `CQL` | `min_action`/`max_action` do not match normalized action assumptions. | Confirm whether policy output is normalized and whether action scaling is enabled. |
| `BCQ` | `VAE`, perturbation actor, and critic disagree on observation/action dimensions. | Validate one forward pass with a small batch before training. |
| `TD3BC` | Actor outputs already-scaled actions but policy/action scaling is configured inconsistently. | Align policy scaling with the environment action space; see `../procedural-training/SKILL.md`. |
| `DiscreteBCQ` | `target_update_freq=0` or `unlikely_action_threshold` outside `[0, 1)`. | Use a positive target update frequency and validate the threshold. |
| `DiscreteCQL` | Model output does not match `num_quantiles` and action count. | Validate `QRDQNPolicy` output shape before constructing the trainer. |
| `DiscreteCRR` | Shared actor/critic nets are wired with incompatible last sizes. | Check actor logits and critic Q-values both have one value per action. |
| `GAIL` | Discriminator output has the wrong shape or policy actor lacks known output dimension. | Use a discriminator ending in one unbounded logit and a Tianshou actor that exposes output dimension. |
| `ICM` | Action space is continuous or `obs_next` is missing. | Use ICM with discrete action dimensions and full transition batches. |
| `PSRL` | Observations are continuous vectors instead of discrete state ids. | Use PSRL only for tabular integer-state MDPs. |
| MARL | Batch lacks `obs.agent_id` or legal-action mask location differs. | Fix PettingZoo wrapper/action-mask plumbing in `../envs-and-vectorization/SKILL.md`. |

## Trainer And Workflow Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Offline trainer tries to collect training data | Confused offline training with off-policy online training. | Use `OfflineTrainerParams(buffer=..., test_collector=...)`; general trainer wiring belongs to `../procedural-training/SKILL.md`. |
| Evaluation collector fails after offline training starts | Test env action space or observation schema differs from the offline buffer. | Validate env spaces against policy and buffer before training. |
| GAIL run is unexpectedly slow | GAIL is on-policy and still collects environment rollouts while sampling an expert buffer. | Reduce env counts, epoch/step counts, and discriminator updates for smoke tests. |
| ICM reward scale overwhelms learning | `reward_scale` is too large for the environment reward magnitude. | Start with a small scale and inspect wrapped stats (`icm_loss`, forward/inverse loss). |
| PSRL appears to ignore batch size | PSRL updates posterior statistics from collected transitions and does not use gradient mini-batches. | Set trainer parameters for collection cadence, not gradient repeat behavior. |

## Evaluation, Joblib, And Rliable

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Joblib uses too many cores | `JoblibConfig.n_jobs=-1` uses all CPUs. | Set `JoblibConfig(n_jobs=1)` or `n_jobs=2` for bounded checks. |
| Joblib backend setting is ignored | `JoblibExpLauncher` forces `loky`. | Expect `loky` or use sequential launcher for debugging. |
| Rliable loader finds no data | Experiment directory lacks restorable logger data or test/train scopes. | Confirm experiments completed and persisted logs; use high-level experiment guidance for persistence. |
| Plot display blocks an agent run | `show_plots=True` in a non-interactive session. | Set `show_plots=False`; optionally set `save_plots=False` for smoke tests. |
| JSON aggregation misses algorithms | Expected `rliable_evaluation_test.json` files are absent. | Run rliable evaluation on each experiment directory before aggregation. |

## Benchmark-Scale Safety

The benchmark orchestration utility can discover many scripts, launch tmux sessions, run Atari/MuJoCo tasks, and aggregate rliable outputs. Treat it as reference-only unless the user explicitly asks for benchmark execution.

Before running anything benchmark-like, require all of these reductions:

- One benchmark type and one task.
- `num_experiments=1` until a single run succeeds.
- `max_scripts=1` and `max_tasks=1` for first validation.
- Low `max_epochs` and `epoch_num_steps` overrides.
- `max_concurrent_sessions=1` or another explicitly bounded value.
- Explicit output/persistence directory and cleanup plan.

If any optional engine, dataset, tmux, or logging dependency is unavailable, report the missing capability and offer a smaller API/import/schema validation instead of trying to repair the whole benchmark stack.

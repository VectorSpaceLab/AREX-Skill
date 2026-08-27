---
name: environment-utils
description: "Use PARL environment wrappers, replay buffers, schedulers, CSV
  logging, and summary helpers safely across Gym, continuous-control, Atari,
  MuJoCo, multi-agent, and vector-env workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PARL environment utilities

Use this sub-skill when a task involves PARL's environment wrappers or small utilities around an RL loop: Gym API compatibility, continuous action remapping, Atari/MuJoCo/multi-agent/vector environment wrappers, `ReplayMemory`, schedulers, `CSVLogger`, `logger`, `summary`, `tensorboard`, or `visualdl` helpers.

Do not use this sub-skill to choose a full algorithm, implement a `parl.Model`/`parl.Agent`, or manage xparl workers. Route adjacent tasks to sibling operating skills:

- `../core-framework/SKILL.md` for backend selection, `Model`/`Algorithm`/`Agent`, save/restore, inference export, and weight synchronization.
- `../algorithm-recipes/SKILL.md` for DQN/DDPG/TD3/SAC/PPO/QMIX/MADDPG/A2C/IMPALA/CQL/OAC recipes and training-loop structure.
- `../xparl-distributed/SKILL.md` for `@parl.remote_class`, `parl.connect`, `xparl start`, remote environments, ports, and cluster security.

## Operating workflow

1. **Normalize the environment API first.** For ordinary Gym environments, wrap with `CompatWrapper` before calling code that expects the old four-return `step` API. Then add workflow-specific wrappers such as `ActionMappingWrapper`, `wrap_deepmind`, `wrap_rms`, `MAenv`, or `VectorEnv`.
2. **Choose wrappers by action/observation surface.** Use `ActionMappingWrapper` only when the environment action space is a continuous `Box`; use Atari wrappers only for Atari-like image/action-meaning environments; use MuJoCo RMS wrappers for continuous-control normalization; use multi-agent wrappers only when the PettingZoo or legacy multiagent dependency stack is intentionally installed.
3. **Check data utility shapes before training.** Configure `ReplayMemory(max_size, obs_dim, act_dim)` from the actual observation and action dimensions. For discrete actions pass `act_dim=0`; for continuous actions pass a positive integer action dimension.
4. **Keep logging output explicit.** Set a deliberate `logger.set_dir(...)` before writing summaries, or create `CSVLogger` with an explicit file path in a scratch/output directory. Avoid accidental deletion from logger helpers when a directory already exists.
5. **Smoke-test utilities safely.** Run the bundled checker before adapting examples:

   ```bash
   python scripts/check_env_utils.py --json
   ```

   Add `--optional-wrappers` to classify optional Atari, MuJoCo, and multi-agent imports without creating real environments.
6. **Escalate by symptom.** For wrapper/data-flow behavior, read `references/wrappers-and-data.md`; for logging and schedulers, read `references/logging-and-schedulers.md`; for failures, read `references/troubleshooting.md`.

## Verification status

The utility signatures for `CompatWrapper`, `ActionMappingWrapper`, `VectorEnv`, `ReplayMemory`, `PiecewiseScheduler`, `LinearDecayScheduler`, and `CSVLogger` were checked against an installed PARL 2.2.1 package. Small scheduler, replay-memory, CSV, vector-env, and action-mapping behaviors are covered by the bundled checker. Atari, MuJoCo, PettingZoo multi-agent, TensorBoard, and VisualDL flows are optional dependency surfaces and should be rechecked in the user's target environment before use.

## Reference map

- `references/wrappers-and-data.md` — Gym compatibility, action mapping, vector envs, Atari/MuJoCo/multi-agent wrappers, replay-memory contracts, and small NumPy RL helpers.
- `references/logging-and-schedulers.md` — schedulers, CSV output, PARL logger directories, summary/TensorBoard/VisualDL behavior, and file-write safety.
- `references/troubleshooting.md` — common fixes for Gym API mismatches, optional dependencies, action/replay shapes, logger deletion, CSV key mismatches, and summary backends.
- `scripts/check_env_utils.py` — deterministic local checker for safe imports, signatures, and tiny pure-Python utility exercises.

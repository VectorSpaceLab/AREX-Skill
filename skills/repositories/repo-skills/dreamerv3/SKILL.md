---
name: dreamerv3
description: "Use DreamerV3 for world-model reinforcement learning training,
  embodied environment dataflow, JAX model internals, result operations, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DreamerV3 Repo Skill

Use this skill when a task involves DreamerV3, the `dreamer` Python distribution,
its `dreamerv3` training entry point, or the bundled `embodied` RL runtime. The
repository implements DreamerV3 world-model reinforcement learning with a
fixed-hyperparameter training CLI, JAX/Ninjax model internals, environment
adapters, replay/dataflow utilities, and result/log plotting helpers.

## Start here

1. Check that the installed package is importable and the intended JAX backend is
   visible:

   ```bash
   python scripts/check_dreamerv3_install.py --backend cpu
   python scripts/check_dreamerv3_install.py --backend auto --json
   ```

2. Pick the closest route below. Read only the sub-skill needed for the task,
   then follow its linked references and bundled scripts.
3. If the current checkout or package version may differ from this skill, read
   [references/repo-provenance.md](references/repo-provenance.md) before relying
   on version-sensitive details.
4. For cross-cutting setup or failure triage, read
   [references/troubleshooting.md](references/troubleshooting.md).

## Route map

| User task | Read this |
| --- | --- |
| Compose a training command, choose `--configs`, run a bounded debug smoke, resume/evaluate a checkpoint, or pick `train`, `train_eval`, `eval_only`, or `parallel` | [sub-skills/train-configure/SKILL.md](sub-skills/train-configure/SKILL.md) |
| Implement or debug an `embodied.Env`, `Driver`, replay buffer, stream, wrapper chain, built-in env adapter, or custom dataflow contract | [sub-skills/embodied-dataflow/SKILL.md](sub-skills/embodied-dataflow/SKILL.md) |
| Inspect or modify `dreamerv3.agent.Agent`, RSSM, encoder/decoder, JAX setup, Ninjax state, heads/outputs, losses, optimizers, sharding, dtype, or numerics | [sub-skills/jax-models/SKILL.md](sub-skills/jax-models/SKILL.md) |
| Install DreamerV3, reason about CUDA/Docker/optional suite dependencies, inspect logdirs, summarize metrics/scores, use Scope/TensorBoard/W&B, or triage operational failures | [sub-skills/results-ops/SKILL.md](sub-skills/results-ops/SKILL.md) |

## Minimal install and import facts

- Public repository: `danijar/dreamerv3`.
- Python requirement from README: Python 3.11+.
- Distribution name from package metadata: `dreamer`.
- Import roots: `dreamerv3` and `embodied`.
- Package version captured for this skill: `3.3.1`.
- Base runtime requirements include JAX CUDA 12 packages, `elements`, `ninjax`,
  `optax`, `portal`, `scope`, `ale_py`, `autorom`, `av`, and NumPy `<2`.
- Several environment suites are optional in practice: DMC/Loconav need
  `dm_control`; Crafter needs `crafter`; DMLab needs `deepmind_lab`; Minecraft
  needs MineRL and Java; ProcGen needs `procgen`; Gym/Memory Maze need their
  respective packages.

A minimal import check should succeed before any larger run:

```python
import dreamerv3
import embodied
from embodied.envs import dummy
```

For JAX-only debugging, prefer an explicit CPU platform first:

```bash
JAX_PLATFORM_NAME=cpu python scripts/check_dreamerv3_install.py --backend cpu
```

## Common operating decisions

- Use `debug` and `dummy_disc` for fast installation, config, replay, logging,
  and JAX sanity checks. Do not expect learning quality from the debug preset.
- Use real task presets such as `crafter`, `atari`, `dmc_vision`, `dmc_proprio`,
  `dmlab`, `minecraft`, or `procgen` only after optional suite dependencies are
  installed and the backend is appropriate.
- Reuse a `--logdir` only when continuing a compatible run. Changing size
  presets, RSSM dimensions, head bins, action/observation spaces, or major model
  config usually requires a fresh logdir or selective checkpoint restore.
- Treat CUDA as a production-performance backend, not a substitute for fixing a
  failing CPU debug smoke. First make the debug CPU route work, then scale up.
- Original repository tests and examples are verification evidence. Runtime
  workflows in this generated skill use bundled references/scripts instead of
  requiring future agents to open source files from a checkout.

## Bundled root references and scripts

- [references/repo-provenance.md](references/repo-provenance.md): source commit,
  package version, dirty-state baseline, and evidence paths.
- [references/troubleshooting.md](references/troubleshooting.md): cross-cutting
  install/import/JAX/config/task/logdir triage and sub-skill routing.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json):
  structured scenario placement for managed router import.
- [scripts/check_dreamerv3_install.py](scripts/check_dreamerv3_install.py): safe
  package/JAX/config/dummy-env smoke checker.

## Do not use this skill for

- Generic RL theory questions that do not involve DreamerV3, world models, or the
  `embodied` runtime.
- Editing an unrelated reinforcement-learning library such as Stable-Baselines3,
  CleanRL, Tianshou, PettingZoo, or Gymnasium.
- Full benchmark reproduction claims without running the required environment,
  seed, hardware, and duration-specific experiments.
- Tasks that require private datasets, credentials, cloud accounts, or long
  training jobs without explicit user approval.

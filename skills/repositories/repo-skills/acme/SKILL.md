---
name: acme
description: "Route Acme reinforcement-learning framework tasks across core
  loops, replay/data, JAX agents, and TensorFlow/Sonnet agents."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Acme Repo Skill

Use this repo skill when a user asks about DeepMind Acme (`dm-acme`), Acme-style reinforcement-learning agents, `dm_env` loops, Reverb adders, Acme JAX experiments, or Acme TensorFlow/Sonnet agents.

## Start Here

- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a current checkout or should be refreshed.
- Read [references/package-overview.md](references/package-overview.md) for install extras, public dependency groups, repository capability map, and optional-backend expectations.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, optional dependency, backend, and example-runtime failures.
- Run `python scripts/check_acme_skill_runtime.py --help` for a bundled, dependency-light helper that explains package import checks and available sub-skill helper scripts.

## Route By Task

- **Core loops/specs/wrappers:** use [sub-skills/core-workflows/SKILL.md](sub-skills/core-workflows/SKILL.md) for `dm_env` specs, `Actor`/`Learner`, `EnvironmentLoop`, wrappers, loggers, counters, observers, and simple custom loop debugging.
- **Replay and data:** use [sub-skills/replay-and-data/SKILL.md](sub-skills/replay-and-data/SKILL.md) for `Adder` contracts, Reverb adders, replay tables, dataset iterators, TFDS/offline data, and transition/sequence/episode shape decisions.
- **JAX agents:** use [sub-skills/jax-agents/SKILL.md](sub-skills/jax-agents/SKILL.md) for Acme JAX algorithms, `acme.jax.experiments`, Haiku/Optax/RLax networks, online/offline/distributed JAX workflows, and JAX multiagent examples.
- **TensorFlow agents:** use [sub-skills/tf-agents/SKILL.md](sub-skills/tf-agents/SKILL.md) for Acme TensorFlow/Sonnet algorithms, TF losses, TF savers/snapshotters, Launchpad TF examples, and TF learner debugging.

## Install Baseline

- Distribution name: `dm-acme`; import package: `acme`; snapshot version: `0.4.1`.
- Minimal package metadata lists core requirements: `absl-py`, `dm-env`, `dm-tree`, `numpy`, `pillow`, and `typing-extensions`.
- Real agent execution usually needs optional extras: `dm-acme[jax]` for JAX agents, `dm-acme[tf]` for TensorFlow/Reverb/Launchpad agents, and `dm-acme[envs]` for example environments.
- Treat optional extras as backend/runtime choices, not as always-required imports. Many examples require Gym, bsuite, Control Suite, Atari ROMs, OpenSpiel, Reverb servers, Launchpad launch modes, or long training budgets.

## Minimal Import Check

```bash
python - <<'PY'
import acme
from acme import specs
print(acme.__version__)
print(specs.Array((2,), float))
PY
```

If this fails with `ModuleNotFoundError` for `jax`, `tensorflow`, `reverb`, `launchpad`, `gym`, `bsuite`, or environment packages, read [references/troubleshooting.md](references/troubleshooting.md) before broadening installs.

## Skill Boundaries

- This skill is for using, adapting, troubleshooting, and explaining Acme as an RL framework; it is not a benchmark reproduction plan and does not verify long training results.
- Do not route generic RL theory questions here unless the task names Acme APIs, Acme examples, or Acme-style builders/adders/loops.
- Do not tell future agents to open or run original repository files. This skill distills the repo evidence into bundled references and scripts.
- For source drift, compare current commit, dirty state, package metadata, and evidence paths with [references/repo-provenance.md](references/repo-provenance.md), then run `refresh-repo-skill` if they differ.

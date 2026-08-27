# Acme Package Overview

## Purpose

Read this for Acme's package identity, dependency groups, capability map, and how the generated sub-skills divide public workflows.

## Package Identity

- Public project name in prose: Acme.
- Distribution: `dm-acme`.
- Import package: `acme`.
- Snapshot version: `0.4.1`.
- Core install requirements from package metadata: `absl-py`, `dm-env`, `dm-tree`, `numpy`, `pillow`, and `typing-extensions`.

## Optional Dependency Groups

| Extra | Main purpose | Important packages | Use when |
| --- | --- | --- | --- |
| `jax` | JAX agents and experiments | `jax`, `jaxlib`, `chex`, `dm-haiku`, `flax`, `optax`, `rlax`, plus TF/Reverb/Launchpad stack | Running or debugging `acme.agents.jax` and `acme.jax.experiments` workflows |
| `tf` | TensorFlow/Sonnet agents | `tensorflow`, `tensorflow_probability`, `tensorflow_datasets`, `dm-reverb`, `dm-launchpad`, `dm-sonnet`, `trfl` | Running `acme.agents.tf`, Launchpad examples, Reverb-backed TF agents, or TF savers |
| `envs` | Example environments | `atari-py`, `bsuite`, `dm-control`, `gym`, `pygame`, `rlds` | Running repo examples that instantiate Gym, bsuite, Control Suite, Atari, or RLDS inputs |
| `testing` | Developer test tools | `pytype`, `pytest-xdist` | Repository development and selected test execution, not normal Acme usage |

The snapshot metadata pins several older backend versions. If modern indexes cannot satisfy those exact pins, decide whether the user needs historical reproducibility, source inspection, or a modernized runtime, then document the trade-off.

## Capability Map

| Capability | Owner | Evidence distilled |
| --- | --- | --- |
| `dm_env` specs, core `Actor`/`Learner`, `EnvironmentLoop`, wrappers, loggers, counters, observers | `sub-skills/core-workflows` | Overview/components docs, `acme/core.py`, `acme/specs.py`, `acme/environment_loop.py`, wrappers/utils tests |
| Adders, Reverb replay, datasets, offline iterators, data structure choices | `sub-skills/replay-and-data` | Components docs, `acme/adders`, `acme/datasets`, Reverb utility tests, offline examples |
| JAX online/offline/distributed agents and experiment configs | `sub-skills/jax-agents` | Agent docs, JAX agent READMEs, `acme/jax/experiments`, JAX examples/tests |
| TensorFlow/Sonnet agents, TF networks/losses/savers, Launchpad TF examples | `sub-skills/tf-agents` | Components/agent docs, TF agent READMEs, `acme/tf`, TF examples/tests |

## Runtime Expectations

- Acme examples are research examples, not tiny smoke tests. Many default to hundreds of thousands or millions of environment steps.
- Distributed examples use Launchpad; local debugging usually starts with local single-process runs or Launchpad `local_mt`/`local_mp` modes.
- Reverb-backed agents need a Reverb server/table and matching adder/dataset signatures.
- Atari and Control Suite examples may need ROMs, MuJoCo/control-suite dependencies, display/GL libraries, or other system setup.

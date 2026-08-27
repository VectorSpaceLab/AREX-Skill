---
name: dreamerv2
description: "Use DreamerV2 2.2.0 for TensorFlow world-model
  reinforcement-learning training, custom Gym integration, typed experiment
  configuration, replay/checkpoint management, and JSONL/TensorBoard
  evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DreamerV2

Use this skill for the `danijar/dreamerv2` 2.2.0 package: discrete world-model
reinforcement learning with TensorFlow, native Atari/DM Control/Crafter runners,
custom legacy Gym environments, typed configuration, replay/checkpoints, and
experiment plots. Treat this as a TensorFlow 2.6-era package, not a current
Gymnasium or modern-Keras package.

## Route the task

- **Launch, bound, resume, or diagnose a run:** read
  [training](sub-skills/training/SKILL.md).
- **Adapt an environment or validate observations/actions:** read
  [environments](sub-skills/environments/SKILL.md).
- **Compose presets, flags, schedules, or serialized configs:** read
  [configuration](sub-skills/configuration/SKILL.md).
- **Inspect metrics, TensorBoard artifacts, or compare runs:** read
  [evaluation](sub-skills/evaluation/SKILL.md).

Read only the route needed for the request, then follow its linked references.
The sub-skills are one operating graph: a training request commonly visits
configuration first, environments for the data contract, and evaluation after
artifacts exist.

## Install a compatible runtime

The verified package facts are distribution `dreamerv2==2.2.0`, import modules
`dreamerv2` and `dreamerv2.api`, and console entry point `dreamerv2`. This source
release uses `tensorflow.keras.mixed_precision.experimental` and the legacy Gym
API. Prefer a fresh Python 3.9 environment with a coherent era stack:

```sh
python -m pip install \
  'tensorflow==2.6.0' 'tensorflow-probability==0.14.1' \
  'gym==0.23.1' 'ruamel.yaml<0.18' \
  'numpy==1.19.5' 'pillow<10' 'pandas<2' 'matplotlib<3.8'
python -m pip install --no-deps 'dreamerv2==2.2.0'
```

Add only the suites you will use: `atari_py` plus imported Atari ROMs for
Atari, a compatible `dm_control`/MuJoCo/EGL setup for DMC, `crafter` for
Crafter, and the environment's own package for custom Gym. Do not download
ROMs, MuJoCo assets, or credentials as an unattended smoke check. Read
[troubleshooting](references/troubleshooting.md) before mixing newer TensorFlow,
TensorFlow Probability, Gym/Gymnasium, or NumPy versions.

Check the installation without starting training:

```sh
python -m pip check
python - <<'PY'
import inspect
import tensorflow as tf
import dreamerv2.api as dv2
print('TensorFlow', tf.__version__)
print('GPUs', tf.config.list_physical_devices('GPU'))
print('api.train', inspect.signature(dv2.train))
print('default task', dv2.defaults.task)
PY
python -m dreamerv2.train --help
```

The module help route is verified. Do **not** use the installed `dreamerv2`
launcher in this release: `train.py` derives `configs.yaml` from
`sys.argv[0]`, so the launcher may search beside its bin script and fail with a
missing-config error. Use `python -m dreamerv2.train` instead. The plotting
route is available through the evaluation sub-skill's bundled adapter.

## Operating rules

- Native `python -m dreamerv2.train` asserts that TensorFlow sees a GPU; a CPU
  import or `debug` preset does not make native training CPU-safe.
- Use a new writable `logdir` per run. The effective `config.yaml`, replay
  episodes, `metrics.jsonl`, TensorBoard events, and `variables.pkl` are the
  observable outputs; a checkpoint alone is not a successful experiment.
- Validate one environment reset/step and its action/observation contract
  before allocating training. Keep `--envs_parallel none` for this snapshot
  unless the asynchronous branch has been patched and tested.
- Make `debug` the last preset, set a bounded `--steps`, and explicitly choose
  `--precision 32` when the legacy mixed-precision path is not verified.
- Preserve exact package/runtime versions and effective config with results.
  For refresh decisions, read [repository provenance](references/repo-provenance.md).

## Scope and limits

This graph distills public package behavior and safe operational recipes. It
does not run benchmark-scale training, fetch external assets, import the skill
into the managed repo library, or claim that a modern unpinned dependency set
is compatible. Use [cross-cutting troubleshooting](references/troubleshooting.md)
for install/import, backend, dependency, and source-version failures before
escalating to the focused route.

---
name: rex-gym
description: "Operate the legacy Rex-Gym quadruped reinforcement-learning
  package for PyBullet environments, kinematics and gait modeling, PPO training
  setup, and packaged policy playback."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Rex-Gym operating skill

Use this skill when a task involves the `rex_gym` package, Rex/SpotMicro
quadruped simulation, PyBullet Gym environments, inverse kinematics, Bezier
walking/galloping, motor models, legacy PPO training, or shipped policy
checkpoints.

## Route the request

- Use [simulation-environments](sub-skills/simulation-environments/SKILL.md) for
  environment construction, task/signal/terrain/mark selection, reset/step,
  observations, rewards, termination, and headless or GUI simulation.
- Use [locomotion-modeling](sub-skills/locomotion-modeling/SKILL.md) for
  `Kinematics`, `GaitPlanner`, pose/frame ordering, motor constants, and torque
  conversion.
- Use [training-policy](sub-skills/training-policy/SKILL.md) for `rex-gym
  train`, `rex-gym policy`, PPO configuration, agent counts, log directories,
  policy ids, checkpoints, and TensorFlow compatibility.

Read [troubleshooting](references/troubleshooting.md) first when installation,
legacy dependencies, package data, or a runtime error is involved. Read
[repository provenance](references/repo-provenance.md) before deciding whether
this graph matches a changed checkout. Run the shared [package inspector](scripts/inspect_rex_gym.py)
for a no-training import, CLI, mapping, and deterministic-kinematics check; use
[troubleshooting](references/troubleshooting.md) for cross-cutting failures.

## Install and establish the compatibility family

The public distribution is `rex_gym`, imported as `rex_gym`, and exposes the
`rex-gym` console command:

```bash
python -m pip install rex_gym
python -c "import rex_gym; print('rex_gym import ok')"
rex-gym --help
```

For the pinned repository behavior, prefer an isolated Python 3.7 environment
with NumPy 1.17.3, PyBullet 2.8.3, Gym 0.17.1, TensorFlow 1.15.5,
TensorFlow Probability 0.8, `ruamel.yaml`, and Click. Modern pip reports an
upstream metadata conflict between Gym 0.17.1's `cloudpickle` range and TFP
0.8's exact pin; do not casually upgrade this legacy family. TensorFlow 1.15
also needs a protobuf 3.20.x-or-earlier runtime on modern installations. See
the training route for the optional PPO surface and the troubleshooting
reference for recovery.

## Choose a safe execution mode

Prefer headless PyBullet (`render=False`) and a bounded step count on servers,
CI, and first checks. Use the simulation smoke helper for a deterministic
package/API check; it supplies `terrain_id` explicitly and always closes the
environment. Do not start full training or policy playback merely to test an
import. GUI playback and playground training require a display and can run
until the environment ends.

The legacy environment API is `reset()` followed by `step(action)` returning
`(observation, reward, done, info)`, not the newer terminated/truncated pair.
Use task-specific action spaces, and expect `info["action"]` to contain the
transformed motor command. Always close environments in `finally` blocks.

## Scope and non-goals

This graph covers the public simulation and learning tools in Rex-Gym. It does
not operate physical hardware, replace `rexctl`, validate sim-to-real transfer,
claim policy quality, or prescribe long PPO experiments without an explicit
bounded run plan. Large TensorFlow checkpoint binaries remain package data;
inspect their catalog and sidecars rather than copying them into this skill.

The source package is legacy and has no dedicated repository test suite or
examples tree. The bundled routes and scripts therefore combine documented
workflows, source-backed API facts, live import checks, and bounded synthetic
smokes. Use the verification artifacts only as construction evidence; they are
not runtime dependencies.

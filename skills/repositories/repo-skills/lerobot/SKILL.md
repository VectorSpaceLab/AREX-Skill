---
name: lerobot
description: "Route LeRobot robotics workflows for datasets, policies, training,
  evaluation, simulation, physical robot control, and package extensions with
  verified configuration and safety gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LeRobot

Use this repo skill when a task uses LeRobot, `lerobot-*` commands,
`LeRobotDataset`, robot-learning policies, robot/camera/motor control, or the
LeRobot plugin and service interfaces. It is an operating guide for a later
Researcher: inspect and plan first, then execute only the requested bounded
workflow. Do not treat a package import or CLI help check as proof that a
specific robot, simulator, model checkpoint, codec, or CUDA policy is runnable.

## First gates

1. Record the package version, Python version (LeRobot 0.6.2 requires Python
   3.12+), source of data/checkpoint, device/backend, optional extras, output
   location, time/compute budget, and whether network, credentials, simulator
   assets, or physical actuation are authorized.
2. Prefer a private environment and the smallest feature extra. Install the
   public package with `pip install lerobot` and add only the documented extra
   for the chosen route (`dataset`, `training`, `hardware`, `viz`, a policy,
   an environment, or a service). Do not use `lerobot[all]` as a first fix.
3. Run `lerobot-info` or the bundled [environment probe](scripts/check_environment.py)
   before deeper work. A minimal import is:

   ```python
   import lerobot
   from lerobot.datasets.lerobot_dataset import LeRobotDataset
   print(lerobot.__version__)
   ```

4. Keep local, deterministic checks separate from Hub downloads, remote jobs,
   W&B logging, model downloads, simulator asset acquisition, long training,
   and hardware commands. Ask for explicit consent before those side effects.
5. If the repository checkout or package version differs from the snapshot in
   [repo-provenance.md](references/repo-provenance.md), refresh this skill
   before relying on version-sensitive instructions.

## Route the request

- **Dataset files, episodes, features, Parquet/MP4, streaming, stats,
  transforms, visualization, conversion, or dataset edits:** read
  [dataset-workflows](sub-skills/dataset-workflows/SKILL.md).
- **Policy type/checkpoint, processors, device placement, training,
  evaluation, inference, PEFT, or rollout planning:** read
  [policy-training-inference](sub-skills/policy-training-inference/SKILL.md).
- **Robot, motor, camera, teleoperator, calibration, serial/CAN, teleoperation,
  recording, replay, or physical deployment:** read
  [robot-control-data-collection](sub-skills/robot-control-data-collection/SKILL.md)
  and require its safety gates.
- **Gymnasium environment, LIBERO/MetaWorld/PushT/RobotWin/VLABench/RoboCasa,
  HIL-SERL, RL, or reward model:** read
  [simulation-and-rl](sub-skills/simulation-and-rl/SKILL.md).
- **Custom policy/processor/plugin, async inference, gRPC transport,
  annotation, HF Jobs, or service endpoint:** read
  [extensions-and-services](sub-skills/extensions-and-services/SKILL.md).

For a multi-stage task, load the dataset route before policy training, and
load the policy route before physical rollout. Cross-route handoffs must name
validated feature shapes/statistics, device, checkpoint, environment, and
side-effect approvals; never assume a preceding route proved them.

## Cross-cutting failure rules

Use [quick-reference.md](references/quick-reference.md) for terminology,
extra selection, and backend boundaries. Use
[troubleshooting.md](references/troubleshooting.md) when installation/import,
optional dependencies, configuration, codecs, Hub/network, CUDA, or a CLI
fails. Run [validate_skill_links.py](scripts/validate_skill_links.py) only when
checking this skill tree itself; it must report no external runtime links.

Stop and report `blocked` rather than guessing when a required dataset field,
checkpoint processor, simulator asset, optional package, GPU backend, camera,
serial/CAN device, credential, or safety control is unavailable. A CPU import
may validate CPU packaging but cannot validate GPU-only or physical behavior.

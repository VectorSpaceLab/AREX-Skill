---
name: "trajectories-and-datasets"
description: "Record ManiSkill episodes, replay and convert HDF5 trajectories,
  manage demos/assets, and plan motion-planning or teleoperation data
  workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Trajectories and Datasets

Use this sub-skill from the `mani-skill` root when the task is about recorded
ManiSkill data: collecting episodes, downloading demonstration or asset bundles,
replaying HDF5 trajectories, converting trajectories, loading trajectory data in
Python, running motion-planning data generation examples, or collecting
teleoperation demonstrations.

Route away from this sub-skill when the request is mainly about:

- General environment creation, observation modes, vectorization, rendering, or
  controller use: load `../environment-usage/`.
- Writing or changing task definitions, assets, rewards, registration, or custom
  scenes: load `../custom-environments/`.
- RL/IL baseline training loops, evaluation sweeps, or benchmark hyperparameters:
  use the learning/baseline sub-skill instead.

## Fast routes

| User need | Use |
|---|---|
| Record episodes from an already-created environment | `RecordEpisode`; see [CLI/API notes](references/cli-api-notes.md#recordepisode-wrapper). |
| Understand `.h5`/`.json` trajectory bundles | [data layout](references/data-layout.md). |
| Validate a trajectory bundle before doing anything expensive | `python scripts/inspect_trajectory_bundle.py PATH/trajectory.h5`. |
| Plan a replay command without running replay | `python scripts/plan_replay_command.py PATH/trajectory.h5 ...`. |
| Download official demos or required assets | [download planning](references/workflows.md#download-official-demos-or-assets) and `python scripts/preview_download_options.py`. |
| Replay demonstrations to add observations/rewards/videos or convert control modes | [replay workflows](references/workflows.md#replay-or-reprocess-trajectories). |
| Convert ManiSkill trajectories to LeRobot format | [LeRobot conversion](references/workflows.md#convert-to-lerobot-format) and `python scripts/plan_lerobot_conversion.py`. |
| Load data with PyTorch | `ManiSkillTrajectoryDataset`; see [CLI/API notes](references/cli-api-notes.md#maniskilltrajectorydataset). |
| Generate data from built-in motion-planning examples | [motion-planning workflow](references/workflows.md#motion-planning-generated-data). |
| Collect click+drag teleoperation data | [teleoperation workflow](references/workflows.md#teleoperation-generated-data). |
| Diagnose failed replay, conversion, recording, downloads, or display issues | [troubleshooting](references/troubleshooting.md). |

## Core operating rules

1. Treat a ManiSkill trajectory as a paired bundle: a `.h5` file plus a sibling
   `.json` file with the same stem. Replay, dataset loading, and LeRobot
   conversion all rely on the JSON metadata.
2. Prefer source metadata over filename guesses. File names commonly encode
   `<obs_mode>.<control_mode>.<sim_backend>`, but the JSON `env_info` and each
   episode's `control_mode`, `reset_kwargs`, and `info` are authoritative.
3. Never launch networked downloads, long replays, full conversions, or GUI
   teleoperation without explicit user intent. Use the bundled planning scripts
   first when the next action is unclear.
4. Control-mode conversion is limited and robot/controller dependent. Panda
   trajectories are the best-supported path; GPU-parallel replay does not
   support converting to a different control mode.
5. Use `source_type` and `source_desc` when recording new demos so future agents
   can distinguish motion-planning, teleoperation, RL-policy, or other sources.
6. Keep training-policy details out of this sub-skill. This sub-skill prepares
   data; it does not teach imitation or reinforcement learning baselines.

## Minimal recipes

### Record a trajectory bundle

```python
from mani_skill.utils.wrappers.record import RecordEpisode

env = RecordEpisode(
    env,
    output_dir="demos/PickCube-v1/manual-check",
    trajectory_name="trajectory",
    save_trajectory=True,
    save_video=False,
    source_type="manual",
    source_desc="short human-readable collection note",
)
```

Close the wrapper to flush metadata, then validate the bundle:

```bash
python scripts/inspect_trajectory_bundle.py demos/PickCube-v1/manual-check/trajectory.h5
```

### Replay or reprocess a bundle

```bash
python -m mani_skill.trajectory.replay_trajectory \
  --traj-path demos/PickCube-v1/teleop/trajectory.h5 \
  --save-traj -o state -c pd_joint_delta_pos
```

For exact visual/state reproduction, prefer `--use-env-states`; for CPU-to-GPU
or GPU-to-CPU replay attempts, consider `--use-first-env-state` and keep the
original backend available when precision matters.

### Convert to LeRobot format

```bash
python scripts/plan_lerobot_conversion.py \
  demos/PickCube-v1/teleop/trajectory.h5 \
  converted/pickcube_lerobot
```

The planner only prints the command and dependency status. Run the printed
`python -m mani_skill.trajectory.convert_to_lerobot ...` command only after the
user confirms the conversion and output directory.

## Bundled references and scripts

- [workflows](references/workflows.md): end-to-end recording, download, replay,
  conversion, motion-planning, and teleoperation flows.
- [CLI/API notes](references/cli-api-notes.md): signatures, options, and module
  entry points for `RecordEpisode`, replay, converter, downloader, dataset, and
  generation examples.
- [data layout](references/data-layout.md): HDF5/JSON schema, replay naming,
  LeRobot output shape, dataset-loader behavior, and trajectory utilities.
- [troubleshooting](references/troubleshooting.md): concrete fixes for missing
  pairs, conversion limits, optional dependencies, download prompts, video
  recording, and display issues.
- `scripts/inspect_trajectory_bundle.py`: safe HDF5/JSON bundle validator.
- `scripts/plan_replay_command.py`: safe replay-command planner.
- `scripts/plan_lerobot_conversion.py`: safe LeRobot conversion-command planner
  and dependency checker.
- `scripts/preview_download_options.py`: safe demo/asset UID and command planner;
  it does not download anything.

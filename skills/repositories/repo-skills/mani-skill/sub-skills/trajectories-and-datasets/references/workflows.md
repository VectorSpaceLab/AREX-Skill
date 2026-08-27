# ManiSkill trajectory and dataset workflows

This reference gives future agents concrete, self-contained data workflows. It
uses package module entry points rather than source-checkout paths.

## Workflow selection

| Goal | Use this workflow | Stop or route elsewhere when |
|---|---|---|
| Record your own episodes | `RecordEpisode` wrapper around an existing env | The user needs help creating the env itself: route to `../../environment-usage/`. |
| Fetch official demonstrations | `python -m mani_skill.utils.download_demo` | The user has not approved network/download cost. |
| Fetch assets or scene data | `python -m mani_skill.utils.download_asset` | The asset is large, prompts would remove existing data, or network is unavailable. |
| Reprocess raw demos | `python -m mani_skill.trajectory.replay_trajectory` | The `.json` pair is missing or the requested control conversion is unsupported. |
| Convert to LeRobot | `python -m mani_skill.trajectory.convert_to_lerobot` | Optional converter dependencies or the `.json` pair are missing. |
| Generate demonstrations by planners | `python -m mani_skill.examples.motionplanning.<robot>.run` | The target task/robot has no maintained solution or the run requires unapproved GUI/rendering. |
| Collect click+drag demos | `python -m mani_skill.examples.teleoperation.interactive_<robot>` | No display/mouse/keyboard is available. |

## Record with `RecordEpisode`

Use `RecordEpisode` when an environment already exists and the task is to save
transitions, metadata, and optionally videos.

```python
from mani_skill.utils.wrappers.record import RecordEpisode

env = RecordEpisode(
    env,
    output_dir="demos/PickCube-v1/my_source",
    trajectory_name="trajectory",
    save_trajectory=True,
    save_video=False,
    save_on_reset=True,
    record_reward=True,
    record_env_state=True,
    source_type="teleoperation",     # or motionplanning, RL, scripted, manual, etc.
    source_desc="click+drag teleop session with a human operator",
)
```

Operating notes:

- A named run creates `trajectory.h5` and `trajectory.json` under `output_dir`.
  If `trajectory_name` is omitted, a timestamp is used.
- `save_on_reset=True` automatically flushes the previous episode when the env
  resets. Set it to `False` when the outer collection loop controls flushing.
- `record_env_state=True` is useful for later exact replay, backend migration,
  or observation regeneration.
- `save_video=True` calls the environment renderer. GPU-parallel videos need a
  fixed `max_steps_per_video` because partial resets make video cutting
  ambiguous.

Validate the resulting pair before replay or conversion:

```bash
python scripts/inspect_trajectory_bundle.py demos/PickCube-v1/my_source/trajectory.h5
```

## Download official demos or assets

Official demos and assets are networked workflows. Use list/preview commands
first, then ask the user before running a download.

Safe list/preview:

```bash
python -m mani_skill.utils.download_demo
python -m mani_skill.utils.download_asset --list scene
python scripts/preview_download_options.py --kind both --category scene --limit 20
```

Download after explicit approval:

```bash
python -m mani_skill.utils.download_demo PickCube-v1
python -m mani_skill.utils.download_demo PickCube-v1 -o demos_cache
python -m mani_skill.utils.download_asset ReplicaCAD -y -o asset_cache
```

Important details:

- `download_demo` with no UID lists known demo datasets; `all` downloads every
  known demo and can be slow/large.
- `download_asset --list <category>` lists asset IDs in categories such as
  `scene`, `robot`, `task_assets`, and `objects`.
- `download_asset` may prompt to create directories or remove existing targets.
  Use `-y/--non-interactive` only when the user accepts those side effects.
- Downloaded official demonstrations are often raw/minimized and may omit
  observations and rewards until replayed.

## Replay or reprocess trajectories

Use replay to view demonstrations, regenerate observations/rewards/videos, or
produce a dataset in a new observation/control/backend configuration.

View or video without rewriting the source trajectory:

```bash
python -m mani_skill.trajectory.replay_trajectory \
  --traj-path demos/PickCube-v1/teleop/trajectory.h5 --vis

python -m mani_skill.trajectory.replay_trajectory \
  --traj-path demos/PickCube-v1/teleop/trajectory.h5 --save-video
```

Replay and save a new trajectory with observations and a target controller:

```bash
python -m mani_skill.trajectory.replay_trajectory \
  --traj-path demos/PickCube-v1/teleop/trajectory.h5 \
  --save-traj -o state -c pd_joint_delta_pos
```

Add rewards and RGB observations while forcing state-based replay:

```bash
python -m mani_skill.trajectory.replay_trajectory \
  --traj-path demos/PickCube-v1/teleop/trajectory.h5 \
  --save-traj --record-rewards --reward-mode normalized_dense \
  -o rgb --use-env-states
```

CPU/GPU migration pattern:

```bash
python -m mani_skill.trajectory.replay_trajectory \
  --traj-path demos/PickCube-v1/teleop/trajectory.h5 \
  --save-traj --use-first-env-state -b physx_cuda \
  -o state -c pd_joint_delta_pos -n 8
```

Before emitting a command for a user, run the safe planner:

```bash
python scripts/plan_replay_command.py \
  demos/PickCube-v1/teleop/trajectory.h5 \
  --save-traj -o state -c pd_joint_delta_pos -b physx_cpu
```

Replay caveats:

- The current replay CLI uses `--num-envs`/`-n` for parallel replay. Some older
  prose examples may call this `--num-procs`; prefer the installed CLI help.
- Conversion between control modes is not supported in GPU-parallel replay.
- `--use-env-states` is for exact state/observation reproduction and cannot be
  combined with a different target control mode.
- High-precision or non-quasi-static tasks may need `--use-env-states` to avoid
  small simulation divergence.

## Convert to LeRobot format

The LeRobot converter reads a ManiSkill `.h5` plus sibling `.json`, writes
parquet data, metadata, statistics, and optional videos.

Plan first:

```bash
python scripts/plan_lerobot_conversion.py \
  demos/PickCube-v1/teleop/trajectory.h5 converted/pickcube_lerobot \
  --task-name "Pick up the red cube" --fps 30 --image-size 640x480
```

Run after approval and dependency checks:

```bash
python -m mani_skill.trajectory.convert_to_lerobot \
  --traj-path demos/PickCube-v1/teleop/trajectory.h5 \
  --output-dir converted/pickcube_lerobot \
  --task-name "Pick up the red cube" \
  --fps 30 --image-size 640x480 --chunks-size 1000 --robot-type panda
```

Dependency expectations:

- The converter imports `pandas` at module import time, so even help can fail if
  pandas is missing.
- It writes parquet through `pyarrow` during conversion. Installing the full
  `lerobot` package is an alternative route because it brings useful dataset
  tooling, but the converter entry point itself is ManiSkill's module.
- Image/video export uses OpenCV. If `cv2` import or video writer creation
  fails, treat it as a conversion-environment issue rather than a trajectory
  problem.

## Motion-planning generated data

Built-in motion-planning examples generate demonstration trajectories for a
limited set of tasks/robots. Always use `-h` first to inspect the installed
options and supported tasks.

Panda examples:

```bash
python -m mani_skill.examples.motionplanning.panda.run -h
python -m mani_skill.examples.motionplanning.panda.run -e PickCube-v1 --save-video
python -m mani_skill.examples.motionplanning.panda.run -e StackCube-v1 --vis
```

Other robot families have separate installed modules, for example:

```bash
python -m mani_skill.examples.motionplanning.so100.run -h
python -m mani_skill.examples.motionplanning.xarm6.run -h
```

Important details:

- The Panda runner exposes maintained solution IDs such as `PickCube-v1`,
  `StackCube-v1`, `PegInsertionSide-v1`, `PlugCharger-v1`, `PushCube-v1`,
  `PullCube-v1`, `PullCubeTool-v1`, `LiftPegUpright-v1`, `DrawTriangle-v1`,
  `DrawSVG-v1`, `PlaceSphere-v1`, and `StackPyramid-v1`.
- Motion-planning examples record with `source_type="motionplanning"` and a
  contributor-authored `source_desc`.
- The maintained runner writes to `<record_dir>/<env_id>/motionplanning/` by
  default, not necessarily the folder order shown in older docs.
- `--num-procs` on the motion-planning runner uses CPU multiprocessing and then
  merges per-worker trajectory files. Avoid it unless the user accepts the
  extra CPU/process and file-merging work.
- Planners may fail to find a solution for some seeds; `--only-count-success`
  keeps generating until the requested number of successful trajectories is
  saved.

## Teleoperation generated data

The click+drag teleoperation examples are interactive and require a display,
mouse, and keyboard.

```bash
python -m mani_skill.examples.teleoperation.interactive_panda -e StackCube-v1
python -m mani_skill.examples.teleoperation.interactive_so100 -e PickCube-v1
python -m mani_skill.examples.teleoperation.interactive_xarm6 -e PickCube-v1
```

Common keyboard flow:

- `h`: print help.
- Drag the end-effector ghost in the viewer.
- `n`: motion-plan to the current target pose.
- `g`: toggle gripper open/closed when the robot has a gripper.
- `c`: finish the current episode, save it, and continue to a new one.
- `q`: quit and close/save the trajectory bundle.

Important details:

- Default teleop output is `<record_dir>/<env_id>/teleop/trajectory.h5` plus the
  matching JSON metadata.
- The first collection pass records trajectories. When `--save-video` is used,
  the script performs a second pass over recorded env states to render videos.
- Teleop demos are often CPU/display oriented. If a later ML workflow needs GPU
  simulation, replay the saved data into the GPU backend and keep failures
  visible rather than assuming exact transfer.

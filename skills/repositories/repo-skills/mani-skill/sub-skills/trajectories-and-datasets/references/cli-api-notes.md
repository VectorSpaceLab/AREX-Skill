# CLI and API notes

Use these notes for concrete entry points and signatures. For general env
creation or controller semantics, route to `../../environment-usage/`.

## `RecordEpisode` wrapper

Import path:

```python
from mani_skill.utils.wrappers.record import RecordEpisode
```

Installed constructor shape:

```python
RecordEpisode(
    env,
    output_dir,
    save_trajectory=True,
    trajectory_name=None,
    save_video=True,
    info_on_video=False,
    save_on_reset=True,
    save_video_trigger=None,
    max_steps_per_video=None,
    clean_on_close=True,
    record_reward=True,
    record_env_state=True,
    video_fps=30,
    render_substeps=False,
    avoid_overwriting_video=False,
    source_type=None,
    source_desc=None,
)
```

Operational meaning of key arguments:

- `output_dir`: destination directory for the trajectory pair and optional
  videos. Created when trajectory or video saving is enabled.
- `trajectory_name`: stem of `<trajectory_name>.h5` and `<trajectory_name>.json`;
  defaults to a timestamp.
- `save_on_reset`: flush the current episode when `reset()` starts a new one.
  Use `False` when an explicit collection loop calls `flush_trajectory()`.
- `record_env_state`: save state dictionaries under `env_states`; keep enabled
  when exact replay or backend migration is a future need.
- `record_reward`: include per-step `rewards` in the HDF5 group.
- `save_video`, `video_fps`, `info_on_video`, `render_substeps`: control video
  generation. Video rendering uses the env's render mode/backend.
- `max_steps_per_video`: mandatory when recording video from GPU-parallel
  environments with more than one env; otherwise partial resets make video
  boundaries ambiguous.
- `source_type`/`source_desc`: embed provenance such as `motionplanning`,
  `teleoperation`, `RL`, or a human-readable source note in the JSON metadata.

## `mani_skill.trajectory.replay_trajectory`

Help:

```bash
python -m mani_skill.trajectory.replay_trajectory -h
```

Important options:

| Option | Purpose |
|---|---|
| `--traj-path PATH` | Required `.h5` trajectory file. The sibling `.json` must exist. |
| `-b`, `--sim-backend` | Override backend; if omitted, replay uses metadata or defaults to CPU. |
| `-o`, `--obs-mode` | Observation mode to record in the replayed trajectory. |
| `-c`, `--target-control-mode` | Target control mode for action conversion. |
| `--save-traj` | Save a new trajectory; the source file is not overwritten. |
| `--save-video` | Save videos through `RecordEpisode`. |
| `--vis` | Render live in the GUI. |
| `--use-env-states` | Set env state at every step for exact state/observation replay. |
| `--use-first-env-state` | Set only the initial state, useful for CPU/GPU backend migration attempts. |
| `--count N` | Replay only the first `N` demos. |
| `--record-rewards`, `--reward-mode MODE` | Add rewards to the replayed trajectory. |
| `--render-mode MODE`, `--shader MODE`, `--video-fps FPS` | Control video/render output. |
| `-n`, `--num-envs N` | Number of environments/processes used for replay; CPU uses multiprocessing, GPU uses parallel sim. |

Conversion support is intentionally narrow:

- If original and target control modes match, replay simply steps original
  actions.
- Original `pd_joint_pos` can be converted to several joint or end-effector
  target modes when the robot/controller structure supports it.
- Original `pd_joint_delta_pos` can convert back to `pd_joint_pos`.
- The conversion helper is Panda-centric and may be wrong or unsupported for
  other robots.
- GPU-parallel replay rejects different target control modes.
- `--use-env-states` is incompatible with changing control modes because action
  counts/timings can differ.

## `mani_skill.trajectory.convert_to_lerobot`

Help:

```bash
python -m mani_skill.trajectory.convert_to_lerobot -h
```

Core options:

| Option | Purpose |
|---|---|
| `--traj-path PATH` | Required ManiSkill `.h5` trajectory file; sibling `.json` is read when present and required for normal workflows. |
| `--output-dir DIR` | Destination LeRobot dataset directory. |
| `--fps INT` | Video and timestamp FPS; default is 30. |
| `--task-name TEXT` | Task description; if omitted, converter tries metadata `env_id`. |
| `--chunks-size INT` | Episodes per parquet chunk; default is 1000. |
| `--image-size WxH` | Output video frame size, e.g. `640x480`; a single integer creates square output. |
| `--robot-type TEXT` | Robot type override; otherwise the converter guesses from metadata. |

Converter data extraction:

- Reads `actions` from each `traj_*` group.
- Detects RGB cameras under `obs/sensor_data/<camera>/rgb` if observations were
  recorded or replayed with vision observations.
- Detects robot state from `obs/agent/qpos` when present.
- Writes parquet chunks, metadata, statistics, and one MP4 per camera/episode
  when RGB frames exist.

Dependency facts:

- `pandas` is imported at module import time.
- `pyarrow` is imported during parquet writing.
- `cv2`/OpenCV is used for resizing and writing videos.
- Installing `lerobot` can provide broader dataset tooling; installing
  `pyarrow` alone is enough for the converter's parquet-writing path when the
  other imports are already available.

## `ManiSkillTrajectoryDataset`

Import path:

```python
from mani_skill.trajectory.dataset import ManiSkillTrajectoryDataset
```

Constructor shape:

```python
ManiSkillTrajectoryDataset(
    dataset_file: str,
    load_count=-1,
    success_only: bool = False,
    device=None,
)
```

Use this class as starter code for PyTorch data loading:

```python
dataset = ManiSkillTrajectoryDataset("demos/PickCube-v1/trajectory.state.pd_joint_delta_pos.physx_cpu.h5")
sample = dataset[0]
print(sample.keys())  # obs, action, terminated, truncated, and optional reward/success/fail
```

Important behavior:

- Loads selected trajectories into memory; it is not a streaming dataset.
- Requires the `.json` pair next to the `.h5` file.
- Concatenates actions and terminal flags across episodes.
- Uses `obs[:T]`, excluding the final observation, because most learning
  workflows use observations aligned with actions.
- `success_only=True` requires episode-level `success` metadata.
- Converts `uint16` observation arrays to `int32` for easier tensor conversion.

## Download CLIs

Demo list/download:

```bash
python -m mani_skill.utils.download_demo
python -m mani_skill.utils.download_demo PickCube-v1
python -m mani_skill.utils.download_demo PickCube-v1 -o demos_cache
```

Asset list/download:

```bash
python -m mani_skill.utils.download_asset
python -m mani_skill.utils.download_asset --list scene
python -m mani_skill.utils.download_asset ReplicaCAD -y -o asset_cache
```

Safety notes:

- List modes are safe and local; download modes need network and may create,
  overwrite, or remove directories.
- `download_demo all` and `download_asset all` can be very large.
- `download_asset -y/--non-interactive` suppresses prompts; use only with user
  approval because existing targets may be removed.
- `MS_SKIP_ASSET_DOWNLOAD_PROMPT=1` also skips asset prompts.

## Motion-planning and teleoperation entry points

Motion-planning runners:

```bash
python -m mani_skill.examples.motionplanning.panda.run -h
python -m mani_skill.examples.motionplanning.panda.run -e PickCube-v1 --save-video
python -m mani_skill.examples.motionplanning.so100.run -h
python -m mani_skill.examples.motionplanning.xarm6.run -h
```

Teleoperation runners:

```bash
python -m mani_skill.examples.teleoperation.interactive_panda -e StackCube-v1
python -m mani_skill.examples.teleoperation.interactive_so100 -e PickCube-v1
python -m mani_skill.examples.teleoperation.interactive_xarm6 -e PickCube-v1
```

Teleoperation key bindings are displayed by `h` in the viewer. The common flow
is drag target, press `n` to execute a motion-plan to the target, use `g` for the
gripper, `c` to save and continue, and `q` to quit.

## Trajectory utilities and merging

Useful module functions:

```python
from mani_skill.trajectory import utils as trajectory_utils
states = trajectory_utils.dict_to_list_of_dicts(traj["env_states"])
state_t = trajectory_utils.index_dict(states, t)
batched = trajectory_utils.list_of_dicts_to_dict([state_t])
```

For worker outputs that need merging:

```python
from mani_skill.trajectory.merge_trajectory import merge_trajectories
merge_trajectories("merged.h5", ["worker0.h5", "worker1.h5"])
```

`merge_trajectories` creates a matching JSON, merges episodes, copies HDF5
`traj_*` groups, and recomputes episode IDs by default.

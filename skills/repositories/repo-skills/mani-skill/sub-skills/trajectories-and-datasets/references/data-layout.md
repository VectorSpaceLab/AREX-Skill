# Trajectory and dataset data layout

## Required bundle shape

A ManiSkill trajectory bundle is a `.h5` file and a sibling `.json` file with the
same stem:

```text
trajectory.h5
trajectory.json
```

Do not replay, load, or convert a `.h5` without first checking that the matching
JSON is present. The JSON carries the task ID, env kwargs, episode reset kwargs,
control mode, source information, and per-episode final info needed to recreate
or diagnose the data.

## File naming convention

Official and replayed files often use this stem:

```text
<trajectory_name>.<obs_mode>.<control_mode>.<sim_backend>.h5
```

`trajectory.h5` is commonly treated as shorthand for a raw minimized trajectory
with no observations, `pd_joint_pos` actions, and a CPU PhysX backend. However,
the JSON metadata should win over filename guesses.

The replay tool writes new output next to the input file and appends the actual
recorded observation mode, control mode, and simulation backend to the output
stem. It asserts that the output path is not the same file as the input.

## JSON metadata

The paired JSON normally contains:

- `env_info`: environment recreation metadata.
  - `env_id`: Gymnasium/ManiSkill task ID.
  - `max_episode_steps`: episode horizon when known.
  - `env_kwargs`: kwargs used to build the environment; essential for replay.
- `episodes`: list of episode records.
  - `episode_id`: integer used by the HDF5 group name `traj_<episode_id>`.
  - `reset_kwargs`: kwargs used for `env.reset(...)`; essential for replay.
  - `control_mode`: control mode used by the actions in that episode.
  - `elapsed_steps`: trajectory length.
  - `info`: final environment info; may include success/failure labels.
- Optional `source_type`: short category such as `motionplanning`,
  `teleoperation`, `RL`, or `manual`.
- Optional `source_desc`: longer human-readable source description.
- Recordings produced by `RecordEpisode` also include commit/build provenance
  fields when available.

## HDF5 trajectory groups

Each episode is stored in an HDF5 group named `traj_<episode_id>`, for example
`traj_0`. A normal group contains:

| Key | Shape/meaning |
|---|---|
| `actions` | `[T, A]`; action vector or nested action tree after wrapper processing. |
| `terminated` | `[T]`; task termination flags. |
| `truncated` | `[T]`; time-limit/episode truncation flags. |
| `env_states` | `[T+1, ...]` dictionary-of-arrays when `record_env_state=True`. |
| `obs` | Optional `[T+1, ...]` observation tree; often absent from raw compressed demos. |
| `rewards` | Optional `[T]` rewards when `record_reward=True` or replay adds rewards. |
| `success` | Optional `[T]` success flags when the environment reports them. |
| `fail` | Optional `[T]` failure flags when the environment reports them. |

The `env_states` and many observation modes are nested dictionaries. In HDF5 they
are stored as dictionary-of-arrays. To work with one timestep at a time:

```python
from mani_skill.trajectory import utils as trajectory_utils

with h5py.File("trajectory.h5", "r") as f:
    states = trajectory_utils.dict_to_list_of_dicts(f["traj_0"]["env_states"])
    state_10 = trajectory_utils.index_dict(states, 10)
```

Use `list_of_dicts_to_dict` to invert the representation when batching multiple
state dictionaries for vectorized replay.

## RecordEpisode output locations

`RecordEpisode` writes directly under the configured `output_dir`:

```text
<output_dir>/<trajectory_name>.h5
<output_dir>/<trajectory_name>.json
<output_dir>/*.mp4                  # optional, depending on video settings
```

Maintained example runners choose their own `output_dir`:

- Teleoperation defaults to `<record_dir>/<env_id>/teleop/trajectory.h5`.
- Motion-planning examples default to `<record_dir>/<env_id>/motionplanning/`.
  This order follows the installed runner behavior; do not assume legacy prose
  examples that invert the `<env_id>` and `motionplanning` folders are current.

## Replayed output layout

When `--save-traj` is enabled, the replay CLI writes a new `.h5`/`.json` pair in
the source trajectory directory. The output stem is based on the original stem
plus the actual target observation mode, control mode, and backend, for example:

```text
trajectory.state.pd_joint_delta_pos.physx_cpu.h5
trajectory.state.pd_joint_delta_pos.physx_cpu.json
```

CPU replay with multiple workers can create temporary per-worker files and then
merge them. The merge step copies `traj_*` groups, merges JSON episode lists, and
recomputes episode IDs by default.

## LeRobot conversion output

The LeRobot converter creates a dataset directory shaped like:

```text
<output-dir>/
  data/
    chunk-000/file-000.parquet
    chunk-001/file-000.parquet
  videos/
    observation.images.<camera>/chunk-000/file-000.mp4
  meta/
    info.json
    stats.json
    tasks.parquet
    episodes/chunk-000/file-000.parquet
```

The exact videos subtree appears only when the ManiSkill trajectory includes RGB
observations under `obs/sensor_data/<camera>/rgb`. If the source trajectory has
no observations, replay it first with a vision obs mode before LeRobot
conversion.

## `ManiSkillTrajectoryDataset` memory layout

`ManiSkillTrajectoryDataset` is starter PyTorch dataset code, not a streaming
production loader:

- Opens the `.h5` and loads selected HDF5 groups into memory.
- Loads metadata from the sibling `.json`.
- Concatenates actions, terminal flags, rewards, success, and failure arrays.
- Uses `obs[:T]` for each episode, dropping the final observation so observation
  samples align with actions.
- Returns a dictionary containing `obs`, `action`, `terminated`, `truncated`, and
  optional `reward`, `success`, `fail`.
- Moves arrays to `device` when one is provided.

For large visual datasets, copy/adapt the class rather than expecting it to be
memory efficient out of the box.

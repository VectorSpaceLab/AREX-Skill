# Data formats

## Canonical normalized tree

The preferred layout is:

```text
data/<task_config>/<task>/<embodiment>/
  data/episode_0000000.hdf5
  data/episode_0000001.hdf5
  video/episode_0000000.mp4
  instruction/episode_0000000.json
  seed.txt                # present for self-collected runs
  scene_info.json         # present for self-collected runs
```

The default embodiment in this checkout is `aloha_agilex`, but the same folder contract is used for other supported embodiments.

## XPolicyLab episode HDF5

A normalized episode is a single HDF5 file with these common top-level fields:

- `source_format` and `source_path` attributes
- `data_format_version` dataset
- `instructions` dataset or string payload with the candidate language set
- `instruction` may appear in converted legacy files as one preferred string
- `additional_info/frequency`
- `state/*`
- `action/*`
- `vision/*`

### State and action groups

The common joint keys are:

- `left_arm_joint_states`
- `left_ee_joint_states`
- `right_arm_joint_states`
- `right_ee_joint_states`
- `joint_states` when a combined vector is present
- `left_ee_poses` and `right_ee_poses` when end-pose data is available

These datasets are 2D time series. The first axis is the horizon. The converter and native collection path both use next-frame alignment by default, so `state` and `action` should have matching horizon lengths after conversion.

### Vision group

The camera mapping used by the data pipeline is:

- `head_camera` -> `cam_head`
- `left_camera` -> `cam_left_wrist`
- `right_camera` -> `cam_right_wrist`
- `front_camera` -> `cam_third_view`

Each camera group may contain:

- `colors` for JPEG-encoded RGB frames
- `shape` for the decoded image size
- `depths` when depth is stored
- `intrinsic_matrix`
- `extrinsic_matrix`

A file may also contain `pointclouds` if point clouds were saved.

## Native collection sidecars

Fresh collection writes extra files next to the HDF5 episodes:

- `video/episode_*.mp4` from the head camera
- `instruction/episode_*.json` with `seen` and `unseen` language candidates
- `scene_info.json` with per-episode metadata
- `seed.txt` with the replay seeds used for the run

## Legacy layouts

Older RoboTwin data may use two legacy forms:

1. **Raw episode bundles** under `data/<task>/<task_config>/data/`.
   - These are the inputs for `scripts/process_data_xpolicylab.py`.
   - The converter can also copy `seed.txt` and `scene_info.json` when they exist.

2. **Intermediate per-frame cache pickles** used during collection.
   - `envs/utils/pkl2hdf5.py` merges those caches into the final HDF5/video pair.
   - `data/process_stuck.py` only applies to the older `.pkl` episode bundle layout.

Do not treat legacy raw outputs as final training data until they have been normalized.

## Reader and writer notes

- `envs/utils/pkl2hdf5.py` writes the normalized episode structure and JPEG byte arrays.
- `envs/utils/parse_hdf5.py` reads the same layout back into nested Python data.
- `scripts/process_data_xpolicylab.py` can emit either array or JSON-style instruction payloads, depending on its CLI flags.

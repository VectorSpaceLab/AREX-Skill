# LeRobot data format for StarVLA

StarVLA's robot-action loader expects each dataset selected by a mixture entry to be a LeRobot-format directory. The mixture entry gives the dataset subdirectory relative to `datasets.vla_data.data_root_dir`; the loader then opens metadata, parquet data, videos/images, language task metadata, and statistics from that dataset directory.

## Required dataset files

A usable dataset has this logical shape:

```text
<dataset_subdir>/
  meta/
    modality.json          # StarVLA-specific modality mapping; required
    info.json              # LeRobot data_path, video_path, chunks_size, features
    episodes.jsonl         # LeRobot v2 episode lengths and indices
    tasks.jsonl            # LeRobot v2 task_index -> task text
    stats_gr00t.json       # StarVLA statistics cache; generated if absent/stale
  data/*/*.parquet         # LeRobot step tables
  videos/...               # when video features are stored as videos
```

LeRobot v3 datasets use parquet task and episode metadata (`meta/tasks.parquet`, `meta/episodes/*/*.parquet`) with the same StarVLA `meta/modality.json` requirement. Image-only datasets may store image arrays directly in parquet; video datasets resolve frame timestamps through `info.json` and the video backend.

## `meta/modality.json` contract

`modality.json` must be JSON with these top-level objects:

- `video`: camera aliases used by StarVLA.
- `state`: named slices into a LeRobot state column.
- `action`: named slices into a LeRobot action column.
- `annotation`: language/task lookup metadata.

Minimal two-camera single-arm example:

```json
{
  "video": {
    "cam_global": {"original_key": "observation.images.cam_global"},
    "cam_wrist": {"original_key": "observation.images.cam_wrist"}
  },
  "state": {
    "joint_positions": {"start": 0, "end": 6, "original_key": "observation.state"},
    "gripper_width": {"start": 6, "end": 7, "original_key": "observation.state"}
  },
  "action": {
    "ee_positions": {"start": 0, "end": 7, "original_key": "action"},
    "gripper_width": {"start": 7, "end": 8, "original_key": "action"}
  },
  "annotation": {
    "human.task_description": {"original_key": "task_index"}
  }
}
```

Important details:

- StarVLA references a language key as `annotation.<annotation-subkey>` in `DataConfig.language_keys`; therefore `annotation.human.task_description` means the `annotation` object contains a flat key `human.task_description`.
- Some existing benchmark configs use `annotation.human.action.task_description`; in that case the flat key inside `annotation` is `human.action.task_description` and the `DataConfig.language_keys` entry must be `annotation.human.action.task_description`.
- The language annotation `original_key` must be `task_index`. StarVLA reads the task id from the step parquet row and uses it to index the LeRobot task table.
- `state` and `action` entries use end-exclusive integer slices. `start` must be non-negative and `end` must be greater than `start`.
- If `original_key` is omitted for state/action, StarVLA's schema defaults are `observation.state` for state and `action` for action. Supplying `original_key` is clearer for custom datasets.
- Optional state/action metadata includes `rotation_type`, `absolute`, `dtype`, and `range`. `rotation_type` values are StarVLA rotation enum strings such as `axis_angle`, `quaternion`, or `rotation_6d`; `absolute` controls padding behavior for out-of-range temporal samples.

## Matching modality keys to `DataConfig`

The keys in `DataConfig` are full StarVLA keys built from a modality prefix plus a `modality.json` subkey:

| `modality.json` location | `DataConfig` key example |
| --- | --- |
| `video.cam_global` | `video.cam_global` |
| `state.joint_positions` | `state.joint_positions` |
| `action.ee_positions` | `action.ee_positions` |
| `annotation.human.task_description` | `annotation.human.task_description` |

The data loader checks every configured key against `modality.json`; a mismatch fails during dataset initialization.

## Temporal indices and action horizon

`ModalityConfig.delta_indices` controls which relative time steps are loaded for a modality. Common choices:

- `observation_indices = [0]`: current image/state/language only.
- `state_indices = [0]`: current state only.
- `state_indices = list(range(-16, 0))`: a previous-state window for selected configs.
- `action_indices = list(range(8))`: actions from `t` through `t+7`.
- `action_indices = list(range(16))` or `list(range(50))`: longer chunks for specific benchmark or VM4A recipes.

Keep `len(action_indices)` consistent with the selected framework's `action_horizon` or policy horizon. If the YAML/model side must be changed, route to [training-config](../../training-config/SKILL.md).

## What the loader returns

For each sample, StarVLA packs:

- `image`: one resized PIL image per configured video key, in `DataConfig.video_keys` order.
- `lang`: the task text looked up through `task_index`.
- `action`: concatenated transformed action chunks in `DataConfig.action_keys` order.
- `robot_tag`: the embodiment tag value.
- `state`: included only when the dataset config requests state packing.

Order matters. Camera, state, and action ordering in `DataConfig` must match the dimensions expected by the model config and deployment client.

## Statistics and cache behavior

StarVLA computes low-dimensional statistics from the dataset's parquet files and stores a StarVLA cache at `meta/stats_gr00t.json`. The cache includes a format version and a cache config containing action mode. If the cache is legacy, unreadable, or built with a different action mode, StarVLA removes/rebuilds it on rank 0 and other ranks wait for the cache.

Action mode caveats:

- `abs` leaves action values as stored.
- `delta` converts selected action keys into step deltas, with the first action relative to the matching state.
- `rel` makes selected action keys relative to the current state.
- Delta/relative statistics need both action and state modalities plus valid `action_mode_apply_keys` and optional `action_mode_state_map` when action and state key names differ.

Training also writes a run-level `dataset_statistics.json`. Keep that file with the checkpoint because deployment unnormalization and policy-server metadata depend on the same state/action dimensions and normalization masks.

## Video backends

The loader supports `decord`, `torchcodec`, `opencv`, `pyav`, and `torchvision_av` backend paths. `video_backend` is passed from `datasets.vla_data`. `decord` is often fast; `torchvision_av` and `pyav` are useful compatibility fallbacks; `opencv` can help with simple containers. Backend failures are usually dependency or codec issues, not modality schema issues.

## Evidence notes

This reference distills the metadata constants, schema models, dataset initialization, language lookup, action-mode conversion, statistics cache, video backend handling, and sample packing behavior from the StarVLA dataloader sources and representative modality files.

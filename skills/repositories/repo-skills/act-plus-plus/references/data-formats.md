# Data formats

## When to read

Read this before generating, validating, mirroring, compressing, training on, or caching features for ACT++ HDF5 episodes.

## Episode HDF5 layout

A standard episode file is named `episode_<idx>.hdf5` and uses these fields:

| Path or attr | Shape / type | Meaning |
| --- | --- | --- |
| `attrs['sim']` | bool | Whether the episode came from simulation. |
| `attrs['compress']` | bool, optional | Present and true for JPEG-compressed images. |
| `/observations/qpos` | `(T, 14)` | Joint-space state: left 6 arm joints + left gripper + right 6 arm joints + right gripper. |
| `/observations/qvel` | `(T, 14)` | Joint velocities with normalized gripper velocities. |
| `/action` | `(T, 14)` | Joint command targets matching qpos ordering for sim data. |
| `/base_action` | `(T, 2)`, optional | Mobile base linear/angular action for real/mobile data. `utils.EpisodicDataset` appends zeros when absent. |
| `/observations/images/<camera>` | uncompressed `(T, 480, 640, 3)` uint8 or compressed `(T, padded_len)` uint8 | Camera frames. Sim cameras are usually `top`, `left_wrist`, `right_wrist`. |
| `/compress_len` | `(num_cameras, T)`, compressed only | True encoded JPEG length for each padded frame. |

`utils.find_all_hdf5` recursively finds `*.hdf5` files and skips filenames containing `features`. Set `skip_mirrored_data=True` to exclude filenames containing `mirror`.

## Compressed image contract

Compressed episodes store JPEG bytes as padded uint8 arrays. To decode one frame, use the corresponding `compress_len[cam_id, frame_id]` to trim the padded row before `cv2.imdecode` when available. Some helper code decodes the full padded row; if decoding fails or produces corrupt frames, check the trim length first.

## Mirrored episodes

`postprocess_episodes` writes `mirror_episode_<idx>.hdf5`. It swaps left/right arm state and action blocks, multiplies sign-correction masks, flips wrist/top camera images horizontally, preserves optional `/base_action`, and writes compressed images.

Mirror state masks from the code:

- State/action side block multiplier: `[-1, 1, 1, -1, 1, -1, 1]`
- Base action multiplier: `[1, -1]`

## Training dataset behavior

`utils.load_data` accepts either one dataset directory or a list. It builds train/val ids from the first directory, appends all additional directories to training, then computes normalization stats from `stats_dir_l` if provided, otherwise from the dataset directories.

Important training details:

- ACT/CNNMLP normalize action by mean/std.
- Diffusion normalizes action to `[-1, 1]` using min/max.
- Missing `/base_action` becomes a zero two-vector appended to the 14-D arm action, so model action dimension is 16.
- `EpisodicDataset` reads only one observation at a sampled timestep and pads the future action chunk to `chunk_size`.
- Diffusion training enables image augmentation; ACT/CNNMLP do not.

## Feature HDF5 layout for VINN

VINN feature files are named from the representation and seed parsed from the BYOL checkpoint name:

- `byol_features_seed<seed>_episode_<idx>.hdf5`
- `byol_cotrain_features_seed<seed>_episode_<idx>.hdf5` when checkpoint name contains `cotrain`

Each feature file stores:

| Path | Shape | Meaning |
| --- | --- | --- |
| `/features/<camera>` | `(T, 512)` | ResNet18 penultimate feature for one camera frame stream. |

The k-selection workflow concatenates all camera features along feature dimension before nearest-neighbor regression.

## Quick validation checklist

- Episode indices should be dense from `0` to `N-1`; VINN feature caching asserts there are no holes.
- Check `attrs['compress']` before assuming image arrays are raw RGB frames.
- Confirm camera names match the task config before training or caching features.
- Confirm action width: 14 for sim files on disk, 16 inside training batches when base action is appended.
- Use the simulation-data checker before relying on rendered observations from MuJoCo.

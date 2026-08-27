# Configuration Guide

MonoGS configs are YAML files with recursive inheritance. Scene files should stay small and override only the fields that differ from the shared base.

## Merge rules
- `inherit_from` points at another YAML file.
- The loader merges nested maps recursively, so a scene file can override a single leaf like `Dataset.dataset_path` or `Dataset.Calibration.depth_scale`.
- Base configs provide shared `Results`, `Dataset`, `Training`, `opt_params`, `model_params`, and `pipeline_params` values.
- `Results.save_results=True` makes MonoGS create a timestamped run directory under `Results.save_dir`.
- `Dataset.type` selects the loader family: `tum`, `replica`, `euroc`, or `realsense`.
- `Dataset.sensor_type` should match the family: `monocular`, `depth`, or `stereo`.
- `Training.single_thread` is read by the frontend.
- `Dataset.single_thread`, when present, is read by the backend.
- `Training.kf_cutoff` is optional; when omitted, the frontend falls back to its built-in cutoff.

## Edit the scene file when you change
- one dataset path
- one sequence calibration
- one EuRoC start index
- one Replica single-thread setting
- one live RealSense path or sensor mode

## Family map
| Family | Base config | Scene overrides | Notes |
| --- | --- | --- | --- |
| TUM monocular | `configs/mono/tum/base_config.yaml` | `fr1_desk`, `fr2_xyz`, `fr3_office` | Uses TUM RGB-D files with monocular tracking settings and scene calibration. |
| TUM RGB-D | `configs/rgbd/tum/base_config.yaml` | `fr1_desk`, `fr2_xyz`, `fr3_office` | Same dataset family as TUM monocular, but `sensor_type: depth` and depth-aware defaults. |
| Replica RGB-D | `configs/rgbd/replica/base_config.yaml` | `office0`, `office1`, `office2`, `office3`, `office4`, `room0`, `room1`, `room2`, plus `_sp` variants | Scene files mainly set the `dataset_path`; `_sp` files flip the single-thread flag used by the backend. |
| EuRoC stereo | `configs/stereo/euroc/base_config.yaml` | `mh02` | Requires stereo calibration, rectification data, and a nonzero `start_idx`. |
| RealSense live | `configs/live/realsense.yaml`, `configs/live/realsense_rgbd.yaml` | none | Live camera configs derive pose/camera input from hardware rather than from a dataset tree. |

## Editing checklist
1. Keep `inherit_from` pointed at a shared base config.
2. Change `Dataset.dataset_path` only to the dataset root expected by the parser.
3. Update the matching `Dataset.Calibration` block when the camera or sequence changes.
4. Keep `Results.save_dir` relative and stable if you want predictable output buckets.
5. Run `scripts/validate_monogs_config.py` before handing the config off to a SLAM run.

## Output directory behavior
When saving is enabled, MonoGS groups a run by the last path segments of `Dataset.dataset_path` and writes the resolved config into the timestamped run directory. Changing the dataset path therefore changes the output bucket name.

---
name: data-pipeline
description: "Use RoboTwin datasets, collect demonstrations, validate XPolicyLab
  HDF5 trajectories, and convert legacy data layouts."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# RoboTwin data pipeline

Use this sub-skill when the user asks about RoboTwin pre-collected data, data collection, trajectory layout, HDF5 validation, legacy data conversion, asset downloads, or preparing data for XPolicyLab/LeRobot workflows.

## Route first

- For SAPIEN, `Base_Task`, robot/camera/config bootstrap, or render/backend setup, read [simulation-core](../simulation-core/SKILL.md).
- For policy rollout/evaluation, scheduler configs, remote server mode, or action adapter shapes, read [policy-eval](../policy-eval/SKILL.md).
- For adding new tasks or language templates, read [task-authoring](../task-authoring/SKILL.md).

## Main workflows

1. **Use pre-collected data**: prefer public XPolicyLab-format RoboTwin trajectories when the task is training or evaluation data preparation. Read [workflows.md](references/workflows.md).
2. **Collect demonstrations**: use task/config/GPU arguments and verify simulation prerequisites first. Read [workflows.md](references/workflows.md) and [troubleshooting.md](references/troubleshooting.md).
3. **Validate a trajectory file or downloaded layout**: use [scripts/inspect_xpolicylab_hdf5.py](scripts/inspect_xpolicylab_hdf5.py) for one file and [scripts/validate_download_layout.py](scripts/validate_download_layout.py) for a downloaded task/config/embodiment directory.
4. **Convert old raw data**: read [data-formats.md](references/data-formats.md) and the conversion section in [workflows.md](references/workflows.md).
5. **Create or bootstrap a standalone workspace**: use the root [workspace bootstrapper](../../references/workspace-bootstrap.md) instead of expecting the original checkout.

## Key layout facts

- Recommended downloaded/current collection layout:

  ```text
  data/<task_config>/<task_name>/<embodiment>/
    data/episode_0000000.hdf5
    video/episode_0000000.mp4
    instruction/episode_0000000.json
  ```

- Legacy raw layout converted by the repository utility:

  ```text
  data/<task_name>/<task_config>/data/episode0.hdf5
  ```

- Default config/embodiment examples: `demo_clean`, `demo_randomized`, `aloha_agilex`.
- Collection writes XPolicyLab trajectory HDF5 directly in current RoboTwin 2.0 paths.

## Validation signals

- HDF5 contains `data_format_version`, `state/`, `action/`, `vision/`, and `additional_info/frequency`.
- Required state/action datasets have matching horizon lengths.
- RGB camera data lives under `vision/cam_head/colors` and optionally wrist camera groups.
- Instruction data exists as `instruction` or `instructions`.
- Downloaded layout contains at least one `episode_0000000.hdf5`; videos/instructions are useful but may be optional depending on archive version.

## Safety

- Dataset download and asset download commands can be large and network-heavy; do not run them unless the user asks or the workspace clearly needs them.
- Data collection launches SAPIEN simulation and can use GPU/rendering resources; start with one small task/config before scaling.
- Do not delete stuck episodes or rewrite seed files unless the user explicitly wants data cleanup.

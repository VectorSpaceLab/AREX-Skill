# Dataset registry and `DataConfig` contract

StarVLA chooses robot datasets through three registry maps:

- `ROBOT_TYPE_CONFIG_MAP`: `robot_type -> DataConfig instance`.
- `DATASET_NAMED_MIXTURES`: `data_mix -> [(dataset_subdir, sampling_weight, robot_type), ...]`.
- `ROBOT_TYPE_TO_EMBODIMENT_TAG`: derived registry map used for compatibility; new configs should prefer an `embodiment_tag` class variable on the `DataConfig` class.

The registry starts with base StarVLA configs and then auto-discovers benchmark-specific modules under `examples/**/train_files/data_registry/data_config.py`. Discovery excludes SDK helper trees and merges any exported maps from each discovered module.

## Registry auto-discovery

A discovered `data_config.py` module may export any of these names:

```python
ROBOT_TYPE_CONFIG_MAP = {
    "my_robot": MyRobotDataConfig(),
}

DATASET_NAMED_MIXTURES = {
    "my_mix": [
        ("relative_dataset_subdir", 1.0, "my_robot"),
    ],
}

ROBOT_TYPE_TO_EMBODIMENT_TAG = {
    # Legacy override only; prefer MyRobotDataConfig.embodiment_tag.
}
```

When the user sets `datasets.vla_data.data_mix: my_mix`, StarVLA looks up `DATASET_NAMED_MIXTURES["my_mix"]`, removes duplicate `(dataset_subdir, robot_type)` pairs, and creates each `LeRobotSingleDataset` at `data_root_dir / dataset_subdir` using `ROBOT_TYPE_CONFIG_MAP[robot_type]`.

If `data_mix` is not registered, the loader fails at lookup time. If `robot_type` is not registered, dataset construction fails while creating the mixture.

## `DataConfig` responsibilities

A robot `DataConfig` is a small class with class variables and two required methods.

Required class variables:

- `embodiment_tag`: prefer an `EmbodimentTag` enum value. If absent, registry derivation and dataset construction fall back to `NEW_EMBODIMENT` and may warn.
- `video_keys`: ordered full StarVLA camera keys, for example `video.cam_global`.
- `state_keys`: ordered full state keys, for example `state.joints`.
- `action_keys`: ordered full action keys, for example `action.delta_joints`.
- `language_keys`: ordered language keys; most configs use a single key such as `annotation.human.task_description` or `annotation.human.action.task_description`.
- `observation_indices`: relative samples for image/state/language, commonly `[0]`.
- `action_indices`: relative action chunk indices. Its length must match the model/training action horizon.
- Optional `state_indices`: separate state window; if absent, many configs reuse `observation_indices`.

Required methods:

- `modality_config()` returns a dict with `video`, `state`, `action`, and `language` entries, each a `ModalityConfig(delta_indices=..., modality_keys=...)`.
- `transform()` returns a `ComposedModalityTransform`, usually with `StateActionToTensor` and `StateActionTransform` for state/action keys and optional video transforms or concatenation.

Optional hook:

- `make_dataset(dataset_path=..., modality_configs=..., transforms=..., embodiment_tag=..., video_backend=..., delete_pause_frame=..., data_cfg=..., dataset_name=...)` can swap in a custom dataset class. If absent, StarVLA uses the default `LeRobotSingleDataset`.

## Key alignment checklist

For every `DataConfig` key:

1. Remove the modality prefix to get the `modality.json` subkey. Example: `state.joints` must have a `state` entry named `joints`.
2. Ensure the `modality.json` slice width equals the dimension expected by transforms, model config, and deployment client.
3. Keep camera order deterministic. Model image order follows `video_keys`.
4. Keep action order deterministic. StarVLA concatenates actions in `action_keys` order for training and statistics.
5. Keep language key and annotation subkey identical. Example: `language_keys = ["annotation.human.task_description"]` requires `annotation` to contain a flat `human.task_description` field with `original_key: "task_index"`.

## Transform responsibilities

`DataConfig.transform()` owns training-time low-dimensional preprocessing:

- `StateActionToTensor` converts NumPy arrays to tensors for selected keys.
- `StateActionTransform` performs normalization and optional rotation conversion. Supported normalization modes include `min_max`, `q99`, `mean_std`, and `binary`.
- `StateActionSinCosTransform` is used by selected humanoid/GR1-style configs to expand joint angles into sine/cosine features.
- `ConcatTransform` can combine ordered camera/state/action keys, checking that configured keys and inferred dimensions match metadata.
- Video transforms may crop, resize, jitter, convert to tensor, or convert back to NumPy, but many benchmark configs leave video transforms out and let sample packing resize images to the model size.

Normalization modes must match the actual value semantics. Examples from StarVLA configs:

- `min_max`: common for continuous EEF, joint, and gripper values when min/max stats are meaningful.
- `q99`: robust quantile scaling used by some OpenPI/LIBERO and OXE-style configs.
- `mean_std`: used by Realman joint deltas.
- `binary`: used when gripper fields are non-continuous or thresholded.

If a state/action field is non-continuous, use `binary`; the transform rejects incompatible non-binary normalization.

## Action indices versus horizon

`action_indices` is data-side temporal sampling. `action_horizon` or framework horizon is model-side output length. They must describe the same chunk length for the selected framework.

Examples seen in StarVLA configs:

- LIBERO and VLA-Arena: `action_indices = list(range(8))` for an 8-step chunk.
- Standard OXE/RobotWin/Franka-style configs: `list(range(16))`.
- Some Realman and RoboDojo/RobotWin variants: `list(range(50))` for ACT or long-horizon recipes, with a separate 16-step variant for Diffusion Policy.

If the mismatch is in YAML or launch planning, route to [training-config](../../training-config/SKILL.md). If the mismatch is in client/server action chunk handling, route to [policy-deployment](../../policy-deployment/SKILL.md).

## Embodiment tags

`embodiment_tag` controls the robot tag packed into samples and the embodiment embedding/head selection used by compatible models. Known enum values include `new_embodiment`, `franka`, `gr1`, `oxe_droid`, `oxe_bridge`, `oxe_rt1`, `aloha`, `ur5`, `arx5`, `arx_x5`, and `dos-w1`.

Rules of thumb:

- Use `EmbodimentTag.NEW_EMBODIMENT` when integrating a new robot or when you are not sure that the action space matches an existing embodiment head.
- Use an existing tag only when the state/action semantics and action dimensions match that embodiment's model expectations.
- Prefer the class variable `embodiment_tag = EmbodimentTag.<...>` on the `DataConfig` class.
- Legacy `ROBOT_TYPE_TO_EMBODIMENT_TAG` exports are still honored as overrides. They are useful for older registry modules but not required for new ones.

## Mixture design

A mixture entry is `(dataset_subdir, weight, robot_type)`. Use it to:

- combine multiple task directories for one robot;
- combine multiple robots for cross-embodiment training;
- assign sampling weights for imbalanced data;
- select an alternate `DataConfig` for the same physical dataset, such as a long-horizon ACT variant versus a shorter Diffusion Policy variant.

Avoid duplicate `(dataset_subdir, robot_type)` entries; StarVLA skips duplicates during mixture construction.

## Data loader options that affect integration

Common `datasets.vla_data` options consumed by the loader include:

- `data_root_dir`: parent directory for mixture dataset subdirs.
- `data_mix`: registry key in `DATASET_NAMED_MIXTURES`.
- `dataset_py: lerobot_datasets`: selects this loader path.
- `video_backend`: defaults vary by call path; safe values include `decord`, `torchvision_av`, `pyav`, `opencv`, and `torchcodec` if installed.
- `delete_pause_frame`: optional dataset filtering flag passed into dataset construction.
- `include_state`: if true, sample packing includes concatenated state.
- `lerobot_version`: supports `v2.0` and `v3.0` metadata variants.
- `action_mode`, `action_mode_apply_keys`, `action_mode_state_map`: convert selected action keys to absolute, delta, or relative semantics and change statistics cache compatibility.
- `balance_dataset_weights` and `balance_trajectory_weights`: affect mixture sampling, not schema.

## Debugging registry import without data loading

When debugging a registration, inspect the maps rather than launching training. The expected signal is that the desired `robot_type` appears in `ROBOT_TYPE_CONFIG_MAP`, the desired `data_mix` appears in `DATASET_NAMED_MIXTURES`, and every mixture entry points to a registered `robot_type`.

If registry inspection fails before data loading because a dependency is missing, fix the StarVLA installation/environment first. Do not edit dataset schema to mask an import failure.

## Evidence notes

This reference distills StarVLA's registry module, base robot configs, dataset factory, representative benchmark/real-robot registries, embodiment enum definitions, and transform contracts.

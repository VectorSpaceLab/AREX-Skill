---
name: data-integration
description: "Integrate LeRobot-format StarVLA datasets, modality schemas, robot
  DataConfig classes, mixtures, and registry discovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# StarVLA data integration

Use this sub-skill when the task is to add, debug, or review StarVLA robot-action data sources: LeRobot-format datasets, `meta/modality.json`, robot `DataConfig` classes, dataset mixtures, embodiment tags, registry discovery, statistics caches, and safe custom-dataset templates.

## Route elsewhere

- Training command construction, YAML launch overrides, Accelerate/DeepSpeed, or checkpoint resume: [training-config](../training-config/SKILL.md).
- Policy request/response schemas, server-side unnormalization, deployment clients, or real-robot bridge calls: [policy-deployment](../policy-deployment/SKILL.md).
- Simulator installation, benchmark evaluator loops, rendering, or benchmark environment setup: [benchmark-evaluation](../benchmark-evaluation/SKILL.md).

## Operating map

1. Confirm that each dataset is a LeRobot dataset with `meta/modality.json`, LeRobot metadata files, parquet data, and task metadata. Use [LeRobot data format](references/lerobot-data-format.md) for the expected shape.
2. Draft or edit the robot `DataConfig`: define `video_keys`, `state_keys`, `action_keys`, `language_keys`, `observation_indices`, optional `state_indices`, and `action_indices`; implement `modality_config()` and `transform()`. Use [dataset registry](references/dataset-registry.md).
3. Register the robot and mixture by exporting `ROBOT_TYPE_CONFIG_MAP` and `DATASET_NAMED_MIXTURES` from an auto-discovered `examples/**/train_files/data_registry/data_config.py` module. Prefer an `embodiment_tag` class variable on the `DataConfig`; legacy `ROBOT_TYPE_TO_EMBODIMENT_TAG` overrides still work.
4. Keep `len(action_indices)` aligned with the model/training `action_horizon` for the selected framework. If you are editing launch YAML, route to [training-config](../training-config/SKILL.md).
5. Validate candidate `modality.json` files before data loading with `scripts/validate_modality_json.py` from this sub-skill.
6. If the user starts from the bundled custom-dataset assets, adapt only the dataset and registry pieces here; route the training launcher and benchmark/policy bridge pieces as described in [dataset integration templates](references/dataset-integration-templates.md).

## Must-know StarVLA contracts

- StarVLA data loading uses `data_root_dir` plus `DATASET_NAMED_MIXTURES[data_mix]`; each mixture entry is `(dataset_subdir, sampling_weight, robot_type)`.
- `ROBOT_TYPE_CONFIG_MAP[robot_type]` must produce a `DataConfig` instance whose modality keys match the `meta/modality.json` subkeys.
- Language keys are StarVLA keys such as `annotation.human.task_description` or `annotation.human.action.task_description`; the corresponding `modality.json` annotation entry must read task ids with `original_key: "task_index"`.
- State/action `start` and `end` slices are end-exclusive slices into the LeRobot column named by `original_key` or the schema default.
- `StateActionTransform` owns training-time normalization (`min_max`, `q99`, `mean_std`, or `binary`) and reads dataset statistics generated from LeRobot parquet files.
- StarVLA may rebuild `meta/stats_gr00t.json` when cache format or action-mode configuration changes; keep the training-output `dataset_statistics.json` paired with checkpoints for deployment.

## References

- [LeRobot data format](references/lerobot-data-format.md)
- [Dataset registry](references/dataset-registry.md)
- [Dataset integration templates](references/dataset-integration-templates.md)
- [Troubleshooting](references/troubleshooting.md)

## Safe helper

- `scripts/validate_modality_json.py` validates the JSON shape without importing StarVLA or opening data files. It catches missing top-level modalities, invalid state/action slices, and the common language-conditioning error where the annotation field does not use `task_index`.

## Evidence notes

Distilled from StarVLA dataloader and registry sources (`starVLA/dataloader/__init__.py`, `lerobot_datasets.py`, `gr00t_lerobot/registry.py`, `data_config.py`, `datasets.py`, `schema.py`, `transform/*`), representative benchmark/robot data registries, the custom integration asset templates, and the README/guideline data sections.

# Custom dataset integration templates

StarVLA includes custom-integration assets under the repository's agent-skill template area. Treat them as reference scaffolds, not runtime files: they contain placeholders, launch commands, benchmark bridge code, and repo-relative assumptions that must be adapted to the user's dataset and routed to the correct StarVLA sub-skill.

## Template inventory and routing

| Template asset | Use here? | Reason |
| --- | --- | --- |
| `modality.json` | Adapt the schema here | It documents the required camera/state/action/annotation mapping, but must be normalized to the current StarVLA parser shape before use. |
| `data_config.py` | Adapt the registry/DataConfig here | It shows the `DataConfig`, `ROBOT_TYPE_CONFIG_MAP`, and `DATASET_NAMED_MIXTURES` pattern. |
| `training_config.yaml` | Route to [training-config](../../training-config/SKILL.md) | Training framework, action horizon, batch size, paths, and launch knobs are training-config responsibilities. |
| `run_train.sh` | Route to [training-config](../../training-config/SKILL.md) | It launches distributed training and snapshots configs; not safe as a portable data helper. |
| `model2bench_interface.py` | Route to [policy-deployment](../../policy-deployment/SKILL.md) and [benchmark-evaluation](../../benchmark-evaluation/SKILL.md) | It bridges model inference to benchmark/robot evaluation and depends on checkpoint/deployment contracts. |

## Adapted integration workflow

1. Convert or export the user's data into LeRobot format. Confirm each episode has images/videos, state/action arrays, timestamps, task ids, and task metadata.
2. Write `meta/modality.json` for every dataset subdir. Validate it with `scripts/validate_modality_json.py` from this sub-skill.
3. Draft a `DataConfig` whose keys exactly match the `modality.json` subkeys and whose action window equals the intended model action horizon.
4. Add `ROBOT_TYPE_CONFIG_MAP` and `DATASET_NAMED_MIXTURES` entries in a `data_registry/data_config.py` module under the benchmark or robot training-file tree so StarVLA auto-discovers it.
5. Select an `embodiment_tag`. Use `NEW_EMBODIMENT` unless the robot's action space truly matches an existing StarVLA embodiment.
6. Only after schema and registry are correct, route to [training-config](../../training-config/SKILL.md) to create or edit training YAML/launch files.
7. For evaluation or robot execution, route to [policy-deployment](../../policy-deployment/SKILL.md) and [benchmark-evaluation](../../benchmark-evaluation/SKILL.md).

## Corrected `modality.json` pattern

The concept shown by the template is right: cameras, state slices, action slices, and language must be declared explicitly. For current StarVLA parsing, keep annotation keys flat inside the top-level `annotation` object.

Use this pattern for a new custom dataset:

```json
{
  "video": {
    "cam_1": {"original_key": "observation.images.cam_1"},
    "cam_2": {"original_key": "observation.images.cam_2"}
  },
  "state": {
    "state_group_1": {"start": 0, "end": 6, "original_key": "observation.state"},
    "state_group_2": {"start": 6, "end": 7, "original_key": "observation.state"}
  },
  "action": {
    "action_group_1": {"start": 0, "end": 7, "original_key": "action"},
    "action_group_2": {"start": 7, "end": 8, "original_key": "action"}
  },
  "annotation": {
    "human.task_description": {"original_key": "task_index"}
  }
}
```

Then the matching `DataConfig.language_keys` value is:

```python
language_keys = ["annotation.human.task_description"]
```

If the project convention is `annotation.human.action.task_description`, use a flat annotation key named `human.action.task_description` and set `language_keys = ["annotation.human.action.task_description"]`.

## DataConfig skeleton

Start with the smallest version that matches the user's dataset; add video augmentation or custom dataset hooks only after the loader works.

```python
class MyRobotDataConfig:
    embodiment_tag = EmbodimentTag.NEW_EMBODIMENT

    video_keys = ["video.cam_1", "video.cam_2"]
    state_keys = ["state.state_group_1", "state.state_group_2"]
    action_keys = ["action.action_group_1", "action.action_group_2"]
    language_keys = ["annotation.human.task_description"]

    observation_indices = [0]
    state_indices = [0]
    action_indices = list(range(8))

    def modality_config(self):
        return {
            "video": ModalityConfig(delta_indices=self.observation_indices, modality_keys=self.video_keys),
            "state": ModalityConfig(delta_indices=self.state_indices, modality_keys=self.state_keys),
            "action": ModalityConfig(delta_indices=self.action_indices, modality_keys=self.action_keys),
            "language": ModalityConfig(delta_indices=self.observation_indices, modality_keys=self.language_keys),
        }

    def transform(self):
        return ComposedModalityTransform(transforms=[
            StateActionToTensor(apply_to=self.state_keys),
            StateActionTransform(
                apply_to=self.state_keys,
                normalization_modes={k: "min_max" for k in self.state_keys},
            ),
            StateActionToTensor(apply_to=self.action_keys),
            StateActionTransform(
                apply_to=self.action_keys,
                normalization_modes={k: "min_max" for k in self.action_keys},
            ),
        ])
```

Registry exports:

```python
ROBOT_TYPE_CONFIG_MAP = {
    "my_robot": MyRobotDataConfig(),
}

DATASET_NAMED_MIXTURES = {
    "my_robot_smoke": [
        ("my_dataset_lerobot", 1.0, "my_robot"),
    ],
}

ROBOT_TYPE_TO_EMBODIMENT_TAG = {}
```

The legacy tag map can stay empty when the class variable is set. Only add a legacy override if an older integration requires it.

## Choosing normalization modes

Use the simplest mode that matches data semantics:

- Continuous bounded positions/joints: `min_max`.
- Continuous values with outliers: `q99`.
- Joint deltas or near-Gaussian signals: `mean_std`.
- Binary gripper/open-close signals: `binary`.

Keep action and deployment normalization aligned. If a checkpoint was trained with `min_max` but the client expects `q99`, the model may run without shape errors while producing unusable actions.

## Handling action mode conversions

If stored actions are absolute but the task needs deltas or relative actions, configure data-side `action_mode` in `datasets.vla_data` rather than editing the raw parquet blindly.

- Set `action_mode: delta` to use action differences, with the first action relative to the current state.
- Set `action_mode: rel` to make actions relative to the current state.
- Use `action_mode_apply_keys` to apply conversion only to selected action keys, such as joints but not gripper.
- Use `action_mode_state_map` when action and state key names do not match by replacing `action.` with `state.`.

Changing action mode changes statistics cache compatibility and may rebuild `meta/stats_gr00t.json`.

## Template caveats to preserve in handoff

- The template launch script is reference-only because it starts training and contains environment-specific distributed settings. Do not bundle it as a data-integration runtime helper.
- The template training YAML is reference-only for this sub-skill; only the data fields (`dataset_py`, `data_root_dir`, `data_mix`, `video_backend`) are relevant here. Route model/trainer fields elsewhere.
- The template policy bridge is reference-only for this sub-skill because it loads checkpoints and defines benchmark request/response behavior.
- If an example `modality.json` omits state/action `original_key`, StarVLA may use schema defaults. For new integrations, write `original_key` explicitly for readability.
- If copying a conceptual annotation hierarchy, convert it to the flat annotation-subkey form required by the current parser.

## Minimal self-review before training

- `modality.json` validates with no errors.
- Every `DataConfig` key has a matching `modality.json` subkey.
- Every `DATASET_NAMED_MIXTURES` robot type exists in `ROBOT_TYPE_CONFIG_MAP`.
- Every mixture dataset subdir exists under the selected `data_root_dir` in the user's environment.
- `len(action_indices)` equals the intended action horizon.
- Normalization modes match state/action semantics.
- `embodiment_tag` is explicit.
- No policy/evaluation bridge is attempted until dataset loading and statistics are correct.

## Evidence notes

This reference adapts StarVLA's custom-dataset template assets plus observed benchmark registries. Training and policy templates are intentionally summarized here and routed to their owning sub-skills.

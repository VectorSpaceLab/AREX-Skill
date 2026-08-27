# Data integration troubleshooting

Use this page to localize StarVLA data failures before changing model/training code. If the symptom belongs to launch planning, policy serving, or simulator setup, follow the route links in the relevant section.

## `Please provide a meta/modality.json file`

Likely causes:

- The dataset subdir in `DATASET_NAMED_MIXTURES` is wrong relative to `data_root_dir`.
- The LeRobot dataset was downloaded/converted but StarVLA's `meta/modality.json` was not copied into that dataset's `meta/` directory.
- The user points `data_root_dir` at the dataset itself instead of its parent while the mixture entry also includes the dataset name.

Fix:

1. Resolve the mixture entry `(dataset_subdir, weight, robot_type)`.
2. Confirm that `data_root_dir / dataset_subdir / meta / modality.json` exists.
3. Validate the JSON with `scripts/validate_modality_json.py`.
4. Check that the selected `robot_type` exists in `ROBOT_TYPE_CONFIG_MAP`.

## Language conditioning is empty, wrong, or constant

Likely causes:

- The annotation field uses an `original_key` other than `task_index`.
- `DataConfig.language_keys` does not match the flat annotation subkey in `modality.json`.
- The dataset task metadata does not contain the task indices referenced by the parquet rows.

Fix:

- For `language_keys = ["annotation.human.task_description"]`, `modality.json` must contain `"annotation": {"human.task_description": {"original_key": "task_index"}}`.
- For `language_keys = ["annotation.human.action.task_description"]`, use the flat key `human.action.task_description`.
- Do not use nested annotation objects unless the StarVLA parser has been changed to support them.
- Validate with `scripts/validate_modality_json.py --language-key <annotation-subkey> <modality.json>` when using a non-default language key.

## `data_mix` not registered

Likely causes:

- The YAML `datasets.vla_data.data_mix` value is not a key in `DATASET_NAMED_MIXTURES`.
- The custom `data_registry/data_config.py` was placed outside the auto-discovered `examples/**/train_files/data_registry/` pattern.
- The registry module fails to import because of a syntax error or an unavailable dependency.
- Two integrations reused names and a later registry update overwrote the intended mixture.

Fix:

1. Inspect registry names, not training launch logs.
2. Ensure the module exports `DATASET_NAMED_MIXTURES` at top level.
3. Ensure every mixture entry's `robot_type` is present in `ROBOT_TYPE_CONFIG_MAP`.
4. Use unique, descriptive mixture names for custom benchmarks.

Training launch edits belong in [training-config](../../training-config/SKILL.md).

## Missing `embodiment_tag` warning

Likely causes:

- A custom `DataConfig` class did not set `embodiment_tag`.
- An older example relies on `ROBOT_TYPE_TO_EMBODIMENT_TAG` legacy overrides.

Fix:

- Add `embodiment_tag = EmbodimentTag.NEW_EMBODIMENT` for a new robot unless an existing tag's action semantics and dimensions truly match.
- Prefer the class variable over a legacy map entry.
- If the model was trained with a specific embodiment tag, keep the same tag for evaluation/deployment.

## Video backend import, codec, or frame-read failures

Likely causes:

- `decord` is not installed but `video_backend: decord` is configured.
- PyAV/FFmpeg cannot decode the dataset's video container.
- OpenCV opens the file but frame seeking fails for variable-frame-rate or unusual codecs.
- Image-only LeRobot data is being treated as a video-backed dataset, or vice versa.

Fix:

- Try a different configured backend: `torchvision_av`, `pyav`, `opencv`, `decord`, or `torchcodec` if available.
- Verify that `meta/info.json` video features and `modality.json.video.*.original_key` point to the same LeRobot feature names.
- If backend installation is the issue, fix the StarVLA environment rather than editing schema.
- If the failure only happens inside a simulator or policy server, route to [benchmark-evaluation](../../benchmark-evaluation/SKILL.md) or [policy-deployment](../../policy-deployment/SKILL.md).

## Statistics cache mismatch or rebuild loop

Likely causes:

- `meta/stats_gr00t.json` was created by an older StarVLA cache format.
- `action_mode` changed from `abs` to `delta`/`rel`, or back.
- `action_mode_apply_keys` or `action_mode_state_map` changed but the old cache remains.
- Multiple processes or jobs are racing to create the cache in a shared dataset directory.
- The parquet data changed without clearing the old cache.

Fix:

1. Treat `meta/stats_gr00t.json` as a generated StarVLA cache.
2. Allow StarVLA to rebuild stale caches, or remove the stale cache deliberately after confirming the dataset has not been corrupted.
3. Keep action-mode config stable once training starts.
4. Preserve the run-level `dataset_statistics.json` with the checkpoint; deployment uses it for normalization/unnormalization.

## Action normalization mismatch

Symptoms:

- Training loss appears finite but rollout actions are too small, too large, or stuck at gripper extremes.
- Deployment client/server dimensions match, but unnormalized actions are physically wrong.
- A gripper dimension is normalized as continuous or a continuous joint is thresholded as binary.

Likely causes:

- `StateActionTransform.normalization_modes` does not match the data field semantics.
- Policy/deployment unnormalization expects a different set or order of action keys than training used.
- `action_mode` converted actions to deltas/relative values but deployment expects absolute values.
- A checkpoint is paired with the wrong `dataset_statistics.json`.

Fix:

- Re-check `DataConfig.action_keys` order and each action slice width.
- Confirm the normalization mode for every state/action key.
- Confirm the action statistics file came from the same training run/checkpoint.
- Route request/response and server metadata debugging to [policy-deployment](../../policy-deployment/SKILL.md).

## Action horizon or chunk-size mismatch

Symptoms:

- The model config says `action_horizon: 8` but `DataConfig.action_indices` has length 16 or 50.
- VM4A/ACT/Diffusion Policy recipes fail with shape errors.
- The policy server returns an action chunk size different from the client or evaluator expects.

Fix:

- Set `len(action_indices)` equal to the model/training horizon for the selected recipe.
- Use separate robot types or `DataConfig` subclasses when the same dataset is used by different horizons, such as ACT versus Diffusion Policy.
- Route YAML and launch changes to [training-config](../../training-config/SKILL.md).
- Route client/server action chunk handling to [policy-deployment](../../policy-deployment/SKILL.md).

## State/action key not found in metadata

Likely causes:

- `DataConfig.state_keys` or `action_keys` uses a key not present under `state` or `action` in `modality.json`.
- The `modality.json` field is nested or prefixed incorrectly.
- The `original_key` column does not exist in the parquet data.
- The state/action slice exceeds the stored vector width.

Fix:

1. Convert each `DataConfig` key to its `modality.json` location by removing the modality prefix.
2. Validate all `start` and `end` ranges.
3. Inspect the LeRobot parquet column names and vector widths from the user's dataset environment.
4. Keep state/action group names stable after statistics are computed.

## Dataset mixture sampling surprises

Likely causes:

- Duplicate `(dataset_subdir, robot_type)` entries are skipped during mixture construction.
- Sampling weights do not compensate for very different trajectory counts.
- `balance_dataset_weights` or `balance_trajectory_weights` changed effective sampling.

Fix:

- Remove accidental duplicates.
- Make weights explicit and document their purpose.
- Decide whether balancing flags should be enabled for the experiment; route training implications to [training-config](../../training-config/SKILL.md).

## Source artifact decisions

- Custom training launch scripts are reference-only for this sub-skill because they start distributed training and depend on the user's hardware and environment.
- Policy/benchmark bridge scripts are reference-only for this sub-skill because they load checkpoints and define serving/evaluation contracts.
- The safe bundled helper here only validates `modality.json` and does not import StarVLA or open data files.

# Auxiliary Analysis Troubleshooting

Use this reference before rerunning an auxiliary command with broader dependencies or heavier settings. These commands can invoke segmentation, load model weights, and write JSON/PNG outputs, so small configuration mistakes can become expensive.

## Fast Triage

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: xgboost` | Phase, modality, or XGBoost body-stats backend needs XGBoost. | Install `xgboost` in the runtime environment, or for body stats use default `--model_type cnn` if CNN dependencies are available. |
| `CNN body-stats inference requires timm` | Default body-stats CNN backend cannot construct EfficientNet-style models. | Install `timm`, then rerun the body-stats command. |
| `CNN body-stats inference requires monai` | CNN checkpoint metadata contains MONAI objects. | Install `monai`; keep PyTorch compatible with the runtime backend. |
| `CNN body-stats inference requires PyTorch` | Body-stats CNN path cannot create tensors or load checkpoints. | Install a compatible `torch`; if GPU setup is uncertain, start with `-d cpu`. |
| `Error: antspyx package not installed` or missing `ants` | Evans index registration dependency is missing. | Install `antspyx`; the import name is `ants`. |
| `Error: blosc package not installed` | Evans index serialization dependency is missing. | Install `blosc`. |
| Body-stats XGBoost fails on `tissue_types` or license | Tissue-type segmentation is license-gated. | Set up a valid TotalSegmentator license before running XGBoost body stats, or use CNN body stats if appropriate. Route license mechanics to runtime configuration. |
| Output JSON missing or empty | Parent directory does not exist, path is unwritable, or command exited before final write. | Create the output directory, use an absolute or pipeline-owned relative path, rerun with `--debug`/non-quiet if needed, and check stderr. |
| Evans JSON fields are `null` | Brain, skull, or frontal-horn segmentation was empty. | Inspect the preview PNG and verify the input contains the full brain/skull; do not treat `null` as a valid measurement. |
| Phase result asks for rerun or is slow | Existing stats were not supplied or were missing required keys. | If compatible `statistics.json` already exists, pass it with `-s`; otherwise budget for internal segmentation. |
| Body-stats result has high `stddev` or implausible value | Ensemble disagreement, out-of-distribution age/FOV/body habitus, or narrow FOV. | Review input FOV and patient age; avoid use for age under 16; prefer larger thorax+abdomen FOV when possible. |
| Modality output seems wrong after normalization | Default global-intensity classifier expects meaningful original intensities. | Rerun with `-n`, which uses normalized ROI intensities but is slower because it runs internal segmentation. |

## Dependency-Specific Recovery

### XGBoost tools

Affected commands:

- `totalseg_get_phase`
- `totalseg_get_modality`
- `totalseg_get_body_stats --model_type xgboost`

Recovery steps:

1. Verify the failure is import-time or model-load related before changing the command.
2. Install `xgboost` in the environment that runs the console script.
3. For body stats, decide whether XGBoost is necessary; the default CNN backend is documented as faster and more accurate in the body-stats reference.
4. If the command uses a custom classifier path, verify the path points to the expected classifier family: phase expects a pickle, modality expects packaged fold JSON files, and body-stats XGBoost expects a base model path or default weight directory.

### Body-stats CNN dependencies

Affected command:

- `totalseg_get_body_stats` with default `--model_type cnn`

Recovery steps:

1. Install or repair `torch` first because the CNN path creates tensors and loads checkpoints.
2. Install `timm` for model construction.
3. Install `monai` if checkpoint loading reports MONAI metadata or `MetaTensor` errors.
4. Rerun with `-d cpu` if CUDA/MPS availability is uncertain; device/backend setup belongs to runtime configuration.
5. Use `--only_weight` to reduce target count when only weight is needed, but expect the model file/dependency requirements for that target to remain.

### Evans index registration dependencies

Affected command:

- `totalseg_evans_index`

Recovery steps:

1. Install `antspyx` and `blosc`; the tool checks both before calculation.
2. If registration fails after dependencies import, rerun with `-v` and inspect whether the input is a full brain/skull CT.
3. If the output JSON contains `null` fields, inspect the PNG. Empty segmentation usually means the input is not suitable, not that the numeric calculation should be retried unchanged.
4. Avoid rerunning repeatedly on cropped/non-brain images; fix input selection first.

## License-Gated Body Stats

Body-stats XGBoost extracts tissue-type slice features using `tissue_types` for CT or `tissue_types_mr` for MR. These tasks require a valid TotalSegmentator license.

Use this staged plan:

1. If the user only needs ordinary body stats, prefer CNN: `totalseg_get_body_stats -i image.nii.gz -o body_stats.json -m ct --model_type cnn`.
2. If XGBoost is required, confirm license setup before the run; pass `-l <license_number>` only when the surrounding workflow is already allowed to handle the secret.
3. Do not store license numbers in scripts, generated skill content, logs, or command templates.
4. Route license acquisition, persistence, and config-file mechanics to runtime configuration.

## Avoiding Expensive Reruns

- Contrast phase supports `-s <statistics.json>`. Use it when the stats were produced with compatible TotalSegmentator settings and include the required ROI intensity keys.
- Body-stats CLI does not expose an existing-statistics argument even though the Python function has internal parameters; do not invent a CLI flag for it.
- Modality default mode is fast global-intensity inference. Only use `-n` when normalization makes global intensities unreliable because `-n` runs internal segmentation.
- Evans index always runs internal brain/skull and ventricle segmentations; use it only when the input is a suitable skull/brain CT and the PNG overlay will be reviewed.

## Output Path Fixes

- Create parent directories before running commands; these CLIs write JSON/PNG directly and do not create arbitrary parent directories for you.
- Use `.json` for machine-readable outputs and `.png` for Evans previews.
- If a command prints a result but no file appears, check whether the selected flag is optional: body-stats `-o` is optional, but phase/modality/Evans output paths are required.
- For automation, fail closed when expected keys are absent: phase needs `pi_time`, `phase`, `probability`, and `stddev`; modality needs `modality` and `probability`; body stats needs the requested target keys; Evans needs all numeric keys or explicit `null` handling.

## When To Route Away

- Unknown TotalSegmentator tasks, ROI names, or license-required task inventory: `../capability-discovery/SKILL.md`.
- How to run a general segmentation or produce `statistics.json`: `../segmentation-workflows/SKILL.md` and `../outputs-and-statistics/SKILL.md`.
- Installing TotalSegmentator, downloading weights, offline cache setup, device compatibility, license persistence, or usage telemetry: `../runtime-configuration/SKILL.md` when present.
- DICOM folder/zip layout, DICOM SEG/RTSTRUCT outputs, or `crop_to_body`: `../dicom-and-formats/SKILL.md` when present.

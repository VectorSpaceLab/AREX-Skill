# Advanced Training Troubleshooting

Use this reference before spending GPU days or copying large datasets. Most failures in this area are setup, data-contract, or benchmark-comparability issues rather than TotalSegmentator inference bugs.

## Routing Checks

| User request | Action |
| --- | --- |
| "Segment this CT/MR image" | Route to [`../../segmentation-workflows/SKILL.md`](../../segmentation-workflows/SKILL.md); do not train. |
| "Which task/class should I use?" | Route to [`../../capability-discovery/SKILL.md`](../../capability-discovery/SKILL.md). |
| "Install TotalSegmentator or fix CUDA/weights/license" | Route to [`../../runtime-configuration/SKILL.md`](../../runtime-configuration/SKILL.md). |
| "Parse reports/statistics/masks after inference" | Route to [`../../outputs-and-statistics/SKILL.md`](../../outputs-and-statistics/SKILL.md). |
| "Retrain/evaluate/contribute a model" | Stay in this sub-skill. |

## Failure Matrix

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError: 'nnUNet_raw'` or missing preprocessed output | nnU-Net environment variables are unset or unwritable. | Set `nnUNet_raw`, `nnUNet_preprocessed`, and `nnUNet_results` to large writable storage; create directories before conversion. |
| `nnUNetv2_plan_and_preprocess` cannot find the dataset | Dataset ID and `DatasetXXX_*` folder name do not match, or the folder is under the wrong `nnUNet_raw`. | Verify the raw folder name starts with the same numeric ID passed to `-d`; avoid IDs that collide with existing datasets. |
| Conversion produces empty or incomplete labels | Source `segmentations/<class>.nii.gz` files are missing, class-map names do not match the dataset, or masks were combined in the wrong order. | Check every selected class name against the subject mask files; inspect unique label values in combined labels; treat missing masks as a data issue, not normal background. |
| Training starts but runs for days or exhausts GPU memory | Full-resolution 3D nnU-Net is expensive and the maintainer recipe uses `3d_fullres`. | Stop and confirm the user approved GPU time; reduce scope, use fewer experiments, or plan hardware explicitly. Do not silently switch benchmark settings if comparability matters. |
| Prediction output is missing cases | `imagesTs` naming is wrong, prediction command used the wrong input folder, or fold/checkpoint is unavailable. | Confirm files are named `<subject>_0000.nii.gz`; check the trained fold `0` exists under `nnUNet_results`; rerun prediction only after validating paths. |
| Evaluation fails importing `surface_distance` or `p_tqdm` | Optional benchmark dependencies are missing. | Install the evaluation dependencies in the research environment before rerunning; keep this separate from ordinary inference runtime setup. |
| Evaluation reports poor Dice for every class | Predictions and ground truth use different label orders or class maps. | Reconfirm the selected `class_map_part_*`, combined-label value order, and prediction dataset ID. Do not compare outputs across different maps. |
| Evaluation skips many classes as `NaN` | The ground truth class is absent in many test cases, so per-class means exclude those subjects. | Report class support and absent-class handling; do not treat `NaN` as success or failure without context. |
| Results do not match published TotalSegmentator v2 | Public retraining is not the released v2 training run. | State the known caveats: v2 used additional non-public data, public data contains blurred faces, and training is nondeterministic. |
| User asks to run release, anonymization, or weight upload scripts | Maintainer-only workflow with credentials and privacy risk. | Decline automatic execution unless authorized explicitly; review the plan at a high level and suggest maintainer contact. |
| User asks to deploy a TotalSegmentator server | Server deployment is outside this sub-skill. | Do not copy service files; route to project-specific deployment guidance if the user provides it. |

## Preflight Checklist for Retraining

Before launching `nnUNetv2_train`, record the user-approved choices:

- Dataset source, license, and privacy status.
- Dataset ID and folder name.
- Class map or label list.
- Train/validation/test split source.
- nnU-Net raw, preprocessed, and results roots.
- Trainer, configuration, fold, and prediction flags.
- GPU count, memory expectation, storage budget, and runtime budget.
- Evaluation metrics and reference baseline.

If any item is unknown, pause and ask rather than starting a heavyweight job.

## Benchmark Comparability Checklist

A result is comparable to the maintainer recipe only if all of these match:

- Same public dataset version and `meta.csv` split.
- Same five-part CT class map or explicitly matching task-specific class map.
- Same conversion order from binary masks to combined labels.
- Same `3d_fullres` configuration and `nnUNetTrainerNoMirroring` trainer.
- Same fold `0` prediction with `--disable_tta`.
- Same metric definitions, including 3.0 mm surface Dice tolerance and expected voxel spacing for surface-distance calculation.

If the user changed any item, present the result as an experiment, not a reproduction.

## Maintainer-Only Boundaries

Do not run or recreate these as default runtime actions:

- Package release publishing to PyPI.
- Git tagging or changelog/version commits.
- Weight anonymization, archive creation, or upload.
- Server/service deployment.
- Any command requiring private credentials, private data paths, or protected patient data.

It is acceptable to summarize risks, draft checklists, or tell the user what evidence an authorized maintainer should review.

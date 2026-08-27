# Training and Evaluation Reference

This reference distills TotalSegmentator maintainer workflows for advanced research work. It is intentionally not a runnable launcher: the workflows copy full imaging datasets, require nnU-Net v2, and can run for days on GPU hardware.

## When to Use This

Use these notes for requests such as:

- "Retrain TotalSegmentator on the public dataset."
- "Convert TotalSegmentator-style masks into nnU-Net format."
- "Evaluate a trained nnU-Net model against the TotalSegmentator benchmark split."
- "I trained a model for a new anatomy and want to contribute it."
- "Explain which package-management steps are maintainer-only."

Do not use this for ordinary segmentation. Route ordinary inference to [`../../segmentation-workflows/SKILL.md`](../../segmentation-workflows/SKILL.md).

## Baseline Workflow Shape

The maintainer training guide follows this order:

1. Install and configure nnU-Net v2.
2. Obtain the public CT TotalSegmentator dataset, including `meta.csv`, subject folders, `ct.nii.gz`, and per-class binary masks under each subject’s `segmentations/` directory.
3. Convert the dataset into nnU-Net v2 format.
4. Run nnU-Net planning/preprocessing for a dataset ID.
5. Train a `3d_fullres` model on fold `0` with `nnUNetTrainerNoMirroring`.
6. Predict the test images with test-time augmentation disabled.
7. Evaluate per-class Dice and 3 mm surface Dice against the held-out labels.

The public CT workflow is split into five part datasets because TotalSegmentator’s full class set was trained as multiple nnU-Net models:

| Dataset ID pattern | Suggested folder suffix | Class map |
| --- | --- | --- |
| `101` | `Dataset101_TotalSegmentator_public_part1` | `class_map_part_organs` |
| `102` | `Dataset102_TotalSegmentator_public_part2` | `class_map_part_vertebrae` |
| `103` | `Dataset103_TotalSegmentator_public_part3` | `class_map_part_cardiac` |
| `104` | `Dataset104_TotalSegmentator_public_part4` | `class_map_part_muscles` |
| `105` | `Dataset105_TotalSegmentator_public_part5` | `class_map_part_ribs` |

Use different dataset IDs if those IDs already exist in the user’s nnU-Net workspace.

## Environment Assumptions

Before any expensive command, verify:

- `nnUNet_raw`, `nnUNet_preprocessed`, and `nnUNet_results` point to writable storage with enough space for copied NIfTI images, preprocessed arrays, checkpoints, and predictions.
- The TotalSegmentator Python package is importable if using its class-map constants for conversion or evaluation.
- nnU-Net v2 console scripts such as `nnUNetv2_plan_and_preprocess`, `nnUNetv2_train`, and `nnUNetv2_predict` are on `PATH`.
- PyTorch sees the intended GPU, or the user knowingly accepts CPU impracticality.
- The dataset license and patient-data handling rules allow copying, preprocessing, training, and benchmark reporting.

Example environment placeholders:

```bash
export nnUNet_raw=<nnunet-raw>
export nnUNet_preprocessed=<nnunet-preprocessed>
export nnUNet_results=<nnunet-results>
```

## Dataset Conversion Contract

The TotalSegmentator converter consumes a public-dataset-style tree:

```text
TotalSegmentator_dataset/
  meta.csv
  <subject_id>/
    ct.nii.gz
    segmentations/
      <class_name>.nii.gz
```

`meta.csv` is semicolon-separated and contains an `image_id` column plus a `split` column with `train`, `val`, or `test` values. The train and validation subjects become nnU-Net training cases; test subjects become held-out test images and labels.

For each target part dataset:

1. Create `imagesTr/`, `labelsTr/`, `imagesTs/`, and `labelsTs/` under the nnU-Net raw dataset folder.
2. For each `train` and `val` subject, copy `ct.nii.gz` to `imagesTr/<subject_id>_0000.nii.gz`.
3. For each `test` subject, copy `ct.nii.gz` to `imagesTs/<subject_id>_0000.nii.gz`.
4. Convert per-class binary masks into one combined label NIfTI named `<subject_id>.nii.gz` in `labelsTr/` or `labelsTs/`. Background is `0`; class labels start at `1` in the selected class-map order.
5. Write `dataset.json` under the raw dataset folder.
6. Write `splits_final.json` under `nnUNet_preprocessed/<DatasetName>/` with fold `0` containing the train and validation subject lists.

The converter’s `dataset.json` fields are:

```json
{
  "name": "TotalSegmentator",
  "description": "Segmentation of TotalSegmentator classes",
  "reference": "https://zenodo.org/record/6802614",
  "licence": "Apache 2.0",
  "release": "2.0",
  "channel_names": {"0": "CT"},
  "labels": {"background": 0, "<class_name>": 1},
  "numTraining": 0,
  "file_ending": ".nii.gz",
  "overwrite_image_reader_writer": "NibabelIOWithReorient"
}
```

Populate `labels` with every class from the chosen class map and set `numTraining` to `len(train_subjects) + len(val_subjects)`.

Use the installed class-map constants when available:

```python
from totalsegmentator.map_to_binary import class_map, class_map_5_parts
print(class_map_5_parts.keys())
print(class_map.keys())
```

Validate conversion before preprocessing:

- Every `imagesTr` file has suffix `_0000.nii.gz`.
- Every training image has a matching `labelsTr/<subject_id>.nii.gz`.
- Test labels exist if benchmark evaluation is planned.
- The combined labels contain only `0..N` for the selected class map.
- Missing source masks are investigated instead of silently treated as absent anatomy.

## nnU-Net Command Patterns

After conversion, run planning/preprocessing for each dataset ID:

```bash
nnUNetv2_plan_and_preprocess -d 101 -pl ExperimentPlanner -c 3d_fullres -np 2
```

Train fold `0` with the no-mirroring trainer used by the maintainer recipe:

```bash
nnUNetv2_train 101 3d_fullres 0 -tr nnUNetTrainerNoMirroring
```

Expect training to take several days for full-resolution 3D models. Do not start this command unless the user has approved GPU time, storage use, and checkpoint output.

Predict the held-out test split from the raw dataset folder:

```bash
nnUNetv2_predict \
  -i "$nnUNet_raw/Dataset101_TotalSegmentator_public_part1/imagesTs" \
  -o "$nnUNet_raw/Dataset101_TotalSegmentator_public_part1/labelsTs_predicted" \
  -d 101 \
  -c 3d_fullres \
  -tr nnUNetTrainerNoMirroring \
  --disable_tta \
  -f 0
```

The benchmark recipe disables test-time augmentation. If a user enables TTA or changes trainer/planner/configuration, note that results are no longer directly comparable to the maintainer recipe.

## Evaluation Contract

The maintainer evaluation script computes two per-class metrics from combined-label NIfTI files:

- `dice-<class_name>`: binary Dice score for each class.
- `surface_dice_3-<class_name>`: surface Dice at 3.0 mm tolerance using voxel spacing `[1.5, 1.5, 1.5]`.

Inputs:

```text
labelsTs/              # ground-truth combined labels named <subject_id>.nii.gz
labelsTs_predicted/    # predicted combined labels named <subject_id>.nii.gz
class_map_part_*       # one of the five CT public part class maps
```

Dependencies include `nibabel`, `numpy`, `pandas`, `p_tqdm`, and Google DeepMind’s `surface-distance` package. The script parallelizes per-subject metric calculation and prints per-ROI means. Cases where the ground truth class is absent are excluded as `NaN`; cases where the ground truth class is present and prediction is empty score `0`.

Reference command pattern:

```bash
python evaluate_totalseg_part.py labelsTs labelsTs_predicted class_map_part_organs
```

If no local evaluation helper exists, implement one from the contract above instead of assuming source-repository scripts are present.

## Interpreting Results

Compare results only when the data, split, class map, trainer, prediction flags, and evaluation code match the benchmark recipe.

Known reference evidence:

- The CT high-resolution reference JSON contains `dice` and `normalized_surface_distance` for 104 classes, with mean Dice about `0.942` and mean normalized surface distance about `0.965`.
- The MR reference JSON contains `dice` and `normalized_surface_distance` for 80 classes, with mean Dice about `0.825` and mean normalized surface distance about `0.901`.
- The text evaluation output reports per-class Dice and `surface_dice_3` values.
- Training is not deterministic; the mean Dice across all classes can vary by up to roughly one Dice point.
- Public retraining will not exactly match released TotalSegmentator v2 because the released v2 model used additional non-public data, and the public dataset contains blurred faces while the released model training did not.

Report results with caveats. Do not claim regression or superiority from a single run unless the benchmark setup is identical and the variation is larger than expected nondeterminism.

## New Anatomy or Model Contribution Checklist

For a user who wants to add or contribute a new model, collect:

- Target modality and acquisition constraints, such as CT, MR, TOF MRI, CBCT, contrast phase, resolution, and body region.
- Class names, label definitions, expected overlaps, and whether classes map to existing TotalSegmentator tasks.
- Dataset size, annotation source, data license, patient privacy state, and whether public sharing is possible.
- Train/validation/test split policy and whether an external validation set exists.
- nnU-Net dataset ID, trainer, configuration, folds, preprocessing choices, and inference flags.
- Evaluation metrics, expected failure modes, and comparison baseline.
- Packaging goal: private research model, publication supplement, or upstream TotalSegmentator contribution.

If the goal is upstream inclusion, advise contacting the TotalSegmentator maintainers with the model scope, evidence, paper or dataset citation, license terms, and reproducibility details. A user-provided nnU-Net model for unsupported structures may be eligible for integration, but upstream acceptance is a maintainer decision.

## Package-Management and Release Boundary

Package maintenance evidence includes pre-commit checks, version updates, changelog updates, tags, source/wheel builds, PyPI upload, and weight-release preparation. These are not normal user workflows.

Safe guidance:

- It is fine to explain that release steps are maintainer-only and require repository ownership, credentials, and data-governance review.
- It is fine to review a release plan for missing checks without running it.
- Do not run publishing commands, create tags, upload distributions, anonymize weights, or prepare release archives unless explicitly instructed by an authorized maintainer.
- Release publishing, weight anonymization, and server deployment scripts are intentionally not bundled in this sub-skill.

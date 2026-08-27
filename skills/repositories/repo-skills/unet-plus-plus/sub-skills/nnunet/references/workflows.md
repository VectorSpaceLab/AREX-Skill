# nnU-Net workflows

## 1. Convert a Decathlon-style task folder

Use `nnUNet_convert_decathlon_task` when the source data is a Medical
Segmentation Decathlon task folder with 4D NIfTI files.

Typical flow:

1. Confirm the input folder is named `TaskXX_Name`.
2. Remove hidden files from `imagesTr`, `labelsTr`, and `imagesTs`.
3. Run the conversion command with the desired process count.
4. Verify the output task folder structure before planning.

This workflow is the right place to reject malformed task layouts.

## 2. Plan and preprocess

Use `nnUNet_plan_and_preprocess` after the raw data root and path variables are
sane.

Recommended order:

1. Set `nnUNet_raw_data_base`, `nnUNet_preprocessed`, and `RESULTS_FOLDER`.
2. Verify dataset integrity when the user wants a safety check.
3. Run planning for the target task ids.
4. Decide whether to skip preprocessing with `-no_pp`.

This step is expensive enough that it should not be treated as a trivial smoke
check.

## 3. Train or validate

Use `nnUNet_train` for the common single-node training path.

Key choices:

- `network`: `3d_fullres` is the common default in the inspected snapshot.
- `network_trainer`: `nnUNetPlusPlusTrainerV2` for the UNet++ variant.
- `task`: task name or id.
- `fold`: `0`-`5` or `all`.

Typical follow-up actions:

- `-val` for validation only.
- `-c` to continue training.
- `--npz` when you will ensemble later.
- `--fp32` only if mixed precision must be disabled.

## 4. Predict from a trained model

Use `nnUNet_predict` when you already have trained weights or downloaded
pretrained models.

Important details:

- Input files must be named `CASENAME_XXXX.nii.gz`.
- `--lowres_segmentations` only matters for cascade inference.
- `--disable_tta` trades accuracy for speed.
- `--overwrite_existing` can replace old predictions, so use it deliberately.
- `--disable_mixed_precision` is usually not the default choice.

## 5. Ensemble and postprocess

Use `nnUNet_ensemble` and `nnUNet_determine_postprocessing` after validation
outputs exist.

- `nnUNet_determine_postprocessing` decides which postprocessing settings to
  use for a model folder.
- `nnUNet_ensemble` merges `.npz` outputs from multiple folders and can apply
  a saved postprocessing JSON.

## 6. Choose the best model family

Use `nnUNet_find_best_configuration` when multiple model families have been
trained and the user wants the best test-time plan.

This helper can emit concrete `nnUNet_predict` and `nnUNet_ensemble` commands
for the chosen model combination.

## 7. Pretrained models

Use the pretrained-model helpers when the user wants to:

- list available TaskXXX pretrained models,
- inspect the dataset/modality summary,
- download by task name or URL,
- install from zip, or
- export a trained model archive.

These are network- and license-sensitive workflows.

## 8. Advanced trainer repair

Use `nnUNet_change_trainer_class` when a checkpoint exists but its trainer name
must be rewritten for inference compatibility.

This is an advanced repair workflow; back up the model folder first.

## 9. Advanced multi-GPU routes

`nnUNet_train_DP` and `nnUNet_train_DDP` are available, but the inspected
snapshot showed they should be treated cautiously because their code paths are
more brittle than the default single-node training route.

## Best native verification candidate

The safe native unit test to keep for later verification is:

- `pytorch/tests/test_steps_for_sliding_window_prediction.py`

It exercises the sliding-window helper without requiring a full dataset.

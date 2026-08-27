# Inference and Evaluation CLI Reference

## Choose the Prediction Route

Use `nnUNetv2_predict` when the trained model lives in the standard nnU-Net results layout and can be resolved from dataset, trainer, plans, and configuration:

```bash
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET001_Example -c 3d_fullres
```

Use `nnUNetv2_predict_from_modelfolder` when the model folder is explicit, such as an exported/copied model or an environment where `nnUNet_results` is not set:

```bash
nnUNetv2_predict_from_modelfolder -i INPUT_FOLDER -o OUTPUT_FOLDER -m MODEL_FOLDER
```

Both routes initialize `nnUNetPredictor` and call `predict_from_files`. The input folder must contain one file per channel per case using `{case_id}_0000{file_ending}`, `{case_id}_0001{file_ending}`, and so on, matching the model's `dataset.json`.

## `nnUNetv2_predict`

Required:

- `-i INPUT_FOLDER`: source images with training-time channel suffixes and file ending.
- `-o OUTPUT_FOLDER`: output segmentations; created if missing.
- `-d DATASET_NAME_OR_ID`: dataset id or name used to resolve the result folder.
- `-c CONFIGURATION`: trained configuration, for example `2d`, `3d_fullres`, `3d_lowres`, or `3d_cascade_fullres`.

Common optional flags:

- `-p nnUNetPlans`: plans identifier; default is `nnUNetPlans`.
- `-tr nnUNetTrainer`: trainer class name; default is `nnUNetTrainer`.
- `-f 0 1 2 3 4` or `-f all`: folds to use; default is five folds.
- `-chk checkpoint_final.pth`: checkpoint file within each fold; default is final checkpoint.
- `-step_size 0.5`: sliding-window step size; larger is faster but can reduce quality.
- `--disable_tta`: disables mirroring test-time augmentation; faster but usually less accurate.
- `--save_probabilities`: writes `.npz` probability maps and `.pkl` metadata; required before ensembling.
- `--continue_prediction`: skips already completed outputs instead of overwriting them.
- `-npp 3`: preprocessing worker count; can also default from `nnUNet_npp`.
- `-nps 3`: segmentation export worker count; can also default from `nnUNet_nps`.
- `-prev_stage_predictions FOLDER`: supplies prior-stage segmentations for cascades.
- `-num_parts N -part_id K`: split one input folder across multiple prediction jobs; `part_id` is zero-based and must be less than `num_parts`.
- `-device cuda|cpu|mps`: device type. Select a specific GPU with `CUDA_VISIBLE_DEVICES`, not `-device`.
- `--disable_progress_bar`: useful for non-interactive batch jobs.
- `--not_on_device`: disables `perform_everything_on_device`; useful when cases exceed VRAM.

When both `-npp 0` and `-nps 0`, `nnUNetv2_predict` uses the sequential prediction path instead of multiprocessing.

## `nnUNetv2_predict_from_modelfolder`

Required:

- `-i INPUT_FOLDER`: source images with correct channel suffixes and file ending.
- `-o OUTPUT_FOLDER`: output segmentations.
- `-m MODEL_FOLDER`: trained model folder containing `dataset.json`, `plans.json`, and requested `fold_*` checkpoint files.

Optional flags are the same as `nnUNetv2_predict` except this route does not take `-d`, `-p`, `-tr`, `-c`, `-num_parts`, or `-part_id`. It supports `-f`, `-step_size`, `--disable_tta`, `--save_probabilities`, `--continue_prediction`/`--c`, `-chk`, `-npp`, `-nps`, `-prev_stage_predictions`, `-device`, `--disable_progress_bar`, and `--not_on_device`.

## Ensembling

`nnUNetv2_ensemble` averages probability maps from multiple prediction folders:

```bash
nnUNetv2_ensemble -i OUTPUT_2D OUTPUT_3D_FULLRES -o OUTPUT_ENSEMBLE -np 8
```

Requirements:

- Each input folder must have matching `.npz` files from predictions run with `--save_probabilities`.
- Each input folder should include compatible `dataset.json` and `plans.json`; prediction normally writes them automatically.
- Use `--save_npz` only if the ensembled probabilities are needed for another downstream ensemble.

## Postprocessing

Determine postprocessing from a validation-like prediction folder and reference labels:

```bash
nnUNetv2_determine_postprocessing -i PRED_FOLDER -ref GT_FOLDER -np 8
```

Optional metadata flags:

- `-plans_json PLANS_JSON`: required if `plans.json` is not in the prediction folder.
- `-dataset_json DATASET_JSON`: required if `dataset.json` is not in the prediction folder.
- `--remove_postprocessed`: remove temporary postprocessed outputs after selecting `postprocessing.pkl`.

Apply a selected postprocessing file:

```bash
nnUNetv2_apply_postprocessing \
  -i PRED_FOLDER \
  -o PRED_FOLDER_PP \
  -pp_pkl_file POSTPROCESSING_PKL \
  -plans_json PLANS_JSON \
  -dataset_json DATASET_JSON \
  -np 8
```

For single-configuration prediction folders, metadata is usually present. For ensemble folders or copied outputs, pass `-plans_json` and `-dataset_json` explicitly when missing.

## Evaluation

Use the dataset/plans-aware evaluator when `dataset.json` and `plans.json` are available:

```bash
nnUNetv2_evaluate_folder GT_FOLDER PRED_FOLDER -djfile DATASET_JSON -pfile PLANS_JSON -o SUMMARY_JSON -np 8
```

Use simple label-list evaluation when plans are unavailable:

```bash
nnUNetv2_evaluate_simple GT_FOLDER PRED_FOLDER -l 1 2 3 -il 255 -o SUMMARY_JSON -np 8
```

Evaluation flags:

- `-o`: output JSON; defaults to `PRED_FOLDER/summary.json`.
- `-np`: number of worker processes.
- `--chill`: do not crash when some ground-truth cases are missing predictions. Without `--chill`, missing predictions are an error.
- `-il`: ignore label for `nnUNetv2_evaluate_simple`.

## Best Configuration Selection

`nnUNetv2_find_best_configuration` compares trained configurations and optionally pairwise ensembles:

```bash
nnUNetv2_find_best_configuration DATASET001_Example -c 2d 3d_fullres 3d_lowres -f 0 1 2 3 4 -np 8
```

Important flags:

- `-p`: one or more plans identifiers; default `nnUNetPlans`.
- `-c`: one or more configurations; defaults include `2d`, `3d_fullres`, `3d_lowres`, and `3d_cascade_fullres`.
- `-tr`: one or more trainer class names; default `nnUNetTrainer`.
- `-f`: folds to compare; default `0 1 2 3 4`.
- `--disable_ensembling`: skip pairwise ensemble comparison.
- `--no_overwrite`: reuse existing merged/evaluation outputs.

Prerequisite: validation probability files must exist. Train with `--npz` or rerun validation with `--val --npz` from the training sub-skill before using this command.

Outputs are written in the dataset's results folder:

- `inference_instructions.txt`: runnable prediction, ensembling, and postprocessing commands.
- `inference_information.json`: structured selected model/ensemble metadata.

## Model Sharing Commands

Export a trained model:

```bash
nnUNetv2_export_model_to_zip -d DATASET001_Example -o model.zip -c 3d_fullres -f 0 1 2 3 4
```

Install a model zip:

```bash
nnUNetv2_install_pretrained_model_from_zip model.zip
```

Download and install from a URL:

```bash
nnUNetv2_download_pretrained_model_by_url URL
```

Pretrained weights from nnU-Net v1 are not compatible with nnU-Net v2. Treat v1 models as requiring retraining or continued v1 inference.

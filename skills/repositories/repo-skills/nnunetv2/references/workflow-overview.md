# Workflow Overview

## Required Order

nnU-Net workflows are staged. Most failures come from running a downstream command before upstream artifacts exist.

1. **Install and path setup**: package imports, `nnUNet_raw`, `nnUNet_preprocessed`, and `nnUNet_results` are available for the workflow.
2. **Data preparation**: dataset lives under `nnUNet_raw/DatasetXXX_Name` with valid `dataset.json`, `imagesTr`, `labelsTr`, and optional `imagesTs`.
3. **Planning/preprocessing**: fingerprint, plans, and preprocessed arrays exist under `nnUNet_preprocessed/DatasetXXX_Name`.
4. **Training**: one or more folds/configurations exist under `nnUNet_results/DatasetXXX_Name/TRAINER__PLANS__CONFIGURATION/fold_X`.
5. **Inference/evaluation/model selection**: prediction, ensembling, postprocessing, evaluation, and best-configuration commands use trained outputs and validation probability files.
6. **Customization**: custom trainers/planners/preprocessors/image I/O classes must be importable wherever they are selected by command names or stored checkpoints.

## Minimal End-to-End Command Shape

```bash
nnUNetv2_plan_and_preprocess -d DATASET_ID --verify_dataset_integrity
nnUNetv2_train DATASET_ID 3d_fullres 0 --npz
nnUNetv2_train DATASET_ID 3d_fullres 1 --npz
nnUNetv2_train DATASET_ID 3d_fullres 2 --npz
nnUNetv2_train DATASET_ID 3d_fullres 3 --npz
nnUNetv2_train DATASET_ID 3d_fullres 4 --npz
nnUNetv2_find_best_configuration DATASET_ID -c 2d 3d_fullres 3d_lowres
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET_ID -c CONFIGURATION
```

Adjust configurations to the plans actually created for the dataset.

## Cross-Skill Handoffs

- `data-preparation` hands off a valid dataset id/name, dataset folder, `dataset.json`, channel/file-ending assumptions, and label/region conventions.
- `planning-preprocessing` hands off generated configurations, plans identifier, preprocessed output folders, and any custom planner/preprocessor names.
- `training-configuration` hands off trainer name, plans identifier, configuration, fold list, checkpoints, validation outputs, and whether `.npz` probabilities exist.
- `inference-evaluation` hands off prediction folders, probability folders, postprocessing files, evaluation summaries, model zips, or generated inference commands.
- `customization-extension` hands off class names, import paths, `nnUNet_extTrainer` usage, package/install choices, and portability requirements for custom models.

## Safe Checks Before Expensive Runs

Use the bundled scripts for deterministic checks before launching expensive operations:

```bash
python scripts/check_nnunet_setup.py --require-commands --check-torch
python sub-skills/data-preparation/scripts/validate_dataset_json.py /path/to/nnUNet_raw/Dataset123_MyDataset --check-files
python sub-skills/planning-preprocessing/scripts/build_plan_preprocess_command.py --dataset-id 123 --verify-dataset-integrity
python sub-skills/training-configuration/scripts/plan_training_matrix.py 123 --configs 3d_fullres --folds 0 1 2 3 4 --npz
python sub-skills/inference-evaluation/scripts/check_inference_inputs.py /path/to/imagesTs /path/to/model_or_dataset_json
python sub-skills/customization-extension/scripts/list_available_nnunet_classes.py --kind trainer
```

These helpers do not run preprocessing, training, full inference, downloads, or destructive cleanup.

## Common Decision Points

- **Combined vs split preprocessing**: use `nnUNetv2_plan_and_preprocess` for new datasets; use split commands when only fingerprinting, planning, or preprocessing must be rerun.
- **`--npz` during training**: enable it when best-configuration selection or probability ensembling may be needed; recover later with `--val --npz`.
- **Folds vs `all`**: use folds `0` through `4` for cross-validation and model selection; use fold `all` for a final model after configuration decisions are made.
- **One GPU per fold vs DDP**: prefer independent folds on separate GPUs for throughput unless the single training run needs distributed training.
- **Dataset id vs name**: many commands accept either, but numeric ids are concise and reduce shell quoting issues.
- **Model-folder prediction**: use `nnUNetv2_predict_from_modelfolder` when results are not installed in `nnUNet_results`.

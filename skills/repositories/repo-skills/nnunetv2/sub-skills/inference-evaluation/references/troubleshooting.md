# Inference and Evaluation Troubleshooting

## Input Channel Naming or File Ending Errors

Symptoms:

- Prediction reports missing channels or unexpected files.
- Cases are not detected, or output names are wrong.
- Multi-modal input appears to use the wrong channel order.

Checks:

```bash
python sub-skills/inference-evaluation/scripts/check_inference_inputs.py INPUT_FOLDER MODEL_FOLDER
```

Fixes:

- Use `{case_id}_0000{file_ending}`, `{case_id}_0001{file_ending}`, and so on.
- Match `dataset.json` `file_ending` exactly, including compound endings such as `.nii.gz`.
- Keep the same channel order as `dataset.json` `channel_names` and the training data.
- Move unrelated files out of the input folder, or pass `--allow-extra-files` only when intentional.
- For explicit Python file-list prediction, suffixes are not required, but the inner file list order must still match channel order.

## Missing Folds or Checkpoints

Symptoms:

- `fold_X/checkpoint_final.pth` is missing.
- Auto-detected folds are empty or fewer than expected.
- `-f all` fails because `fold_all` does not contain the checkpoint.

Fixes:

- Match `-f` to the folds that were actually trained.
- Use `-chk` if the desired checkpoint is not `checkpoint_final.pth`.
- For cross-validation ensembling, train or validate all requested folds.
- For final deployment models trained on all data, use `-f all` only if `fold_all` exists.

## Wrong Prediction Route or Model Folder

Symptoms:

- `nnUNetv2_predict` cannot resolve a model under `nnUNet_results`.
- `nnUNetv2_predict_from_modelfolder` cannot load `dataset.json` or `plans.json`.
- The selected configuration does not match the model folder.

Fixes:

- Use `nnUNetv2_predict` only when dataset, trainer, plans, and configuration identify a standard results folder.
- Use `nnUNetv2_predict_from_modelfolder -m MODEL_FOLDER` for copied or exported models.
- Confirm the model folder contains `dataset.json`, `plans.json`, and requested `fold_*` checkpoint files.
- Confirm `-d`, `-tr`, `-p`, and `-c` match the training output folder name.

## Ensembling Fails or Produces No Cases

Symptoms:

- `nnUNetv2_ensemble` reports missing `.npz` files.
- Input folders do not contain the same case set.
- Only segmentation files exist, not probabilities.

Fixes:

- Rerun each member prediction with `--save_probabilities`.
- Use the same input case set for every ensemble member.
- Do not delete `.pkl` metadata next to probability files; it is needed to export segmentations.
- Use `--save_npz` on `nnUNetv2_ensemble` only if another downstream ensemble needs probabilities.

## Postprocessing Metadata Is Missing

Symptoms:

- `nnUNetv2_apply_postprocessing` cannot find `plans.json` or `dataset.json`.
- Ensemble outputs lack required metadata.
- Applying postprocessing uses the wrong file ending or label handling.

Fixes:

- Pass `-plans_json PLANS_JSON` and `-dataset_json DATASET_JSON` explicitly.
- Prefer the metadata from one of the ensemble members used to generate the selected postprocessing.
- Use the `postprocessing.pkl` selected for the same dataset/plans/labels as the predictions.
- If no postprocessing file exists, run `nnUNetv2_find_best_configuration` or `nnUNetv2_determine_postprocessing` on validation predictions and reference labels.

## Evaluation Missing Predictions

Symptoms:

- `nnUNetv2_evaluate_folder` or `nnUNetv2_evaluate_simple` fails because not all reference cases are predicted.
- A split prediction job is still running but evaluation starts early.

Fixes:

- Treat missing predictions as an error for final evaluation.
- Use `--chill` only for intentional partial checks, debugging, or split-job smoke tests.
- Verify output filenames are `{case_id}{file_ending}` without channel suffixes.
- For ignore labels, prefer `nnUNetv2_evaluate_folder` with `plans.json` and `dataset.json`; use `nnUNetv2_evaluate_simple -il IGNORE_LABEL` only when plans are unavailable.

## Split Prediction Jobs Are Incomplete

Symptoms:

- Only a fraction of outputs exists.
- Multiple jobs overwrite or duplicate each other.
- `part_id` assertion fails.

Fixes:

- Submit exactly one job for each `part_id` from `0` through `num_parts - 1`.
- Keep `-num_parts` identical across all jobs.
- Ensure every job uses the same input and output folders.
- Assign GPUs outside nnU-Net, for example with `CUDA_VISIBLE_DEVICES` or scheduler resources.
- Use `--continue_prediction` when restarting partial split jobs.

## Device, VRAM, or Worker Problems

Symptoms:

- CUDA out-of-memory errors.
- Worker crashes during preprocessing or export.
- Non-interactive logs are flooded by progress bars.

Fixes:

- Add `--not_on_device` for large cases that exceed VRAM.
- Reduce `-npp` and `-nps` if RAM or worker stability is a problem.
- Set both `-npp 0 -nps 0` with `nnUNetv2_predict` to use sequential mode.
- Use `--disable_tta` only when speed or memory is more important than maximum accuracy.
- Use `--disable_progress_bar` for scheduler logs.
- Use `-device cpu` or `-device mps` only when CUDA is unavailable or inappropriate; expect slower inference.

## Best Configuration Selection Fails

Symptoms:

- Missing `.npz` validation predictions.
- A trained output folder for a requested configuration is absent.
- Cross-validation folders are incomplete.

Fixes:

- Train with `--npz`, or rerun validation with `--val --npz` from the training sub-skill.
- Limit `-c`, `-p`, `-tr`, and `-f` to configurations/folds that exist.
- Use `--disable_ensembling` to compare only individual configurations.
- Use `--no_overwrite` to preserve existing accumulated results when rerunning selection.

## Custom Trainer Unavailable

Symptoms:

- Inference cannot find the trainer class named in the checkpoint.
- Import errors occur after installing a shared model.

Fixes:

- If the trainer is built in, ensure the installed nnU-Net version includes it.
- If the trainer is external, set `nnUNet_extTrainer` to the parent directory that makes the class and its imports resolvable.
- If distributing to others, include custom trainer setup instructions or provide a compatible fork.
- Do not rename a checkpoint to `nnUNetTrainer` unless the network architecture and predictions were manually verified as equivalent.

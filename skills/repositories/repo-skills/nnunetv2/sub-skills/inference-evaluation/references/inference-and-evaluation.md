# Inference and Evaluation Workflows

## Preflight Checklist

Before prediction:

1. The model folder has `dataset.json`, `plans.json`, and the requested `fold_*` checkpoint files.
2. Input images use the same file ending recorded in `dataset.json`, such as `.nii.gz`.
3. Each case has one file per input channel named `{case_id}_0000{file_ending}`, `{case_id}_0001{file_ending}`, and so on.
4. The channel order matches `dataset.json` `channel_names`; the suffix order is semantic, not arbitrary.
5. For cascades, previous-stage predictions exist for the same case ids.
6. If ensembling is planned, prediction commands include `--save_probabilities`.

Use the bundled helper for naming checks:

```bash
python sub-skills/inference-evaluation/scripts/check_inference_inputs.py INPUT_FOLDER MODEL_FOLDER
```

Pass `--allow-extra-files` only when the input folder intentionally contains non-image sidecar files.

## Predict From the Results Layout

Use this when the trained model can be resolved from `nnUNet_results`:

```bash
nnUNetv2_predict \
  -i INPUT_FOLDER \
  -o OUTPUT_FOLDER \
  -d DATASET001_Example \
  -tr nnUNetTrainer \
  -p nnUNetPlans \
  -c 3d_fullres \
  -f 0 1 2 3 4 \
  -chk checkpoint_final.pth
```

This route computes the model folder from dataset, trainer, plans, and configuration. It is the normal route after local training.

Useful variants:

```bash
# Use only a final all-fold model
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET001_Example -c 3d_fullres -f all

# Continue an interrupted run without overwriting completed outputs
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET001_Example -c 3d_fullres --continue_prediction

# Reduce VRAM pressure for large cases
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET001_Example -c 3d_fullres --not_on_device

# CPU or Apple Silicon fallback; expect slower inference
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET001_Example -c 3d_fullres -device cpu
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET001_Example -c 3d_fullres -device mps
```

Select a specific CUDA GPU with the environment, not with `-device`:

```bash
CUDA_VISIBLE_DEVICES=1 nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET001_Example -c 3d_fullres
```

## Predict From an Explicit Model Folder

Use this for copied, installed, exported, or manually selected models:

```bash
nnUNetv2_predict_from_modelfolder \
  -i INPUT_FOLDER \
  -o OUTPUT_FOLDER \
  -m MODEL_FOLDER \
  -f 0 1 2 3 4 \
  -chk checkpoint_final.pth
```

The model folder must contain:

```text
MODEL_FOLDER/
├── dataset.json
├── plans.json
├── fold_0/checkpoint_final.pth
├── fold_1/checkpoint_final.pth
...
```

If only `fold_all` exists, run with `-f all`.

## Cascaded Inference

For `3d_cascade_fullres`, previous-stage predictions from the low-resolution stage are required:

```bash
nnUNetv2_predict \
  -i INPUT_FOLDER \
  -o OUTPUT_LOWRES \
  -d DATASET001_Example \
  -c 3d_lowres \
  -f 0 1 2 3 4

nnUNetv2_predict \
  -i INPUT_FOLDER \
  -o OUTPUT_CASCADE \
  -d DATASET001_Example \
  -c 3d_cascade_fullres \
  -f 0 1 2 3 4 \
  -prev_stage_predictions OUTPUT_LOWRES
```

`nnUNetv2_find_best_configuration` writes cascade-aware commands in `inference_instructions.txt`; prefer those commands after model selection.

## Split a Large Batch Across Jobs

`nnUNetv2_predict` can shard an input folder by case list. For four jobs, submit one command per `part_id`:

```bash
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET001_Example -c 3d_fullres -num_parts 4 -part_id 0
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET001_Example -c 3d_fullres -num_parts 4 -part_id 1
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET001_Example -c 3d_fullres -num_parts 4 -part_id 2
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_FOLDER -d DATASET001_Example -c 3d_fullres -num_parts 4 -part_id 3
```

Rules:

- `part_id` starts at `0` and must be less than `num_parts`.
- Each job writes its own subset into the same output folder.
- Assign GPUs externally, for example with `CUDA_VISIBLE_DEVICES` or a scheduler.
- This split mode is available on `nnUNetv2_predict`; `nnUNetv2_predict_from_modelfolder` does not expose `-num_parts` or `-part_id`.

## Save Probabilities and Ensemble

Run each member with `--save_probabilities`:

```bash
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_2D -d DATASET001_Example -c 2d --save_probabilities
nnUNetv2_predict -i INPUT_FOLDER -o OUTPUT_3D -d DATASET001_Example -c 3d_fullres --save_probabilities
```

Then ensemble:

```bash
nnUNetv2_ensemble -i OUTPUT_2D OUTPUT_3D -o OUTPUT_ENSEMBLE -np 8
```

The ensemble command requires every input folder to have the same `.npz` case files. If one member was predicted without `--save_probabilities`, rerun that member before ensembling.

## Apply Postprocessing

If a `postprocessing.pkl` was selected by `nnUNetv2_find_best_configuration` or `nnUNetv2_determine_postprocessing`, apply it to final predictions:

```bash
nnUNetv2_apply_postprocessing \
  -i OUTPUT_FOLDER \
  -o OUTPUT_FOLDER_PP \
  -pp_pkl_file POSTPROCESSING_PKL \
  -plans_json PLANS_JSON \
  -dataset_json DATASET_JSON \
  -np 8
```

For predictions produced directly by `nnUNetv2_predict`, `plans.json` and `dataset.json` are written to the output folder. For ensemble or copied folders, pass them explicitly when the files are absent.

## Evaluate Predictions

Plans-aware evaluation reads label/region and ignore-label behavior from `plans.json` and `dataset.json`:

```bash
nnUNetv2_evaluate_folder GT_FOLDER PRED_FOLDER -djfile DATASET_JSON -pfile PLANS_JSON -o PRED_FOLDER/summary.json -np 8
```

Simple evaluation accepts explicit foreground labels and optional ignore label:

```bash
nnUNetv2_evaluate_simple GT_FOLDER PRED_FOLDER -l 1 2 3 -il 255 -o PRED_FOLDER/summary.json -np 8
```

Use `--chill` when partial predictions are intentional and the evaluator should not fail because some reference cases lack predictions. Without `--chill`, missing predictions indicate an incomplete run.

Evaluation output includes `metric_per_case`, per-label/region means, and `foreground_mean` metrics such as Dice and IoU.

## Find the Best Configuration

Prerequisite: each compared fold must have validation probability files. If they are missing, rerun validation with `--val --npz` from the training sub-skill.

```bash
nnUNetv2_find_best_configuration DATASET001_Example -c 2d 3d_fullres 3d_lowres -f 0 1 2 3 4 -np 8
```

What happens:

1. Cross-validation predictions are accumulated across requested folds.
2. Individual configurations are evaluated.
3. Pairwise ensembles are evaluated unless `--disable_ensembling` is set.
4. Connected-component postprocessing is tested for the best result.
5. Inference instructions are written for the selected single model or ensemble.

Use the generated `inference_instructions.txt` as the canonical command source for deployment, especially for cascades and ensembles.

## Python API Mapping

For programmatic prediction, create an `nnUNetPredictor`, initialize it from a trained model folder, then call `predict_from_files`:

```python
import torch
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor

predictor = nnUNetPredictor(
    tile_step_size=0.5,
    use_gaussian=True,
    use_mirroring=True,
    perform_everything_on_device=True,
    device=torch.device("cuda"),
    verbose=False,
    verbose_preprocessing=False,
    allow_tqdm=True,
)
predictor.initialize_from_trained_model_folder(
    "MODEL_FOLDER",
    use_folds=(0, 1, 2, 3, 4),
    checkpoint_name="checkpoint_final.pth",
)
predictor.predict_from_files(
    "INPUT_FOLDER",
    "OUTPUT_FOLDER",
    save_probabilities=False,
    overwrite=True,
    num_processes_preprocessing=8,
    num_processes_segmentation_export=8,
    folder_with_segs_from_prev_stage=None,
    num_parts=1,
    part_id=0,
)
```

When passing explicit file lists instead of a folder, provide a list of cases where each case is a list of channel files, ordered like `dataset.json` `channel_names`. Output paths should be truncated paths without the file ending; nnU-Net appends the model's `file_ending`.

# Planning and Preprocessing CLI Reference

nnU-Net v2 exposes a combined CLI workflow plus separate CLIs and separate Python API helpers. Prefer the combined CLI for normal users; use split commands when outputs are partially fresh or when debugging a specific stage.

## Combined workflow

For a new dataset:

```bash
nnUNetv2_plan_and_preprocess -d DATASET_ID --verify_dataset_integrity
```

What it does, in order:

1. Extracts `dataset_fingerprint.json` into the dataset folder under `nnUNet_preprocessed`.
2. Runs experiment planning and writes a plans file such as `nnUNetPlans.json`.
3. Runs preprocessing for requested configurations, by default `2d`, `3d_fullres`, and `3d_lowres` when available.

Important options:

- `-d 1 2 3`: process one or more numeric dataset IDs.
- `--verify_dataset_integrity`: check raw dataset structure and labels; recommended once for each new or changed dataset.
- `--clean`: overwrite an existing fingerprint; required after changing the dataset or fingerprint extractor.
- `--no_pp`: stop after fingerprint extraction and planning.
- `-fpe DatasetFingerprintExtractor`: choose the fingerprint extractor class.
- `-npfp 8`: worker count for fingerprint extraction.
- `-pl ExperimentPlanner`: choose the experiment planner class.
- `-gpu_memory_target 24`: set planner VRAM target in GB; use only when intentionally deviating from defaults.
- `-preprocessor_name DefaultPreprocessor`: choose the preprocessor class recorded in plans.
- `-overwrite_target_spacing X Y Z`: override target spacing for `3d_fullres` and `3d_cascade_fullres`.
- `-overwrite_plans_name NAME`: write a distinct plans identifier; strongly recommended with custom planner memory target, custom preprocessor, or target spacing.
- `-c 2d 3d_fullres`: preprocess only selected configurations.
- `-np 8 4`: preprocessing worker counts. One value applies to all configurations; multiple values must match `-c` length.
- `--no_pbar`: disable progress bars in logs, terminals, and batch jobs.
- `--verbose`: print additional diagnostic output.

## Split commands

Use split commands when fingerprints and plans are fresh but preprocessing is stale, when planning needs inspection before preprocessing, or when a specific stage failed.

```bash
nnUNetv2_extract_fingerprint -d DATASET_ID --verify_dataset_integrity
nnUNetv2_plan_experiment -d DATASET_ID
nnUNetv2_preprocess -d DATASET_ID -c 2d 3d_fullres
```

Stage-specific notes:

- `nnUNetv2_extract_fingerprint` accepts `-fpe`, `-np`, `--verify_dataset_integrity`, `--clean`, `--no_pbar`, and `--verbose`.
- `nnUNetv2_plan_experiment` accepts `-pl`, `-gpu_memory_target`, `-preprocessor_name`, `-overwrite_target_spacing`, and `-overwrite_plans_name`.
- `nnUNetv2_preprocess` accepts `-plans_name`, `-c`, `-np`, `--no_pbar`, and `--verbose`.
- `3d_cascade_fullres` usually does not need separate preprocessing because it reuses the `3d_fullres` data.
- Configurations absent from the plans file are skipped by preprocessing, not treated as fatal.

## Python API boundary

The Python API exposes separate stage helpers, not a combined `plan_and_preprocess` function. Use the CLI for the all-in-one workflow.

```python
from nnunetv2.experiment_planning.plan_and_preprocess_api import (
    extract_fingerprints,
    plan_experiments,
    preprocess,
)

extract_fingerprints([DATASET_ID], num_processes=8, check_dataset_integrity=True, clean=True)
plans_identifier = plan_experiments([DATASET_ID])
preprocess([DATASET_ID], plans_identifier=plans_identifier, configurations=("2d", "3d_fullres"), num_processes=(8, 4))
```

Installed signatures to rely on:

- `extract_fingerprints(dataset_ids, fingerprint_extractor_class_name='DatasetFingerprintExtractor', num_processes=8, check_dataset_integrity=False, clean=True, verbose=True, show_progress_bar=True)`
- `preprocess(dataset_ids, plans_identifier='nnUNetPlans', configurations=('2d','3d_fullres','3d_lowres'), num_processes=(8,4,8), verbose=False, show_progress_bar=True)`

## Safe command builder

The bundled helper prints shell commands and never runs preprocessing:

```bash
python sub-skills/planning-preprocessing/scripts/build_plan_preprocess_command.py --dataset-id 42 --verify-dataset-integrity
python sub-skills/planning-preprocessing/scripts/build_plan_preprocess_command.py --mode split --dataset-id 42 --skip-fingerprint --configurations 3d_fullres --num-processes 2
python sub-skills/planning-preprocessing/scripts/build_plan_preprocess_command.py --mode preprocess --dataset-id 42 --configurations 2d 3d_fullres --plans-name nnUNetPlans
```

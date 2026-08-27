# Cross-Cutting Troubleshooting

## Import or Command Is Missing

Symptoms:

- `ModuleNotFoundError: No module named 'nnunetv2'`
- `nnUNetv2_train: command not found`
- A command imports but fails before showing help.

Checks:

```bash
python scripts/check_nnunet_setup.py --require-commands
python -m pip show nnunetv2
```

Fixes:

- Install the `nnunetv2` distribution in the Python environment used by the agent or shell.
- Ensure the environment's executable directory is on `PATH` for CLI commands.
- Use `COMMAND -h` after installation to verify parser availability before running large workflows.

## Path Environment Variables Are Unset

Symptoms:

- Runtime error that `nnUNet_raw`, `nnUNet_preprocessed`, or `nnUNet_results` is not defined.
- Dataset, preprocessing, training, or inference commands cannot locate inputs or outputs.

Checks:

```bash
python scripts/check_nnunet_setup.py --require-env nnUNet_raw nnUNet_preprocessed nnUNet_results
```

Fixes:

- Set `nnUNet_raw` to the parent folder containing `DatasetXXX_Name` raw datasets.
- Set `nnUNet_preprocessed` to the preprocessing output/cache location.
- Set `nnUNet_results` to the model training and inference-results location.
- Use absolute paths in shell exports or service definitions to avoid working-directory dependence.

## Workflow Order Is Wrong

Symptoms:

- Training cannot find preprocessed data or plans.
- Inference cannot find trained model folders or folds.
- Best-configuration selection complains about missing validation probabilities.

Fixes:

- For missing plans/preprocessed data, route to `sub-skills/planning-preprocessing/SKILL.md`.
- For missing folds/checkpoints or `--npz` validation outputs, route to `sub-skills/training-configuration/SKILL.md`.
- For prediction/model-folder/postprocessing/evaluation issues, route to `sub-skills/inference-evaluation/SKILL.md`.

## GPU, Device, or Backend Problems

Symptoms:

- CUDA is unavailable despite using `-device cuda`.
- Training or inference is unexpectedly slow on CPU/MPS.
- Out-of-memory errors during preprocessing, training, or inference.

Checks:

```bash
python scripts/check_nnunet_setup.py --check-torch
nnUNetv2_train -h
nnUNetv2_predict -h
```

Fixes:

- Use `-device cpu`, `-device cuda`, or `-device mps` only when supported by the installed PyTorch build and hardware.
- Reduce process counts for preprocessing or inference export when RAM is exhausted.
- For training OOM, choose a smaller configuration/plans target, reduce GPU memory target during planning where appropriate, or train fewer concurrent folds.
- Prefer one fold per visible GPU for throughput unless DDP is intentionally required.

## Data or Metadata Validation Fails

Symptoms:

- Dataset integrity verification fails.
- File channel suffixes do not match `dataset.json` channels.
- Region labels, ignore labels, or file endings are inconsistent.

Checks:

```bash
python sub-skills/data-preparation/scripts/validate_dataset_json.py /path/to/nnUNet_raw/Dataset123_MyDataset --check-files
```

Fixes:

- Ensure dataset folder names follow `DatasetXXX_Name`.
- Ensure `imagesTr`, `labelsTr`, and `dataset.json` exist for training.
- Match every case's channel files to `_0000`, `_0001`, ... and the declared file ending.
- Add `regions_class_order` when labels define regions instead of only integer labels.

## Custom Trainer or Class Lookup Fails

Symptoms:

- Trainer, planner, preprocessor, or reader/writer class is not found by name.
- A model trained with a custom trainer cannot be loaded elsewhere.
- An external trainer import error hides the target class.

Checks:

```bash
python sub-skills/customization-extension/scripts/list_available_nnunet_classes.py --kind trainer
python sub-skills/customization-extension/scripts/list_available_nnunet_classes.py --kind trainer --external-trainer-dir /path/to/custom_trainers_root
```

Fixes:

- Route to `sub-skills/customization-extension/SKILL.md`.
- Make the external package importable, or set `nnUNet_extTrainer` to a directory containing importable trainer modules.
- When sharing custom-trainer models, ensure the target machine can import the same trainer class or use a documented portability strategy.

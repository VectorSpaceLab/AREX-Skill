---
name: training-custom-models
description: "Retrain ProteinMPNN, validate training data layout, resume or
  debug training, and use custom training checkpoints for ProteinMPNN
  inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training Custom Models

Use this sub-skill when a user wants to retrain ProteinMPNN, inspect the training dataset format, run a tiny debug training smoke, resume from a checkpoint, or point inference at custom model weights. ProteinMPNN training is normally GPU/HPC work; keep full training runs explicit and treat them as expensive.

## Quick Routing

- For training setup, dataset checks, SLURM adaptation, checkpoint naming, and training logs, use the references in this sub-skill.
- For actually designing or scoring sequences with a custom checkpoint after the model folder and model name are known, route to `../inference-design/` and pass `--path_to_model_weights` plus `--model_name`.
- For fixed positions, tied positions, PSSM, amino-acid bias, or other inference JSONL constraints, route to `../constraint-inputs/`.
- Do not copy or bundle model checkpoints; users keep checkpoints in their ProteinMPNN checkout or training output directory.

## Core Workflow

1. Confirm dependencies: Python, PyTorch, NumPy; training data parsing areas also need `python-dateutil`, SciPy, and `pdbx`/mmCIF tooling when preparing data from CIF files.
2. Validate the training data root before launching training:
   ```bash
   python scripts/check_training_layout.py --data-root path/to/pdb_2021aug02
   ```
3. For a tiny smoke check, use the sample dataset, `--debug True`, one epoch, a small token budget, and a scratch output folder.
4. For real training, adapt the SLURM recipe in `references/training-workflow.md`; expect long GPU runtime and large training data.
5. Use the resulting checkpoint folder with inference:
   ```bash
   python protein_mpnn_run.py --path_to_model_weights path/to/run/model_weights --model_name epoch_last --pdb_path path/to/input.pdb --out_folder path/to/out
   ```

## References

- `references/training-workflow.md`: training flags, debug smoke, SLURM adaptation, resume behavior, output schema.
- `references/data-layout.md`: expected dataset files and `.pt` records, loader behavior, validation script use.
- `references/custom-checkpoints.md`: checkpoint names and inference flags for custom weights.
- `references/troubleshooting.md`: common training, data, dependency, and custom-checkpoint failures.

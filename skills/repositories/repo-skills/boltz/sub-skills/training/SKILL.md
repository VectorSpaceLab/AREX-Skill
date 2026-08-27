---
name: training
description: "Guide Boltz training and retraining through config edits, debug
  launches, resource settings, checkpoints, and training troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Boltz Training

Use this sub-skill when the user wants to train, retrain, resume, debug, or modify Boltz training configs for structure or confidence models.

## Route First

- Raw-data preprocessing, RCSB/OpenFold processing, MSA generation, clustering, CCD, Redis, or `mmseqs` setup belongs in the data-preparation sub-skill.
- Prediction outputs, confidence interpretation, benchmark aggregation, or post-training evaluation belongs in prediction or evaluation.
- Boltz docs state that updated Boltz-2 training information is coming soon; do not invent unreleased Boltz-2 training recipes.

## Start Here

1. Confirm the user already has processed training data, processed MSAs, and a ligand symmetry file; full public preprocessed data is about 250 GB before any training outputs.
2. Choose a config shape from `references/training-configs.md`: structure, confidence-only, or full structure-plus-confidence.
3. Validate placeholders, paths, split files, checkpoint intent, and resource settings with `scripts/boltz_training_config_check.py`.
4. Run a debug launch before any full run; debug mode disables multi-device DDP, sets data workers to zero, and disables wandb in the training script.
5. Treat full training as expensive and hardware-dependent; never promise that it is cheap, quick, or feasible without suitable GPUs and storage.

## Common Workflows

- Training launch sequence, debug overrides, DDP notes, wandb behavior, and checkpoint decisions: `references/training-workflows.md`.
- Config fields, template differences, data module requirements, split semantics, and resource knobs: `references/training-configs.md`.
- Failure diagnosis for placeholders, missing data, Hydra imports, GPU memory, wandb, DDP, and Boltz-2 docs gaps: `references/troubleshooting.md`.

## Native Check

Run the bundled static checker from this sub-skill directory before a launch:

```bash
python scripts/boltz_training_config_check.py path/to/train.yaml --repo-root . --profile debug
```

Use `--check-imports` only inside a Boltz training environment where the package and training dependencies are installed.
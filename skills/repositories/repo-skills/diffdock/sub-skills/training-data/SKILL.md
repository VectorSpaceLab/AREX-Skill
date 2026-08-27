---
name: training-data
description: "Plan DiffDock score/confidence training and prepare datasets,
  splits, ESM embeddings, caches, and checkpoints safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DiffDock Training Data

Use this sub-skill when a user wants to plan DiffDock score-model training, confidence-model training, dataset layout checks, split/caching decisions, ESM embedding preparation, or checkpoint compatibility before running expensive jobs.

## Start Here

- For score and confidence training command patterns, checkpoint outputs, restart/pretrain flows, and safe scaling decisions, read [references/training-workflows.md](references/training-workflows.md).
- For PDBBind, BindingMOAD, DockGen, PoseBusters, van der Mers/sidechain layouts, split files, CSV schemas, cache behavior, and ESM embedding preparation, read [references/data-preparation.md](references/data-preparation.md).
- For parser flag categories, model/checkpoint compatibility, all-atom/coarse-grained choices, confidence heads, and config portability, read [references/model-and-checkpoint-reference.md](references/model-and-checkpoint-reference.md).
- For dependency, backend, data path, cache, ESM, W&B, OOM, and checkpoint failures, read [references/troubleshooting.md](references/troubleshooting.md).

## Safe Helpers

- Build a command without starting training: [scripts/build_training_command.py](scripts/build_training_command.py).
- Check dataset and split layout without importing DiffDock, Torch, RDKit, or ProDy: [scripts/validate_dataset_layout.py](scripts/validate_dataset_layout.py).
- Check an ESM embedding directory or aggregate `.pt` index safely by default: [scripts/validate_esm_embedding_index.py](scripts/validate_esm_embedding_index.py).

## Scope And Routing

This sub-skill covers training planning and data preparation only: score-model and confidence-model training flags, dataset families, split files, ESM embedding preparation/conversion, cache naming, model-parameter outputs, and checkpoint compatibility.

Route these tasks elsewhere:

- Use trained checkpoints for docking prediction, inference YAML tuning, CSV/batch inference, and confidence-guided sampling: `../docking-inference/SKILL.md`.
- Aggregate benchmark metrics, run post-training evaluation, or compare PoseBusters/DockGen/PDBBind results: `../evaluation-benchmarks/SKILL.md`.
- Launch or debug the Gradio UI: `../web-ui/SKILL.md`.

## Quick Commands

```bash
python sub-skills/training-data/scripts/build_training_command.py --mode score --dataset pdbbind --data-dir data/PDBBind_processed --split-train data/splits/timesplit_no_lig_overlap_train --split-val data/splits/timesplit_no_lig_overlap_val --run-name pdbbind_trial --limit-complexes 16 --n-epochs 1 --batch-size 2

python sub-skills/training-data/scripts/validate_dataset_layout.py --dataset-type pdbbind --dataset-root data/PDBBind_processed --split-path data/splits/timesplit_no_lig_overlap_train --max-complexes 5

python sub-skills/training-data/scripts/validate_esm_embedding_index.py data/esm2_embeddings.pt --expect-ids data/splits/timesplit_no_lig_overlap_train
```

## Key Safety Rules

- Treat training, confidence-dataset generation, ESM extraction, graph preprocessing, and evaluation as expensive GPU/storage jobs; do not start them without explicit user approval.
- Use the bundled helpers first: they print commands or JSON checks and never run DiffDock training.
- Keep dataset paths, cache paths, and run directories relative to the active DiffDock checkout or user-provided project workspace.
- Do not assume full imports are available: full training paths require the optional-heavy Torch, PyG, e3nn, W&B, RDKit, ProDy, ESM/OpenFold stack and preferably CUDA.
- Preserve `model_parameters.yml` with checkpoints; downstream confidence training and inference compatibility depend on it.

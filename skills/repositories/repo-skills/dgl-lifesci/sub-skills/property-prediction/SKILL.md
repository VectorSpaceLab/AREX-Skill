---
name: property-prediction
description: "Build DGL-LifeSci molecular property prediction workflows for
  custom CSVs, MoleculeNet/Alchemy/PubChem datasets, multitask tasks, metrics,
  model configs, and safe training or inference planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Property Prediction

Use this sub-skill when the task is to plan, configure, debug, or prototype molecular graph property prediction with DGL-LifeSci.

## Read First

- `references/workflows.md`: choose a property workflow, map data columns to tasks, plan CLI/API execution, and avoid unsafe long-running downloads or training.
- `references/model-configs.md`: choose predictors, featurizers, metrics, dataset/model combinations, and JSON hyperparameter keys.
- `references/troubleshooting.md`: fix label/mask, metric, split, cache/download, CPU/GPU, config-key, and CLI/API issues.
- `scripts/build_property_config.py`: create or validate small JSON config files for common property predictors without training or downloading data.

## Route Here When

- The user has a custom CSV of SMILES plus one or more molecular properties and needs a classification, regression, multitask, or inference plan.
- The user wants MoleculeNet classification/regression, Alchemy quantum property prediction, PubChem aromaticity prediction, OGB graph property prediction, or pretrain-GNN finetuning guidance.
- The user needs a model config for `GCN`, `GAT`, `Weave`, `MPNN`, `AttentiveFP`, `NF`, or supervised-pretrained `GIN` property workflows.
- The user asks how to choose metrics, splits, masks, `n_tasks`, featurizers, or safe short validation before expensive training.

## Delegate Elsewhere

- Use `../molecule-data-prep/` for raw SMILES cleaning, graph construction, custom featurizer design, dataset schema validation, split implementation details, or RDKit/DGL graph debugging.
- Use `../model-zoo-pretraining/` for architecture internals, pretrained model catalog details, `load_pretrained`, GIN pretraining setup, and predictor implementation choices beyond property workflow configuration.
- Avoid this sub-skill for reaction prediction, binding affinity, generative models, molecule embeddings, or link prediction unless they only provide context for what not to use.

## Standard Handoff

1. Identify task type: binary/multilabel classification, regression, quantum regression, aromatic atom count regression, or multitask ADME-style regression.
2. Confirm data shape: SMILES column, task columns, missing-label policy, classification label values, and whether masks are needed.
3. Pick workflow and model family using `references/workflows.md` and `references/model-configs.md`.
4. Create or validate a config with `scripts/build_property_config.py` for quick planning, then separately plan training/inference commands or API code.
5. Run small smoke checks first: import `dgllife`, featurize 1-3 SMILES, instantiate the predictor with `n_tasks`, and compute one forward pass before downloads or full epochs.

## Safe Execution Defaults

- Treat full training, hyperparameter search, dataset downloads, and pretrained checkpoint downloads as long-running or networked work; ask before running them.
- Prefer CPU smoke checks and `num_workers=0` or `1` when debugging featurization, masks, metrics, and config files.
- Keep generated configs and result directories outside package source trees.
- Record dataset cache locations explicitly in user project paths instead of relying on accidental working-directory caches.

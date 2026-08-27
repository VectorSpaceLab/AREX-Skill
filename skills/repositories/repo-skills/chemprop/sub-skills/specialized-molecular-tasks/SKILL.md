---
name: specialized-molecular-tasks
description: "Use this Chemprop sub-skill for reaction SMILES,
  reaction-plus-molecule multicomponent data, atom/bond targets, constrained
  MolAtomBond prediction, spectral tasks, and specialized descriptor/feature
  schemas."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Chemprop Specialized Molecular Tasks

Use this sub-skill when a Chemprop request needs specialized molecular schemas or flags rather than ordinary molecule-level training/prediction.

## Route Here For

- Reaction property models using atom-mapped reaction SMILES, `--reaction-columns`, and `--rxn-mode` / `--reaction-mode`.
- Multicomponent workflows combining reactions and molecule SMILES such as reaction-plus-solvent models.
- MolAtomBond training where molecule, atom, and/or bond targets use `--mol-target-columns`, `--atom-target-columns`, or `--bond-target-columns`.
- Constrained atom/bond prediction with `--constraints-path` and `--constraints-to-targets`.
- Spectral task setup with `--task-type spectral`, `sid`/`earthmovers` style metrics, and positivity/normalization caveats.
- Specialized feature inputs whose component indices, atom ordering, bond ordering, or scaling flags interact with the schema.

## Route Elsewhere

- Use `../training-cli/` for ordinary `chemprop train` options, split policies, checkpoints, losses, metrics, and generic regression/classification workflows.
- Use `../prediction-fingerprints/` for general `chemprop predict` and `chemprop fingerprint` mechanics after the specialized columns are known.
- Use `../data-featurization/` for CSV/NPZ validation, molecule featurizer choices, descriptors, and general feature-file shape checks.
- Use `../python-api-modeling/` for low-level Python API composition of models, dataloaders, Lightning modules, and custom predictors.

## Quick Starts

### Reaction Training

```bash
chemprop train \
  -i reactions.csv \
  --reaction-columns rxn_smiles \
  --rxn-mode REAC_DIFF_BALANCE \
  --target-columns yield \
  --keep-h \
  --epochs 50 \
  --save-dir chemprop_rxn_model
```

Use the same reaction columns and reaction mode at prediction/fingerprint time as were used for training.

### Reaction Plus Solvent

```bash
chemprop train \
  -i reaction_solvent.csv \
  --reaction-columns rxn_smiles \
  --smiles-columns solvent_smiles \
  --split-key-molecule 1 \
  --message-hidden-dim 300 200 \
  --depth 3 5 \
  --target-columns rate \
  --save-dir chemprop_rxn_solvent_model
```

For mixed reaction+molecule inputs, component order is the order implied by reaction columns plus SMILES columns. Match that order when giving per-component feature paths, message dimensions, and prediction inputs.

### Atom/Bond Targets

```bash
chemprop train \
  -i atom_bond_targets.csv \
  --smiles-columns smiles \
  --mol-target-columns mol_y \
  --atom-target-columns atom_charge atom_shift \
  --bond-target-columns bond_order \
  --reorder-atoms \
  --epochs 50 \
  --save-dir chemprop_mab_model
```

Atom and bond target cells must be parseable Python/JSON-like lists. Atom target list order follows RDKit atom order unless atom maps are present and `--reorder-atoms` is used; bond target list order follows the input molecule bond order.

## References

- `references/reaction-multicomponent.md` covers reaction SMILES, `--rxn-mode`, reaction-plus-solvent inputs, and per-component model dimensions.
- `references/mol-atom-bond.md` covers MolAtomBond target schemas, constraints, bounded targets, extra atom/bond descriptors, and prediction ordering.
- `references/spectral-and-special-tasks.md` covers spectral tasks, special task/loss choices, and feature/descriptor interactions.
- `references/troubleshooting.md` covers atom-map ordering, constraint mapping, reaction modes, multicomponent dimensions, and constrained output issues.
- `scripts/chemprop_specialized_command_builder.py` builds command arrays and shell snippets for reaction, multicomponent, MolAtomBond, constrained, and spectral workflows.

## Practical Guardrails

- Prefer `--rxn-mode` in generated commands; `--reaction-mode` is accepted as an alias, but `--rxn-mode` matches the parser destination.
- Do not combine `--mpn-shared` with different `--message-hidden-dim` or `--depth` values; mixed reaction+molecule data also rejects shared MPNNs.
- Do not use `--use-cuikmolmaker-featurization` when `--reorder-atoms` is required for mapped atom target order.
- Treat reaction extra atom/bond features cautiously: the reaction graph featurizer warns that extra atom and bond features are unsupported for reaction components.
- For MolAtomBond constraints, `--constraints-to-targets` names must be selected from the atom/bond target column names passed in the same command, in the same order as the constraints CSV columns.

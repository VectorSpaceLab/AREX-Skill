# Reaction and Multicomponent Workflows

Chemprop supports atom-mapped reaction SMILES and multicomponent inputs where one target row can include reactions plus molecules such as solvents, reagents, or additives.

## Reaction Columns

Use `--reaction-columns` for CSV columns containing reaction SMILES in `REACTANT>AGENT>PRODUCT` form. The agent section may be empty, so `reactants>>products` is valid. Reaction SMILES are expected to be atom mapped when using condensed reaction graph featurization; unmapped leaving groups can appear when the chemistry requires them.

```bash
chemprop train \
  -i rxn.csv \
  --reaction-columns rxn_smiles \
  --target-columns target \
  --rxn-mode REAC_DIFF \
  --save-dir rxn_model
```

For prediction and fingerprinting, repeat the same input-column flags and reaction mode that were used during training:

```bash
chemprop predict \
  -i rxn_to_score.csv \
  --reaction-columns rxn_smiles \
  --rxn-mode REAC_DIFF \
  --model-path rxn_model/model_0/best.pt \
  -o rxn_predictions.csv
```

## Reaction Modes

`--rxn-mode` and `--reaction-mode` are aliases. Prefer `--rxn-mode` in new commands. Values are case-insensitive in the CLI but are usually shown uppercase in parsed form.

| Mode | Meaning | Use when |
| --- | --- | --- |
| `REAC_DIFF` | Reactant features plus product-minus-reactant differences | Default for most reaction property models |
| `REAC_PROD` | Reactant features plus product features | You want both sides represented directly |
| `PROD_DIFF` | Product features plus product-minus-reactant differences | Product-centered reaction modeling is desired |
| `REAC_DIFF_BALANCE` | `REAC_DIFF` plus balancing for imbalanced reactions | Atom mappings are incomplete or reactions are imbalanced |
| `REAC_PROD_BALANCE` | `REAC_PROD` plus balancing | Direct reactant/product representation with balancing |
| `PROD_DIFF_BALANCE` | `PROD_DIFF` plus balancing | Product-centered modeling with balancing |

Add `--keep-h` when mapped hydrogens are meaningful and should remain in the graph.

## Reaction Plus Molecule Inputs

Use both `--reaction-columns` and `--smiles-columns` when a target depends on reactions and separate molecules.

```bash
chemprop train \
  -i rxn_solvent.csv \
  --reaction-columns rxn_smiles \
  --smiles-columns solvent_smiles \
  --target-columns rate \
  --split-key-molecule 1 \
  --save-dir rxn_solvent_model
```

The same column ordering must be used for prediction. Component-sensitive flags use zero-based component indices. A reaction column and one molecule column form two components, so the molecule component is commonly index `1` for splitting and the reaction component is commonly index `0` for indexed feature paths.

## Per-Component Features and Dimensions

For multicomponent data, component-indexed feature paths are written as index/path pairs:

```bash
chemprop train \
  -i rxn_solvent.csv \
  --reaction-columns rxn_smiles \
  --smiles-columns solvent_smiles \
  --atom-descriptors-path 1 solvent_atom_descriptors.npz \
  --descriptors-path global_descriptors.npz \
  --message-hidden-dim 300 200 \
  --depth 3 5
```

Rules to preserve:

- A single `--message-hidden-dim` or `--depth` value is broadcast to all components.
- Multiple `--message-hidden-dim` or `--depth` values must match the number of components exactly.
- Single-component data accepts only one `--message-hidden-dim` and one `--depth` value.
- `--mpn-shared` cannot be combined with multiple `--message-hidden-dim` or `--depth` values.
- Mixed reaction+molecule inputs reject shared MPNNs.

## Feature Compatibility Notes

Molecule-level descriptors from `--descriptors-path`, `--descriptors-columns`, and `--molecule-featurizers` are concatenated after message passing. Atom and bond feature/descriptor NPZ files can be component-indexed, but reaction components need caution: the condensed reaction graph featurizer warns that extra atom and bond features are unsupported for reactions. Prefer applying atom/bond extras to molecule components, or validate carefully before relying on reaction-component extras.

## Safe Command Patterns

Reaction regression with uncertainty-style task choices:

```bash
chemprop train -i rxn.csv --reaction-columns rxn_smiles --task-type regression-mve
chemprop train -i rxn.csv --reaction-columns rxn_smiles --task-type regression-evidential --evidential-regularization 0.2
chemprop train -i rxn.csv --reaction-columns rxn_smiles --task-type regression-quantile
```

Reaction+solvent fingerprint extraction:

```bash
chemprop fingerprint \
  -i rxn_solvent.csv \
  --reaction-columns rxn_smiles \
  --smiles-columns solvent_smiles \
  --model-path rxn_solvent_model/model_0/best.pt \
  --ffn-block-index 0 \
  -o fingerprints.csv
```

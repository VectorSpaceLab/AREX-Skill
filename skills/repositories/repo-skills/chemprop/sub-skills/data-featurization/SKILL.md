---
name: data-featurization
description: "Prepare and validate Chemprop CSV/NPZ inputs, SMILES/reaction
  columns, descriptors, atom/bond features, featurizers, datasets, dataloaders,
  and split APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Chemprop Data Featurization

Use this sub-skill when a task is about Chemprop 2.2.3 data objects, CSV/NPZ input schemas, SMILES or reaction columns, descriptors, extra atom/bond arrays, graph or molecule featurizers, split construction, or dataloaders. Keep this sub-skill focused on getting data into Chemprop correctly; route downstream model fitting, checkpoint use, prediction, uncertainty, and atom/bond target semantics to sibling skills.

## Route Here For

- Building `MoleculeDatapoint`, `ReactionDatapoint`, `MoleculeDataset`, `ReactionDataset`, or `MulticomponentDataset` from Python.
- Validating CSV columns for single-molecule, multicomponent, reaction, or `--no-header-row` inputs.
- Preparing `.npz` files for `--descriptors-path`, `--atom-features-path`, `--atom-descriptors-path`, `--bond-features-path`, or `--bond-descriptors-path`.
- Choosing molecule descriptor featurizers such as `morgan_binary`, `morgan_count`, `rdkit_2d`, `v1_rdkit_2d`, `v1_rdkit_2d_normalized`, or `charge`.
- Choosing atom, bond, reaction, or molgraph featurizers and checking feature dimensions.
- Creating train/validation/test split indices with `make_split_indices` and applying them with `split_data_by_indices`.
- Building `torch.utils.data.DataLoader` objects with Chemprop’s `build_dataloader`.
- Explaining optional `cuik-molmaker` acceleration constraints and why it is not always available.

## Route Elsewhere

- Full CLI training command assembly, output directories, trainer flags, model/predictor/loss/metric choices, and checkpoint handling: [training-cli](../training-cli/SKILL.md).
- Python model assembly with message passing, aggregation, FFNs, predictors, and Lightning modules: [python-api-modeling](../python-api-modeling/SKILL.md).
- Prediction, fingerprint, and checkpoint-loading workflows: [prediction-fingerprints](../prediction-fingerprints/SKILL.md).
- Atom/bond target semantics, constraints, target-column mappings, and specialized molecular task caveats: [specialized-molecular-tasks](../specialized-molecular-tasks/SKILL.md).
- Uncertainty calibration/evaluation after data has been validated: [uncertainty-advanced](../uncertainty-advanced/SKILL.md).

## Quick Decisions

| Situation | Use |
| --- | --- |
| CSV has one molecule column and row targets | `--smiles-columns <col>` and standard `MoleculeDatapoint` / `MoleculeDataset` patterns |
| CSV has no header row | `--no-header-row`; Chemprop treats column `0` as the default SMILES column unless explicit integer column labels are used through Python/pandas-compatible parsing |
| CSV has two or more molecule columns | pass all molecule columns to `--smiles-columns`; Python API uses one component dataset per column and wraps them in `MulticomponentDataset` |
| CSV has reaction SMILES | `--reaction-columns <col>` and `ReactionDatapoint` / `ReactionDataset` with `CondensedGraphOfReactionFeaturizer` |
| Extra row-level numeric descriptors | `--descriptors-path descriptors.npz` containing one 2D `X_d` array shaped `n_rows x n_descriptors`, or `--descriptors-columns` for descriptor columns in the CSV |
| Extra atom or bond features before message passing | `.npz` created with `np.savez(path, *V_fs)` or `np.savez(path, *E_fs)`, one 2D array per row |
| Extra atom or bond descriptors after message passing | `.npz` created with `np.savez(path, *V_ds)` or `np.savez(path, *E_ds)`, one 2D array per row |
| Need generated molecular descriptors | `--molecule-featurizers morgan_binary`, `morgan_count`, `rdkit_2d`, `v1_rdkit_2d`, `v1_rdkit_2d_normalized`, or `charge` |
| Need fast on-the-fly graph building | `--use-cuikmolmaker-featurization` only for single-component molecule data with the optional extra installed and unsupported flags avoided |

## Common CLI Data Shapes

Use the bundled validator before training or prediction when a user reports shape or column errors:

```bash
python sub-skills/data-featurization/scripts/validate_chemprop_tabular_inputs.py \
  --csv data.csv \
  --smiles-columns smiles \
  --target-columns target \
  --descriptors-path descriptors.npz \
  --atom-features-path atom_features.npz
```

For multicomponent data, validate one file with multiple SMILES columns and component-indexed feature paths:

```bash
python sub-skills/data-featurization/scripts/validate_chemprop_tabular_inputs.py \
  --csv data.csv \
  --smiles-columns solute solvent \
  --component-descriptors 0 solute_descriptors.npz \
  --component-descriptors 1 solvent_descriptors.npz
```

For reaction data, validate reaction column syntax and descriptor row counts:

```bash
python sub-skills/data-featurization/scripts/validate_chemprop_tabular_inputs.py \
  --csv reactions.csv \
  --reaction-columns rxn \
  --descriptors-path reaction_descriptors.npz
```

For headerless CSVs, use zero-based column numbers in the validator and `--no-header-row` in Chemprop:

```bash
python sub-skills/data-featurization/scripts/validate_chemprop_tabular_inputs.py \
  --csv no_header.csv \
  --no-header-row \
  --smiles-columns 0 \
  --target-columns 1
```

The validator is intentionally conservative. It checks header/no-header handling, column presence, duplicate or overlapping column roles, nonempty SMILES/reaction/target/descriptor cells, reaction separator syntax, duplicate component feature indices, `.npz` loadability, expected row counts, descriptor matrix rank, and per-row atom/bond array rank. It does not replace RDKit chemistry validation or Chemprop training.

## Required Python API Signatures

Chemprop 2.2.3 accepts these public construction signatures for the core data path:

```python
MoleculeDatapoint(mol, y=None, weight=1.0, gt_mask=None, lt_mask=None, x_d=None, x_phase=None, name=None, V_f=None, E_f=None, V_d=None)
ReactionDatapoint(rct, pdt, y=None, weight=1.0, gt_mask=None, lt_mask=None, x_d=None, x_phase=None, name=None)
MoleculeDataset(data, featurizer=<factory>, n_workers=0)
MulticomponentDataset(datasets)
build_dataloader(dataset, batch_size=64, num_workers=0, class_balance=False, seed=None, shuffle=True, drop_last=None, **kwargs)
make_split_indices(mols, split="random", sizes=(0.8, 0.1, 0.1), seed=0, num_replicates=1, num_folds=None)
split_data_by_indices(data, train_indices=None, val_indices=None, test_indices=None)
```

Start with [references/data-api.md](references/data-api.md) for datapoints, datasets, dataloaders, split utilities, and batch fields.

Minimal molecule dataset pattern:

```python
import numpy as np
from chemprop.data import MoleculeDatapoint, MoleculeDataset, build_dataloader

data = [MoleculeDatapoint.from_smi("CCO", y=np.array([1.2]))]
dset = MoleculeDataset(data)
loader = build_dataloader(dset, batch_size=32, shuffle=True, seed=0)
```

Minimal reaction dataset pattern:

```python
import numpy as np
from chemprop.data import ReactionDatapoint, ReactionDataset
from chemprop.featurizers.molgraph import CondensedGraphOfReactionFeaturizer

data = [ReactionDatapoint.from_smi("[CH3:1][OH:2]>>[CH2:1]=[O:2]", y=np.array([0.3]))]
dset = ReactionDataset(data, featurizer=CondensedGraphOfReactionFeaturizer(mode_="reac_diff"))
```

Use [references/featurizers.md](references/featurizers.md) for featurizer choices, dimensions, reaction modes, molecule descriptor registry names, and `cuik-molmaker` caveats.

## Extra Features And Descriptors

Read [references/extra-features-descriptors.md](references/extra-features-descriptors.md) when a user asks how to create `.npz` files or why Chemprop says array lengths do not match.

Core meanings:

- `x_d` / `X_d`: row-level extra descriptors concatenated after molecular aggregation; one vector per datapoint.
- `V_f`: per-atom features concatenated to atom features before message passing; one `n_atoms x d_vf` matrix per molecule.
- `E_f`: per-bond features concatenated to bond features before message passing; one `n_bonds x d_ef` matrix per molecule.
- `V_d`: per-atom descriptors concatenated after message passing; one `n_atoms x d_vd` matrix per molecule.
- `E_d`: per-bond descriptors for atom/bond specialized models; one `n_bonds x d_ed` matrix per molecule.

For multicomponent CLI atom/bond paths, a single path means component `0`. To attach atom/bond features or descriptors to multiple molecule columns, pass component-index/path pairs for each component. Row-level `--descriptors-path` is global to the datapoint row; do not use it for atom- or bond-indexed arrays.

## Split And Loader Notes

- `make_split_indices(mols, split="random", sizes=(0.8, 0.1, 0.1), seed=0, num_replicates=1)` returns train, validation, and test index lists grouped by replicate.
- Split types include `random`, `random_with_repeated_smiles`, `scaffold_balanced`, `kennard_stone`, and `kmeans`.
- Structure-based splits require RDKit molecules; random splitting can use any sized object with the same length as the dataset.
- `split_data_by_indices(data, train_indices, val_indices, test_indices)` handles molecule, reaction, and multicomponent datapoint collections.
- `build_dataloader` chooses the correct collate function for molecule, reaction, multicomponent, `cuik-molmaker`, or atom/bond datasets.
- `class_balance=True` is only appropriate for single-task classification labels and conflicts with ordinary regression assumptions.

## Troubleshooting First Pass

Use [references/troubleshooting.md](references/troubleshooting.md) for detailed fixes. Fast triage:

- Import failure: confirm Python version is compatible with Chemprop 2.2.3 and core dependencies import; optional extras are not installed by default.
- Invalid SMILES or reaction: check for empty strings, malformed `reactants>agents>products` or `reactants>>products`, and atom maps for reaction CGR tasks.
- No-header mode: pass `--no-header-row`; otherwise Chemprop treats the first row as headers and shifts data rows unexpectedly.
- Overlapping columns: a column should not simultaneously be a SMILES/reaction input, target, descriptor, weight, split, and ignored metadata column.
- `.npz` mismatch: row count must match CSV rows; atom/bond matrices must match RDKit atom/bond counts in the same order.
- Wrong flag family: use `--smiles-columns` for molecules, `--reaction-columns` with `--rxn-mode`/`--reaction-mode` for reactions, and component-indexed atom/bond paths for multicomponent inputs.
- Scaling surprise: `--no-descriptor-scaling`, `--no-atom-feature-scaling`, `--no-atom-descriptor-scaling`, `--no-bond-feature-scaling`, and `--no-bond-descriptor-scaling` preserve externally scaled inputs.
- `cuik-molmaker` errors: install the optional package and avoid unsupported settings such as reactions, multiple molecule components, `--keep-h`, `--ignore-stereo`, or `--reorder-atoms`.

## Verification Ideas

For later usability verification, include these difficult cases:

- Multicomponent CSV with `solute` and `solvent` columns plus separate descriptor `.npz` files; assertions catch that one descriptor file has one fewer row than the CSV and that component index `2` is out of range.
- V1-converted-model featurizer choice case: a CLI or Python preflight that selects `--multi-hot-atom-featurizer-mode V1` and `v1_rdkit_2d_normalized`, then asserts the skill explains why Chemprop v2 defaults differ from v1-compatible featurization.

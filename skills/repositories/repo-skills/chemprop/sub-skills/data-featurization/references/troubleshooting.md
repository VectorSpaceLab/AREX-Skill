# Data Featurization Troubleshooting

Use this guide for Chemprop 2.2.3 failures involving imports, CSV columns, SMILES/reactions, `.npz` extras, featurizer flags, dataloaders, and optional acceleration. For a fast local preflight, run `scripts/validate_chemprop_tabular_inputs.py` from this sub-skill.

## Import Or Installation Failures

Symptoms:

- `ModuleNotFoundError: No module named 'chemprop'`.
- RDKit, Torch, Lightning, or sklearn import errors.
- `chemprop --help` or `chemprop train --help` fails before parsing user data.

Actions:

1. Confirm the active Python version satisfies Chemprop’s package constraint: Python `>=3.11,<3.15`.
2. Confirm the package imports:
   ```bash
   python -c "import chemprop; print(chemprop.__version__)"
   ```
3. Confirm the CLI is installed:
   ```bash
   chemprop --help
   ```
4. Run dependency checking if pip was used:
   ```bash
   python -m pip check
   ```
5. Do not require CUDA just to inspect data or featurizers. CPU Torch works for validation and small shape smoke tests.
6. Treat `hpopt`, docs, notebooks, and `cuik-molmaker` as optional extras unless the user’s workflow specifically uses them.

## CPU Vs CUDA Expectations

Data construction, SMILES parsing, `.npz` validation, split construction, and ordinary molgraph featurization can run on CPU. CUDA matters for training throughput, not for basic schema validation.

If a user sees CUDA or device errors while working only on data:

- Reproduce with a minimal Python script that creates datapoints and a dataset but does not instantiate or train a model.
- If the minimal data script passes, route model/device debugging to training or modeling skills.
- If the failure mentions `cuik-molmaker`, check optional dependency installation and its unsupported flags.

## Invalid SMILES Or Reaction Strings

Symptoms:

- RDKit parse errors.
- `Reactant cannot be None` or `Product cannot be None`.
- Split methods or featurizers fail on `None` molecules.
- Reaction CGR shapes look wrong.

Actions:

1. Check for empty strings, whitespace-only cells, and missing CSV values in input columns.
2. For molecule data, validate each `--smiles-columns` value independently.
3. For reaction data, use `reactants>agents>products` or `reactants>>products` syntax. Chemprop parses a single reaction string by splitting on `>`.
4. Use `--reaction-columns` and `--rxn-mode` / `--reaction-mode` for reaction CGR data. Do not encode separate reactant/product columns as multicomponent molecule columns unless the intended model is a multicomponent molecule model.
5. Use atom maps for chemically meaningful reaction CGR alignment. Unmapped reactions may parse but produce poor or surprising reactant/product matching.
6. If the workflow uses atom/bond targets, route target ordering and `--reorder-atoms` questions to specialized tasks.

Minimal parse check:

```python
from rdkit import Chem

for smi in smiles:
    mol = Chem.MolFromSmiles(smi)
    assert mol is not None, smi
```

Reaction check:

```python
from chemprop.data import ReactionDatapoint

for rxn in reactions:
    dp = ReactionDatapoint.from_smi(rxn)
    assert dp.rct is not None and dp.pdt is not None
```

## CSV Column Errors

Symptoms:

- Parser says a SMILES, reaction, target, split, or descriptor column does not exist.
- The first column is treated as SMILES unexpectedly.
- The first data row disappears because a headerless CSV was parsed as headers.
- A column is accidentally reused as input, target, descriptor, split, weight, or ignored metadata.
- Multicomponent rows are interpreted as single-molecule rows.

Actions:

1. Print CSV headers exactly as parsed:
   ```python
   import pandas as pd
   print(list(pd.read_csv("data.csv", nrows=0).columns))
   ```
2. Add `--no-header-row` when the CSV has no header; otherwise Chemprop treats the first row as column names and shifts data rows.
3. Use `--smiles-columns` for one or more molecule columns.
4. Use `--reaction-columns` for reaction columns, not `--smiles-columns`.
5. Use `--target-columns` for ordinary row targets; route atom/bond target column details to specialized tasks.
6. Use `--ignore-columns` for non-feature metadata that should not become targets.
7. Use `--descriptors-columns` only for numeric row-level descriptor columns that should feed the model as `x_d`.
8. Do not reuse one column for incompatible roles. Chemprop infers default target columns by excluding input, ignored, split, weight, and descriptor columns, so overlaps can silently change targets.
9. Validate with the bundled script before rerunning a long command.

## `.npz` Row Count Mismatches

Symptoms:

- Chemprop says number of molecules and descriptors/features must have the same length.
- The validator reports an archive row count different from CSV row count.
- Prediction fails although training succeeded because prediction descriptors still use train-set row counts.

Actions:

1. Load the archive and inspect keys/shapes:
   ```python
   import numpy as np
   z = np.load("features.npz", allow_pickle=True)
   print(z.files)
   print([z[k].shape for k in z.files])
   ```
2. For `--descriptors-path`, expect one 2D matrix with `n_rows` rows.
3. For atom/bond feature/descriptor paths, expect one 2D matrix per CSV row.
4. Validate train, validation, test, prediction, and calibration CSV/NPZ pairs separately.
5. Confirm no CSV filtering, sorting, duplicate removal, or split export happened after feature files were generated.

## Atom/Bond Matrix Shape Mismatches

Symptoms:

- `Input molecule must have same number of atoms as len(atom_features_extra)`.
- `Input molecule must have same number of bonds as len(bond_features_extra)`.
- Model input dimension mismatch after adding extra features.

Actions:

1. Atom matrices must be `n_atoms x d`, where `n_atoms == mol.GetNumAtoms()` for the same row.
2. Bond matrices must be `n_bonds x d`, where `n_bonds == mol.GetNumBonds()`, not directed edge count.
3. If hydrogens, stereochemistry, atom ordering, or atom maps changed between feature generation and Chemprop parsing, regenerate features with the same SMILES options.
4. If using Python API, instantiate `SimpleMoleculeMolGraphFeaturizer(extra_atom_fdim=d_vf, extra_bond_fdim=d_ef)` to match `V_f` and `E_f` dimensions.
5. For reactions, do not expect `CondensedGraphOfReactionFeaturizer` to use `atom_features_extra` or `bond_features_extra`; it warns that they are unsupported.

## Config Or CLI Flag Misuse

Common fixes:

- Use `--smiles-columns solute solvent` for multicomponent molecule models, not repeated full commands.
- Use component-indexed paths for multicomponent atom/bond features, such as `--atom-features-path 0 solute.npz --atom-features-path 1 solvent.npz`.
- Use `--descriptors-path` for row-level descriptors shared by the row, not for per-atom matrices.
- Use `--molecule-featurizers` for built-in molecular descriptors; the older `--features-generators` name is not the primary v2 spelling.
- Use `--rxn-mode` / `--reaction-mode` with reaction data and repeat the same reaction-mode-compatible choices during prediction.
- Disable scaling only when features/descriptors were intentionally pre-scaled or should remain in original units.

## Missing Checkpoint Or Model Artifacts

This sub-skill validates data and featurizers, but users may encounter artifact errors when data commands are embedded in prediction/fingerprint workflows.

Triage:

- If the error is about `--model-path`, checkpoint contents, ensemble directories, or prediction outputs, route to prediction/inference or training skills.
- Still validate prediction CSV and descriptor paths here, because model artifact errors can hide secondary data mismatches.
- Ensure prediction uses the same feature families as training. A model trained with extra descriptors expects compatible extra descriptors at prediction time.

## Optional Extras

### `cuik-molmaker`

Symptoms:

- `cuik-molmaker is not installed`.
- `CuikmolmakerMolGraphFeaturizer requires cuik-molmaker package`.
- Unsupported flag messages for `--keep-h`, `--ignore-stereo`, or `--reorder-atoms`.

Actions:

1. Install the optional dependency only if accelerated molecule featurization is required.
2. Avoid unsupported molecule parsing flags with `--use-cuikmolmaker-featurization`.
3. Do not use this path for reaction CGR featurization.
4. If memory savings disappear, remove `--molecule-featurizers` and precompute descriptors into `--descriptors-path`.

### `hpopt`, docs, notebooks

Hyperparameter optimization, documentation builds, and notebook extras are not needed for data schema validation. If an import failure names an optional package from those workflows, either install the relevant extra for that workflow or reroute away from the optional feature.

## Dataloader Failures

Symptoms:

- Batch collation fails.
- BatchNorm complains about batch size one.
- Class balance sampling fails.

Actions:

1. Use Chemprop’s `build_dataloader` instead of a raw PyTorch `DataLoader` unless you intentionally provide a custom collate function.
2. For datasets where `len(dataset) % batch_size == 1`, allow `drop_last=True` or choose a different batch size.
3. Use `class_balance=True` only for single-task classification data with valid binary labels.
4. Inspect the first dataset item before building the loader:
   ```python
   item = dset[0]
   print(item.mg.V.shape, item.mg.E.shape, item.y)
   ```

## Split Failures

Symptoms:

- Scaffold, Kennard-Stone, or k-means split fails on invalid molecules.
- `num_folds` error.
- Validation split unexpectedly empty.

Actions:

1. `num_folds` was removed; use `num_replicates`.
2. `sizes` must be a 3-tuple `(train, val, test)`.
3. If `sizes[1] == 0` or `sizes[2] == 0`, validation or test output can be empty by design.
4. Structure-based splits require valid RDKit molecules; use `random` only for non-structure smoke tests.
5. `random_with_repeated_smiles` keeps repeated canonical SMILES together and can produce imbalanced splits if duplicates are heavy.

## Fast Diagnostic Sequence

Run this sequence before changing model code:

```bash
python sub-skills/data-featurization/scripts/validate_chemprop_tabular_inputs.py \
  --csv data.csv \
  --smiles-columns smiles \
  --target-columns target \
  --descriptors-path descriptors.npz
```

Then run a minimal API smoke test:

```python
import numpy as np
from chemprop.data import MoleculeDatapoint, MoleculeDataset, build_dataloader

data = [MoleculeDatapoint.from_smi("CCO", y=np.array([1.0]))]
dset = MoleculeDataset(data)
item = dset[0]
assert item.mg.V.ndim == 2 and item.mg.E.ndim == 2
loader = build_dataloader(dset, batch_size=1, shuffle=False)
next(iter(loader))
```

If both pass, the remaining failure likely belongs to training configuration, model assembly, prediction artifacts, or specialized task semantics rather than base data featurization.

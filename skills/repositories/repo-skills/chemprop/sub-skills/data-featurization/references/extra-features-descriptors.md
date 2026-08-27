# Extra Features And Descriptors

Chemprop supports several kinds of optional numeric inputs. Most failures come from confusing row-level descriptors with atom/bond matrices or from saving `.npz` files in a shape that does not match the CSV row order.

## Vocabulary

| Chemprop name | CLI flag | Python field | Required shape | Used when |
| --- | --- | --- | --- | --- |
| Extra datapoint descriptors | `--descriptors-path` | `x_d` / dataset `X_d` | `(n_rows, d_xd)` | after molecular aggregation |
| Extra atom features | `--atom-features-path` | `V_f` / dataset `V_fs` | one `(n_atoms_i, d_vf)` array per row | before message passing |
| Extra bond features | `--bond-features-path` | `E_f` / dataset `E_fs` | one `(n_bonds_i, d_ef)` array per row | before message passing |
| Extra atom descriptors | `--atom-descriptors-path` | `V_d` / dataset `V_ds` | one `(n_atoms_i, d_vd)` array per row | after message passing |
| Extra bond descriptors | `--bond-descriptors-path` | `E_d` | one `(n_bonds_i, d_ed)` array per row | specialized atom/bond models after message passing |
| Inline descriptor columns | `--descriptors-columns` | `x_d` after parsing | one numeric value per listed column per row | after molecular aggregation |

`V_f`, `E_f`, `V_d`, and `E_d` are list-like because molecules have different atom and bond counts. `X_d` is one rectangular 2D matrix because it has exactly one row per CSV row.

## Saving `.npz` Files

### Row-level descriptors

```python
import numpy as np

X_d = np.asarray([
    [298.15, 1.0],
    [310.15, 0.5],
], dtype=float)
np.savez("descriptors.npz", X_d)
```

The archive should contain one array shaped `n_rows x n_descriptors`. A 1D array is ambiguous; reshape it to `(n_rows, 1)`.

### Atom features or descriptors

```python
from rdkit import Chem
import numpy as np

smiles = ["CCO", "CCN"]
V_fs = []
for smi in smiles:
    mol = Chem.MolFromSmiles(smi)
    n_atoms = mol.GetNumAtoms()
    V_fs.append(np.zeros((n_atoms, 3), dtype=float))

np.savez("atom_features.npz", *V_fs)
```

The archive contains one 2D array per row. Array key names are not semantically important to NumPy’s positional save/load behavior; row order is important. Chemprop expects the arrays to correspond exactly to the input CSV order.

### Bond features or descriptors

```python
E_fs = []
for smi in smiles:
    mol = Chem.MolFromSmiles(smi)
    n_bonds = mol.GetNumBonds()
    E_fs.append(np.zeros((n_bonds, 2), dtype=float))

np.savez("bond_features.npz", *E_fs)
```

Use `n_bonds`, not `2 * n_bonds`. Chemprop duplicates bond feature vectors internally for directed graph edges during molgraph construction.

## CLI Patterns

Single molecule column with row-level descriptors:

```bash
chemprop train \
  -i data.csv \
  -t regression \
  --smiles-columns smiles \
  --target-columns y \
  --descriptors-path descriptors.npz
```

Single molecule column with atom and bond features:

```bash
chemprop train \
  -i data.csv \
  -t regression \
  --smiles-columns smiles \
  --target-columns y \
  --atom-features-path atom_features.npz \
  --bond-features-path bond_features.npz
```

Multicomponent molecule columns with component-specific features:

```bash
chemprop train \
  -i data.csv \
  -t regression \
  --smiles-columns solute solvent \
  --target-columns y \
  --atom-features-path 0 solute_atom_features.npz \
  --atom-features-path 1 solvent_atom_features.npz
```

Inline descriptors in the CSV:

```bash
chemprop train \
  -i data.csv \
  -t regression \
  --smiles-columns smiles \
  --target-columns y \
  --descriptors-columns temperature pressure
```

Prediction and calibration data must use descriptor/feature files with row counts matching their own CSV files. Calibration descriptor paths use `--cal-descriptors-path`, `--cal-atom-features-path`, `--cal-atom-descriptors-path`, `--cal-bond-features-path`, and `--cal-bond-descriptors-path`.

## Python API Pattern

```python
import numpy as np
from rdkit import Chem
from chemprop.data import MoleculeDatapoint, MoleculeDataset
from chemprop.featurizers.molgraph import SimpleMoleculeMolGraphFeaturizer

smi = "CCO"
mol = Chem.MolFromSmiles(smi)
V_f = np.zeros((mol.GetNumAtoms(), 3), dtype=float)
E_f = np.zeros((mol.GetNumBonds(), 2), dtype=float)
V_d = np.ones((mol.GetNumAtoms(), 4), dtype=float)
x_d = np.array([298.15, 1.0], dtype=float)

dp = MoleculeDatapoint.from_smi(smi, y=np.array([1.2]), x_d=x_d, V_f=V_f, E_f=E_f, V_d=V_d)
featurizer = SimpleMoleculeMolGraphFeaturizer(extra_atom_fdim=3, extra_bond_fdim=2)
dset = MoleculeDataset([dp], featurizer=featurizer)
item = dset[0]

assert item.x_d.shape == (2,)
assert item.V_d.shape == (mol.GetNumAtoms(), 4)
assert item.mg.V.shape[0] == mol.GetNumAtoms()
assert item.mg.E.shape[0] == 2 * mol.GetNumBonds()
```

If you pass `V_f` or `E_f` in datapoints, construct the molgraph featurizer with matching `extra_atom_fdim` and `extra_bond_fdim`. Otherwise, the arrays may be accepted by the dataset but later produce graph feature dimensions that do not match model construction.

## Scaling Behavior

By default, CLI training scales supported extra inputs unless disabled:

| Input | Disable flag |
| --- | --- |
| row-level descriptors | `--no-descriptor-scaling` |
| atom features | `--no-atom-feature-scaling` |
| atom descriptors | `--no-atom-descriptor-scaling` |
| bond features | `--no-bond-feature-scaling` |
| bond descriptors | `--no-bond-descriptor-scaling` |

Python datasets expose `normalize_inputs`:

```python
xd_scaler = dset.normalize_inputs("X_d")
vf_scaler = dset.normalize_inputs("V_f")
ef_scaler = dset.normalize_inputs("E_f")
vd_scaler = dset.normalize_inputs("V_d")
dset.reset()
```

For atom/bond arrays, scaling is fit on the concatenation of all per-row matrices, then written back as per-row matrices. If data was externally scaled, pass the matching no-scaling CLI flag or avoid `normalize_inputs` for that key.

## Validation Checklist

Before a Chemprop run:

1. Confirm the CSV has all requested SMILES, reaction, target, ignore, weight, and descriptor columns.
2. Confirm `--smiles-columns` and `--reaction-columns` are not accidentally swapped.
3. Confirm `X_d` has exactly `n_rows` rows.
4. Confirm atom/bond `.npz` archives contain exactly `n_rows` arrays for a single component or for each supplied component.
5. Confirm each atom-feature/descriptor array row count equals RDKit `mol.GetNumAtoms()` for the corresponding SMILES.
6. Confirm each bond-feature/descriptor array row count equals RDKit `mol.GetNumBonds()` for the corresponding SMILES.
7. Confirm arrays are 2D, finite where required by your workflow, and numeric.
8. For multicomponent data, confirm component index `0` maps to the first `--smiles-columns` entry, component index `1` maps to the second, and so on.
9. For reaction data, do not expect atom/bond extra feature matrices to be consumed by `CondensedGraphOfReactionFeaturizer`.
10. For prediction/calibration, validate every CSV/NPZ pair independently; train-set row counts do not apply to prediction files.

The bundled validator automates the column, row-count, duplicate-index, and array-rank parts of this checklist.

## Common Mismatch Examples

### `X_d` saved as one array per row

Wrong for row-level descriptors:

```python
np.savez("descriptors.npz", *[np.array([1.0, 2.0]), np.array([3.0, 4.0])])
```

Right:

```python
np.savez("descriptors.npz", np.array([[1.0, 2.0], [3.0, 4.0]]))
```

### Bond features saved for directed edges

Wrong:

```python
E_f = np.zeros((2 * mol.GetNumBonds(), 5))
```

Right:

```python
E_f = np.zeros((mol.GetNumBonds(), 5))
```

### Multicomponent feature path missing component index

A single feature path applies to component `0` only. If both solute and solvent need atom features, provide both component-indexed paths.

```bash
--atom-features-path 0 solute_atoms.npz --atom-features-path 1 solvent_atoms.npz
```

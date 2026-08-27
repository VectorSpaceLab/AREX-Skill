# Chemprop Data API Reference

This reference covers Chemprop 2.2.3 data objects and loader/split utilities. It is for future agents who need to build or debug data inputs without reopening the source repository.

## Imports

```python
import numpy as np
from rdkit import Chem

from chemprop.data import (
    MoleculeDatapoint,
    ReactionDatapoint,
    MoleculeDataset,
    ReactionDataset,
    MulticomponentDataset,
    build_dataloader,
    make_split_indices,
    split_data_by_indices,
)
from chemprop.featurizers.molgraph import (
    SimpleMoleculeMolGraphFeaturizer,
    CondensedGraphOfReactionFeaturizer,
)
```

Chemprop data classes are regular Python objects around RDKit molecules, reaction molecule pairs, numeric targets, weights, masks, and optional feature arrays. Unknown regression targets are represented with `np.nan`; Chemprop replaces `np.nan` values in extra features/descriptors with `0` during datapoint initialization.

## Public Signatures

Use these Chemprop 2.2.3 signatures when answering API questions or writing minimal scripts:

```python
MoleculeDatapoint(
    mol,
    y=None,
    weight=1.0,
    gt_mask=None,
    lt_mask=None,
    x_d=None,
    x_phase=None,
    name=None,
    V_f=None,
    E_f=None,
    V_d=None,
)
ReactionDatapoint(
    rct,
    pdt,
    y=None,
    weight=1.0,
    gt_mask=None,
    lt_mask=None,
    x_d=None,
    x_phase=None,
    name=None,
)
MoleculeDataset(data, featurizer=<factory>, n_workers=0)
MulticomponentDataset(datasets)
build_dataloader(dataset, batch_size=64, num_workers=0, class_balance=False, seed=None, shuffle=True, drop_last=None, **kwargs)
make_split_indices(mols, split="random", sizes=(0.8, 0.1, 0.1), seed=0, num_replicates=1, num_folds=None)
split_data_by_indices(data, train_indices=None, val_indices=None, test_indices=None)
```

`ReactionDataset(data, featurizer=<factory>, n_workers=0)` follows the same dataset pattern as `MoleculeDataset` but expects `ReactionDatapoint` objects and a reaction molgraph featurizer.

## Datapoints

### `MoleculeDatapoint`

Create from a SMILES string:

```python
dp = MoleculeDatapoint.from_smi(
    "CCO",
    y=np.array([1.2], dtype=float),
    x_d=np.array([298.15, 1.0], dtype=float),
)
```

Important fields:

| Field | Shape | Meaning |
| --- | --- | --- |
| `mol` | RDKit `Mol` | molecule for graph featurization |
| `y` | `(n_tasks,)` or `None` | row targets; use `np.nan` for missing task labels |
| `weight` | scalar | datapoint loss weight |
| `gt_mask`, `lt_mask` | `(n_tasks,)` or `None` | inequality regression masks |
| `x_d` | `(d_xd,)` or `None` | row-level descriptors concatenated after aggregation |
| `x_phase` | list-like or `None` | phase indicator used by spectra workflows |
| `V_f` | `(n_atoms, d_vf)` or `None` | atom features before message passing |
| `E_f` | `(n_bonds, d_ef)` or `None` | bond features before message passing |
| `V_d` | `(n_atoms, d_vd)` or `None` | atom descriptors after message passing |
| `name` | string or `None` | identifier; defaults to the SMILES string in `from_smi` |

SMILES parsing options for `from_smi` are `keep_h=False`, `add_h=False`, `ignore_stereo=False`, and `reorder_atoms=False`. For atom/bond target workflows, specialized datapoints default to atom reordering; route detailed target semantics to the specialized molecular tasks skill.

### `ReactionDatapoint`

Create from a reaction string or a `(reactants, products)` tuple:

```python
rxn_dp = ReactionDatapoint.from_smi(
    "[CH3:1][OH:2]>>[CH2:1]=[O:2]",
    y=np.array([0.3], dtype=float),
)

rxn_dp2 = ReactionDatapoint.from_smi(("[CH3:1][OH:2]", "[CH2:1]=[O:2]"))
```

A string reaction is split as `reactants>agents>products`; if the agent segment is nonempty, Chemprop appends it to the reactants as `reactants.agents`. Reaction datapoints store `rct` and `pdt` RDKit molecules and reject `None` reactants/products. Reaction-level `x_d`, targets, weights, and masks use the same row-level conventions as molecule datapoints.

Reaction graph featurization uses `CondensedGraphOfReactionFeaturizer`; extra atom and bond feature arrays are not supported by this featurizer even though the low-level call signature accepts parity arguments.

## Datasets

### `MoleculeDataset`

```python
data = [
    MoleculeDatapoint.from_smi("CCO", y=np.array([1.2])),
    MoleculeDatapoint.from_smi("CCN", y=np.array([0.7])),
]
dset = MoleculeDataset(data, featurizer=SimpleMoleculeMolGraphFeaturizer())
```

Useful properties:

| Property | Meaning |
| --- | --- |
| `len(dset)` | number of datapoints |
| `dset.Y` | target matrix shaped `(n_rows, n_tasks)` |
| `dset.X_d` | row-level descriptor matrix or object array containing `None` |
| `dset.V_fs`, `dset.E_fs`, `dset.V_ds` | lists of per-row matrices or `None` entries |
| `dset.d_xd`, `dset.d_vf`, `dset.d_ef`, `dset.d_vd` | inferred extra dimensions |
| `dset.names` | datapoint names |
| `dset.cache` | when `True`, precomputes molgraphs; when `False`, featurizes on the fly |

`MoleculeDataset.__getitem__` returns a `Datum` with `mg`, `V_d`, `x_d`, `y`, `weight`, `lt_mask`, and `gt_mask`. The molgraph contains atom features `V`, bond features `E`, `edge_index`, and `rev_edge_index`.

Dataset setters validate that row-level arrays/lists have the same length as the dataset. Atom/bond feature shape mismatches are caught when the molgraph featurizer is called.

### `ReactionDataset`

```python
rxn_data = [ReactionDatapoint.from_smi("[CH3:1][OH:2]>>[CH2:1]=[O:2]", y=np.array([0.3]))]
rxn_dset = ReactionDataset(
    rxn_data,
    featurizer=CondensedGraphOfReactionFeaturizer(mode_="reac_diff"),
)
```

`ReactionDataset` supports row-level descriptors `x_d`/`X_d`, targets, weights, and masks. It does not support molecule-style `V_f`, `E_f`, or `V_d` on `ReactionDatapoint`.

### `MulticomponentDataset`

Use multicomponent datasets when each row contains multiple molecule columns, such as solute and solvent. In the Python API, build one component dataset per molecule column and wrap them:

```python
solute = [
    MoleculeDatapoint.from_smi("CCO", y=np.array([1.2])),
    MoleculeDatapoint.from_smi("CCN", y=np.array([0.7])),
]
solvent = [
    MoleculeDatapoint.from_smi("O", y=np.array([1.2])),
    MoleculeDatapoint.from_smi("CO", y=np.array([0.7])),
]
mc_dset = MulticomponentDataset([
    MoleculeDataset(solute),
    MoleculeDataset(solvent),
])
```

All component datasets must have the same number of rows. Extra atom/bond feature arrays belong to the component they describe. Row-level targets are conceptually per datapoint; keep target arrays aligned across components.

## Normalization And Reset

Dataset methods:

```python
target_scaler = dset.normalize_targets()
xd_scaler = dset.normalize_inputs("X_d")
vf_scaler = dset.normalize_inputs("V_f")
ef_scaler = dset.normalize_inputs("E_f")
vd_scaler = dset.normalize_inputs("V_d")
dset.reset()
```

`MoleculeDataset.normalize_inputs` accepts `X_d`, `V_f`, `E_f`, and `V_d`. The base row-level mixin accepts only `X_d`. For atom and bond arrays, Chemprop concatenates all per-row matrices, fits/transforms with `StandardScaler`, and writes transformed matrices back per datapoint. If a feature dimension is absent, the method returns the provided scaler unchanged.

Use the CLI flags `--no-descriptor-scaling`, `--no-atom-feature-scaling`, `--no-atom-descriptor-scaling`, `--no-bond-feature-scaling`, and `--no-bond-descriptor-scaling` when externally scaled arrays must remain unchanged.

## Splitting

```python
train_idx, val_idx, test_idx = make_split_indices(
    dset.mols,
    split="random",
    sizes=(0.8, 0.1, 0.1),
    seed=0,
    num_replicates=1,
)
train_data, val_data, test_data = split_data_by_indices(dset.data, train_idx, val_idx, test_idx)
```

Supported split types:

- `random`: random rows.
- `random_with_repeated_smiles`: keeps identical canonical SMILES in the same split.
- `scaffold_balanced`: molecular scaffold split with atom maps removed before scaffold calculation.
- `kennard_stone`: structure-based Kennard-Stone split with Morgan fingerprints and Jaccard distance.
- `kmeans`: structure-based cluster split with Morgan fingerprints and Jaccard distance.

`make_split_indices` returns a tuple of replicate lists: `([train_indices_for_rep0, ...], [val_indices_for_rep0, ...], [test_indices_for_rep0, ...])`. If `sizes[1] == 0` or `sizes[2] == 0`, validation or test lists may be empty. If all data is train, use `sizes=(1.0, 0.0, 0.0)`.

For multicomponent Python data, pass a list of component datapoint lists to `split_data_by_indices`; it returns component-preserving split groups.

## Dataloaders

```python
loader = build_dataloader(
    dset,
    batch_size=64,
    num_workers=0,
    class_balance=False,
    seed=0,
    shuffle=True,
)
```

`build_dataloader` chooses the right collate function for `MoleculeDataset`, `ReactionDataset`, `MulticomponentDataset`, `CuikmolmakerDataset`, or atom/bond datasets. If the dataset length modulo batch size is `1`, it sets `drop_last=True` by default to avoid batch-normalization issues.

Use `class_balance=True` only for single-task classification datasets. For regression, multitask, or data with missing targets, leave it `False`.

## Shape Smoke Tests

Use these checks before model assembly:

```python
first = dset[0]
assert first.mg.V.ndim == 2
assert first.mg.E.ndim == 2
assert first.y is None or first.y.ndim == 1
assert dset.d_xd == 0 or dset.X_d.shape[0] == len(dset)
```

For molecule extra atom/bond arrays:

```python
mol = data[0].mol
if data[0].V_f is not None:
    assert data[0].V_f.shape[0] == mol.GetNumAtoms()
if data[0].E_f is not None:
    assert data[0].E_f.shape[0] == mol.GetNumBonds()
if data[0].V_d is not None:
    assert data[0].V_d.shape[0] == mol.GetNumAtoms()
```

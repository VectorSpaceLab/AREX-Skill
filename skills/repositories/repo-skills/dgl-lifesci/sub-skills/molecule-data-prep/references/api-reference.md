# Molecule Data Prep API Reference

This reference distills repository source, docs, tests, and installed-package inspection for DGL-LifeSci 0.3.1. Use it as the local API guide for data preparation tasks; do not rely on the original checkout being present.

## Import Surface

Common imports:

```python
import pandas as pd
from dgllife.data import MoleculeCSVDataset, UnlabeledSMILES
from dgllife.utils import (
    smiles_to_bigraph, smiles_to_complete_graph,
    mol_to_bigraph, mol_to_complete_graph,
    CanonicalAtomFeaturizer, CanonicalBondFeaturizer,
    AttentiveFPAtomFeaturizer, AttentiveFPBondFeaturizer,
    RandomSplitter, ScaffoldSplitter, MolecularWeightSplitter,
    ConsecutiveSplitter, SingleTaskStratifiedSplitter,
    Meter, EarlyStopping,
)
```

Verified installed facts: `dgllife` 0.3.1 imports with DGL 1.1.3, PyTorch CPU, RDKit, scikit-learn, NumPy/SciPy, and pandas. A smoke graph for `CCO` with `CanonicalAtomFeaturizer()` has 3 nodes and node feature `h` with shape `(3, 74)`.

## Graph Construction

| API | Verified signature | Use when | Main gotchas |
| --- | --- | --- | --- |
| `smiles_to_bigraph` | `(smiles, add_self_loop=False, node_featurizer=None, edge_featurizer=None, canonical_atom_order=True, explicit_hydrogens=False, num_virtual_nodes=0)` | Input is a SMILES string and graph topology should follow molecular bonds in both directions. | Returns `None` for RDKit-invalid SMILES. With `canonical_atom_order=True`, atom order may change. |
| `mol_to_bigraph` | `(mol, add_self_loop=False, node_featurizer=None, edge_featurizer=None, canonical_atom_order=True, explicit_hydrogens=False, num_virtual_nodes=0)` | Input is already an RDKit `Mol`. | Preserve atom-map/reaction ordering with `canonical_atom_order=False`. |
| `smiles_to_complete_graph` | `(smiles, add_self_loop=False, node_featurizer=None, edge_featurizer=None, canonical_atom_order=True, explicit_hydrogens=False, num_virtual_nodes=0)` | Models expect all atom pairs connected. | Edge count grows quadratically; use only when the downstream model expects complete graphs. |
| `mol_to_complete_graph` | `(mol, add_self_loop=False, node_featurizer=None, edge_featurizer=None, canonical_atom_order=True, explicit_hydrogens=False, num_virtual_nodes=0)` | RDKit `Mol` plus complete topology. | Edge features from bond featurizers are not meaningful for non-bonded complete-graph edges unless using a complete-graph-aware featurizer. |
| `smiles_to_nearest_neighbor_graph` | `(smiles, coordinates, neighbor_cutoff, max_num_neighbors=None, p_distance=2, add_self_loop=False, node_featurizer=None, edge_featurizer=None, canonical_atom_order=True, keep_dists=False, dist_field='dist', explicit_hydrogens=False, num_virtual_nodes=0)` | 3D coordinates drive neighborhood topology. | Requires one coordinate row per atom after hydrogen/canonicalization choices. |
| `k_nearest_neighbors` | `(coordinates, neighbor_cutoff, max_num_neighbors=None, p_distance=2, self_loops=False)` | Building or debugging coordinate-based graphs. | Edges are not guaranteed to be sorted by distance. |

Graph-constructor behavior from tests:

- `smiles_to_bigraph('CCO', add_self_loop=True)` adds molecular edges plus one self-loop per atom.
- `smiles_to_complete_graph('CCO', add_self_loop=False)` creates directed edges for all ordered atom pairs except self-pairs, so 3 atoms produce 6 edges.
- `explicit_hydrogens=True` increases node counts and changes feature rows; only use it when the model/data contract expects explicit H atoms.
- `num_virtual_nodes=N` appends virtual nodes and extends feature tensors with a virtual-node indicator column.

## Featurizers

| API | Verified signature | Default fields | Typical shape facts |
| --- | --- | --- | --- |
| `CanonicalAtomFeaturizer` | `(atom_data_field='h')` | `g.ndata['h']` | `feat_size()` and `feat_size('h')` are 74. |
| `CanonicalBondFeaturizer` | `(bond_data_field='e', self_loop=False)` | `g.edata['e']` | Set `self_loop=True` when constructing graphs with self-loops and expecting self-loop edge features. |
| `BaseAtomFeaturizer` | `(featurizer_funcs, feat_sizes=None)` | user-defined | `feat_size(name)` reports per-field width when names match. |
| `BaseBondFeaturizer` | `(featurizer_funcs, feat_sizes=None, self_loop=False)` | user-defined | Bond index `i` maps to graph edges `2i` and `2i+1` for bidirected graphs. |
| `AttentiveFPAtomFeaturizer` | `(atom_data_field='h')` | `h` | Match with AttentiveFP-style models. |
| `AttentiveFPBondFeaturizer` | `(bond_data_field='e', self_loop=False)` | `e` | Match with AttentiveFP-style models. |
| `PretrainAtomFeaturizer` | `(atomic_number_types=None, chiral_types=None)` | `atomic_number`, `chirality_type` | Used by pretraining-style GIN inputs, not canonical `h`. |
| `PretrainBondFeaturizer` | `(bond_types=None, bond_direction_types=None, self_loop=True)` | `bond_type`, `bond_direction_type` | Defaults to self-loop-aware bond encodings. |
| `PAGTNAtomFeaturizer` | `(atom_data_field='h')` | `h` | Use with PAGTN-style graph preparation. |
| `PAGTNEdgeFeaturizer` | `(bond_data_field='e', max_length=5)` | `e` | Path-aware edge features, not the same as canonical bond features. |

Low-level atom descriptors include atom type/atomic number, degree, total degree, valence, hybridization, hydrogen count, formal charge, radical electrons, aromaticity, ring membership, chirality, and mass. Low-level bond descriptors include bond type, conjugation, ring membership, stereo, and direction. Combine descriptors with `ConcatFeaturizer` and wrap them in `BaseAtomFeaturizer` or `BaseBondFeaturizer` when custom fields are needed.

## Dataset Classes

### `MoleculeCSVDataset`

Verified signature:

```python
MoleculeCSVDataset(
    df, smiles_to_graph=None, node_featurizer=None, edge_featurizer=None,
    smiles_column=None, cache_file_path=None, task_names=None, load=False,
    log_every=1000, init_mask=True, n_jobs=1, error_log=None,
)
```

Behavior:

- Input is a pandas `DataFrame`, not a file path.
- `smiles_column` must name the SMILES column.
- If `task_names is None`, every column except `smiles_column` is treated as a label task.
- Invalid SMILES are filtered out; surviving row indices are available as `dataset.valid_ids`.
- Missing labels become `0` in `dataset.labels` and are tracked by `dataset.mask` when `init_mask=True`.
- `dataset[i]` returns `(smiles, graph, labels, mask)` with masks enabled, otherwise `(smiles, graph, labels)`.
- `task_pos_weights(indices)` is for binary classification only and expects a mask.
- `cache_file_path` is used by DGL `save_graphs`/`load_graphs`; change or delete the cache when graph construction or featurization changes.

Recommended minimal custom CSV setup:

```python
df = pd.read_csv('molecules.csv')
dataset = MoleculeCSVDataset(
    df=df,
    smiles_to_graph=smiles_to_bigraph,
    node_featurizer=CanonicalAtomFeaturizer(),
    edge_featurizer=CanonicalBondFeaturizer(),
    smiles_column='smiles',
    task_names=['task1', 'task2'],
    cache_file_path='molecules_dglgraph.bin',
    load=False,
)
```

### `UnlabeledSMILES`

Verified signature:

```python
UnlabeledSMILES(smiles_list, mol_to_graph=None, node_featurizer=None, edge_featurizer=None, log_every=1000)
```

Behavior:

- Use for inference inputs without labels.
- Filters invalid SMILES silently and stores canonical SMILES for valid molecules.
- Default `mol_to_graph` is `MolToBigraph()`.
- `dataset[i]` returns `(canonical_smiles, graph)`.
- If passing a `MolToBigraph`/`ToGraph` object already initialized with featurizers, do not also pass `node_featurizer` or `edge_featurizer` separately; the class asserts against duplicate featurizer injection.

## Built-In Dataset Selection

Most MoleculeNet-style classes share this signature pattern:

```python
DatasetClass(smiles_to_graph=None, node_featurizer=None, edge_featurizer=None,
             load=False, log_every=1000, cache_file_path='./name_dglgraph.bin', n_jobs=1)
```

Use these for standard benchmark data when downloads/cache availability are acceptable:

- Regression-like small molecule property data: `ESOL`, `FreeSolv`, `Lipophilicity`.
- Binary or multi-task classification: `Tox21`, `PCBA`, `MUV`, `HIV`, `BACE`, `BBBP`, `ToxCast`, `SIDER`, `ClinTox`.
- Quantum chemistry: `TencentAlchemyDataset(mode='dev', mol_to_graph=mol_to_complete_graph, ...)` defaults to complete-graph style.
- Protein-ligand binding data: `PDBBind(subset, pdb_version='v2015', load_binding_pocket=True, remove_coreset_from_refinedset=True, sanitize=False, calc_charges=False, remove_hs=False, use_conformation=True, construct_graph_and_featurize=ACNN_graph_construction_and_featurization, zero_padding=True, num_processes=None, local_path=None)`.

Avoid using reaction-specific `USPTOCenter`, `USPTORank`, `WLNCenterDataset`, or `WLNRankDataset` here unless the task is only identifying that it should be routed to `reaction-prediction`.

## Protein-Ligand Complex Prep

DGL-LifeSci exposes two complex graph helpers:

- `ACNN_graph_construction_and_featurization(...)` for ACNN-style protein-ligand features.
- `PN_graph_construction_and_featurization(...)` for PotentialNet-style complex graphs.

Use `load_molecule(molecule_file, sanitize=False, calc_charges=False, remove_hs=False, use_conformation=True)` for `.mol2`, `.sdf`, `.pdbqt`, or `.pdb` molecule files. It returns an RDKit molecule plus coordinates when conformation data is available. Missing/invalid files or unsupported extensions should be diagnosed before constructing complex graphs.

## Splitters

Splitter classes expose static `train_val_test_split` and `k_fold_split` methods:

| Splitter | Use when | Notes |
| --- | --- | --- |
| `ConsecutiveSplitter` | Preserve input order for deterministic debugging. | No shuffling. Fractions default to `0.8/0.1/0.1`. |
| `RandomSplitter` | Random IID baseline. | Pass `random_state` for reproducibility. |
| `MolecularWeightSplitter` | Distribution shift by molecular weight. | Requires `dataset.smiles` or a matching `mols` list. |
| `ScaffoldSplitter` | Scaffold-disjoint train/val/test. | Requires valid RDKit molecules; small datasets may produce uneven splits. |
| `SingleTaskStratifiedSplitter` | Keep one task's label distribution balanced. | Pass `labels` and `task_id`; labels shape is `(N, T)`. |

All train/val/test fractions must sum to 1. Split results are DGL/PyTorch-style subsets that wrap the original dataset.

## Support Utilities

### `Meter`

Verified signature: `Meter(mean=None, std=None)`.

- `update(y_pred, y_true, mask=None)` expects tensors shaped `(B, T)`.
- `mask` is a float tensor shaped `(B, T)` where 1 means the label exists.
- `compute_metric(metric_name, reduction='none')` supports `r2`, `mae`, `rmse`, `roc_auc_score`, and `pr_auc_score`.
- Classification metrics skip tasks with undefined scores, such as all-positive or all-negative labels.

### `EarlyStopping`

Verified signature: `EarlyStopping(mode='higher', patience=10, filename=None, metric=None)`.

- `metric='r2'`, `'roc_auc_score'`, or `'pr_auc_score'` automatically sets higher-is-better.
- `metric='mae'` or `'rmse'` automatically sets lower-is-better.
- `step(score, model)` saves a checkpoint on improvement and returns whether to stop.
- Always set `filename` to a run-owned path; the default filename includes a timestamp and may clutter the working directory.

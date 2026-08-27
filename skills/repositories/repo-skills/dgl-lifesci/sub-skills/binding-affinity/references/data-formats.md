# Binding Data Formats

Binding-affinity workflows in DGL-LifeSci are structure-based. They need RDKit molecules plus atom coordinates for both ligand and protein or binding pocket inputs.

## Supported Molecule Files

`dgllife.utils.load_molecule` supports these extensions:

| Extension | Typical binding use | Notes |
| --- | --- | --- |
| `.sdf` | PDBBind ligand files such as `<pdb_code>_ligand.sdf` | Usually carries 3D coordinates. |
| `.mol2` | Ligand or protein-like molecular file | Supported by RDKit loader. |
| `.pdbqt` | Docking-style ligand file | Loader strips each line to a PDB-like block before RDKit parsing. |
| `.pdb` | PDBBind pocket or full protein files such as `<pdb_code>_pocket.pdb` or `<pdb_code>_protein.pdb` | Standard protein/pocket input. |

Use `scripts/check_complex_inputs.py` to fail fast on missing files or unsupported extensions before calling DGL-LifeSci APIs.

## Coordinates and Conformations

ACNN and PotentialNet graph constructors assert that ligand and protein coordinates are provided. With `load_molecule(..., use_conformation=True)`, coordinates are returned as a NumPy array of shape `(num_atoms, 3)` when RDKit can read a conformer; otherwise coordinates are `None`.

Common coordinate rules:

- SDF, PDB, PDBQT, and MOL2 files should contain 3D atom positions for binding workflows.
- SMILES alone is not enough for these binding models; route SMILES-only graph work to `../molecule-data-prep/SKILL.md` unless the user has a separate conformer-generation plan.
- If `use_conformation=False`, graph construction for ACNN/PotentialNet should not proceed because coordinates will be `None`.
- If `remove_hs=True`, coordinates and molecule atom counts change after hydrogen removal; keep padding and feature expectations consistent.
- If graph construction uses `strip_hydrogens=True`, hydrogens are excluded during graph construction even when molecule files contain them.

## PDBBind Local Path Layout

`PDBBind(local_path=...)` expects a PDBBind-like root directory, not an arbitrary pair of files. For local customized data, use the v2015-style layout unless the user intentionally has v2007-format index files.

A usable local root should contain:

- An index/label file whose name includes the selected subset and `data`, such as a core-data or refined-data file.
- One subdirectory per PDB code listed in the index file.
- Ligand files named `<pdb_code>_ligand.sdf`.
- Protein files named `<pdb_code>_pocket.pdb` when `load_binding_pocket=True`, or `<pdb_code>_protein.pdb` when `load_binding_pocket=False`.

Planning example:

```python
from dgllife.data import PDBBind

dataset = PDBBind(
    subset='core',
    pdb_version='v2015',
    local_path='pdbbind_root',
    load_binding_pocket=True,
    sanitize=False,
    calc_charges=False,
    remove_hs=False,
    use_conformation=True,
    num_processes=1,
)
```

When `local_path` is omitted, the dataset can download and extract packaged PDBBind archives. Ask before doing that in an agent workflow.

## Protein Pocket vs Full Protein

`load_binding_pocket=True` uses pocket files, which are smaller and match the binding-affinity example defaults. `load_binding_pocket=False` uses full protein files and can greatly increase atom counts, graph size, and memory use.

Use pocket files when:

- The user has PDBBind-style pocket files.
- The goal is to reproduce DGL-LifeSci example behavior.
- A quick smoke check or low-memory run is needed.

Use full proteins only when:

- The files exist and are named consistently.
- The user wants full-protein context rather than pocket context.
- Resource limits have been considered.

## `load_molecule` Flags

| Flag | Default | Effect | Failure mode to watch |
| --- | --- | --- | --- |
| `sanitize` | `False` | Run RDKit sanitization before returning the molecule. | Sanitization can fail for imperfect protein/ligand files. |
| `calc_charges` | `False` | Compute Gasteiger charges and implicitly require sanitization. | Charge computation can warn or fail for some molecules. |
| `remove_hs` | `False` | Remove hydrogens with RDKit. | Can be slow for large proteins and changes atom/coordinate counts. |
| `use_conformation` | `True` | Return 3D coordinates from the molecule conformer. | Returns `None` coordinates when the file lacks a conformer. |

For binding graph construction, keep `use_conformation=True` and treat missing coordinates as a blocking input problem.

## Binding Example Config Surface

The binding example combines command-line choices with Python configuration dictionaries. Translate these keys into the user's own project code rather than depending on the original runner.

General keys:

- `model`: `ACNN` or `PotentialNet`.
- `dataset`: one of the PDBBind subset/split names, such as `PDBBind_core_pocket_random` or `PDBBind_refined_pocket_scaffold`.
- `version`: `v2015` by default; `v2007` for agglomerative sequence/structure split usage.
- `pdb_path`: local PDBBind root for customized data.
- `subset`: `core` or `refined`.
- `load_binding_pocket`: usually `True`.
- `remove_coreset_from_refinedset`: usually `True` for refined-to-core evaluation.
- `split`: `random`, `scaffold`, `stratified`, `temporal`, `sequence`, or `structure` with version constraints.
- `frac_train`, `frac_val`, `frac_test`, `random_seed`, `batch_size`, `shuffle`, `num_workers`, `num_epochs`, `lr`, `wd`, and `metrics`.

ACNN-specific keys:

- `hidden_sizes`.
- `weight_init_stddevs`, with one more value than `hidden_sizes`.
- `dropouts`, matching hidden layers.
- `atomic_numbers_considered`, used as `features_to_use`.
- `radial`, a three-list radial filter specification.

PotentialNet-specific keys:

- `distance_bins`, used for spatial edge types.
- `f_in`, `f_bond`, `f_spatial`, and `f_gather`.
- `n_bond_conv_steps` and `n_spatial_conv_steps`.
- `n_rows_fc`.
- `dropouts`, three stage dropout values.
- `n_etypes`, computed as `len(distance_bins) + 5` when instantiating the model.

## Model Input Schemas

ACNN expects one graph:

```python
prediction = model(acnn_graph)
```

PotentialNet expects two graphs:

```python
bigraph, knn_graph = graph_tuple
prediction = model(bigraph, knn_graph)
```

A collate function for mixed binding data should branch on whether dataset graphs are tuples. Batch ACNN graphs with `dgl.batch(graphs)`. Batch PotentialNet graphs as separate batched bigraph and knn graph objects, then pass them as a tuple.

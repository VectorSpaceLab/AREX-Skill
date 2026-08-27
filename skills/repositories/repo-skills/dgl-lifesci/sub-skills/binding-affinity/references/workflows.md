# Binding Affinity Workflows

This reference distills DGL-LifeSci's binding-affinity APIs and examples into self-contained planning guidance. The full example runner is reference-only because it can download PDBBind, load thousands of protein-ligand complexes, and run long training loops.

## Verified API Contracts

| Object | Import | Signature or input contract | Use |
| --- | --- | --- | --- |
| `PDBBind` | `from dgllife.data import PDBBind` | `(subset, pdb_version='v2015', load_binding_pocket=True, remove_coreset_from_refinedset=True, sanitize=False, calc_charges=False, remove_hs=False, use_conformation=True, construct_graph_and_featurize=ACNN_graph_construction_and_featurization, zero_padding=True, num_processes=None, local_path=None)` | Load PDBBind labels, molecules, coordinates, and preconstructed graphs. |
| `load_molecule` | `from dgllife.utils import load_molecule` | `(molecule_file, sanitize=False, calc_charges=False, remove_hs=False, use_conformation=True)` | Load `.mol2`, `.sdf`, `.pdbqt`, or `.pdb` files into RDKit molecule plus optional coordinates. |
| `ACNN_graph_construction_and_featurization` | `from dgllife.utils import ACNN_graph_construction_and_featurization` | `(ligand_mol, protein_mol, ligand_coordinates, protein_coordinates, max_num_ligand_atoms=None, max_num_protein_atoms=None, neighbor_cutoff=12.0, max_num_neighbors=12, strip_hydrogens=False)` | Return one DGL heterograph for ACNN. |
| `PN_graph_construction_and_featurization` | `from dgllife.utils import PN_graph_construction_and_featurization` | `(ligand_mol, protein_mol, ligand_coordinates, protein_coordinates, max_num_ligand_atoms=None, max_num_protein_atoms=None, max_num_neighbors=4, distance_bins=[1.5, 2.5, 3.5, 4.5], strip_hydrogens=False)` | Return `(complex_bigraph, complex_knn_graph)` for PotentialNet. |
| `ACNN` | `from dgllife.model import ACNN` | `(hidden_sizes=None, weight_init_stddevs=None, dropouts=None, features_to_use=None, radial=None, num_tasks=1)` | Predict binding affinity from an ACNN heterograph or batched heterograph. |
| `PotentialNet` | `from dgllife.model import PotentialNet` | `(f_in, f_bond, f_spatial, f_gather, n_etypes, n_bond_conv_steps, n_spatial_conv_steps, n_rows_fc, dropouts)` | Predict binding affinity from PotentialNet stage-1 and stage-2 graphs. |

The verified package version was `dgllife` 0.3.1 with CPU-capable DGL, PyTorch, RDKit, scikit-learn, NumPy/SciPy, and pandas available.

## Workflow Map

| Need | Use | Primary graph | Model | First safe check |
| --- | --- | --- | --- | --- |
| Local complex smoke check | User protein/pocket and ligand files | none yet | none yet | `scripts/check_complex_inputs.py` |
| PDBBind ACNN benchmark plan | `PDBBind(..., construct_graph_and_featurize=ACNN_graph_construction_and_featurization)` | one DGL heterograph | `ACNN` | instantiate on a tiny local complex or already-present cache |
| PDBBind PotentialNet plan | `PDBBind(..., construct_graph_and_featurize=partial(PN_graph_construction_and_featurization, distance_bins=...))` | `(complex_bigraph, complex_knn_graph)` | `PotentialNet` | inspect node/edge feature fields and `n_etypes` |
| Local custom complex inference prototype | `load_molecule` + graph constructor | ACNN graph or PN graph tuple | matching model | require 3D coordinates and supported extensions |
| Full PDBBind training | Long user-approved run | batched graphs | ACNN/PotentialNet | explicit local path/download approval, small worker count first |

## PDBBind Planning

1. Decide whether the user has local PDBBind-style files or wants a built-in dataset download. If `local_path` is `None`, `PDBBind` can download and extract PDBBind archives; ask before running this in normal workflows.
2. Choose `subset='core'` or `subset='refined'`. The source describes `core` as about 195 complexes and `refined` as about 3706 complexes for the packaged MoleculeNet-style data.
3. Choose `pdb_version='v2015'` for standard current examples. Use `v2007` when the task specifically requires agglomerative `sequence` or `structure` splits.
4. Use `load_binding_pocket=True` for pocket files named like `<pdb_code>_pocket.pdb`; set it to `False` only when full protein files named like `<pdb_code>_protein.pdb` are intentionally available.
5. For refined-set training with core-set testing, keep `remove_coreset_from_refinedset=True` unless the user intentionally wants overlap for a diagnostic run.
6. Set `num_processes` conservatively for debugging. `None` uses available CPUs and can be heavy because molecule loading and graph construction are multiprocessing workloads.

The dataset item contract is:

```python
index, ligand_mol, protein_mol, graph_or_graph_tuple, label = dataset[item]
```

For ACNN, `graph_or_graph_tuple` is one heterograph. For PotentialNet, it is `(complex_bigraph, complex_knn_graph)`.

## Local Complex Preparation

Use local complex checks before building a full dataset object:

1. Confirm ligand and protein/pocket file paths exist and use supported RDKit file extensions.
2. Load the ligand with `load_molecule(..., use_conformation=True)` and require non-`None` coordinates for ACNN and PotentialNet graph construction.
3. Load the protein or pocket with the same conformation expectation before calling graph constructors in custom code.
4. Choose `sanitize`, `calc_charges`, and `remove_hs` intentionally. Defaults are conservative: no sanitize, no charge calculation, keep hydrogens, and require conformation.
5. Keep pocket-vs-full-protein choice explicit; full protein graphs are larger and can change memory use and receptive-field behavior.

A minimal local graph construction skeleton:

```python
from dgllife.utils import load_molecule, ACNN_graph_construction_and_featurization

ligand_mol, ligand_coords = load_molecule('ligand.sdf', remove_hs=True)
protein_mol, protein_coords = load_molecule('pocket.pdb', remove_hs=True)
if any(value is None for value in (ligand_mol, ligand_coords, protein_mol, protein_coords)):
    raise ValueError('Binding graph construction requires molecules and 3D coordinates.')
graph = ACNN_graph_construction_and_featurization(ligand_mol, protein_mol, ligand_coords, protein_coords)
```

Route SMILES-only molecule cleaning or 2D graph featurization to `../molecule-data-prep/SKILL.md`; binding models here require 3D coordinates for protein-ligand geometry.

## ACNN Selection

Choose `ACNN` when the workflow should model ligand, protein, and complex energy terms from distance-based heterographs.

ACNN graph contract:

- Node types: `ligand_atom` and `protein_atom`.
- Edge relations include ligand-only, protein-only, and four complex-direction relations between ligand/protein node types.
- Node data includes `atomic_number` and `mask` for both node types.
- Edge data includes `distance` on ligand, protein, and complex relations.
- Zero padding is supported through `max_num_ligand_atoms` and `max_num_protein_atoms`; masks mark real atoms.

ACNN constructor planning:

- Default `hidden_sizes` are `[32, 32, 16]`.
- `weight_init_stddevs` length must equal `len(hidden_sizes) + 1`.
- `dropouts` length should match `hidden_sizes`.
- `features_to_use` is a tensor/list of atomic numbers to consider; examples use PDBBind-specific atomic number sets.
- `radial` is three lists for interaction cutoffs, RBF means, and RBF scaling.
- Output shape is `(batch_size, num_tasks)`, usually `(B, 1)` for binding affinity.

## PotentialNet Selection

Choose `PotentialNet` when the workflow should use staged covalent and spatial propagation followed by ligand-only feature gathering.

PotentialNet graph contract:

- `PN_graph_construction_and_featurization` returns `complex_bigraph` and `complex_knn_graph`.
- `complex_bigraph.ndata['h']` stores stage-1 atom features.
- `complex_bigraph.edata['e']` stores stage-1 bond edge-type one-hot features.
- `complex_knn_graph.edata['e']` stores distance-bin and covalent edge-type one-hot features.
- Stage 3 gathers only ligand atom features according to batched node counts, so batching order matters.

PotentialNet constructor planning:

- `f_in` must match `complex_bigraph.ndata['h'].shape[1]`; DGL-LifeSci's built-in PN featurizer uses 44 in the example configuration.
- `n_etypes` should be `len(distance_bins) + 5`, where 5 accounts for covalent bond edge types used by stage 1.
- `f_bond` must be at least as large as `f_in` because the implementation zero-pads features to `f_bond` before gated graph convolution.
- `f_spatial` and `f_gather` should be kept compatible; example configurations use both as 48.
- `dropouts` is a list of three floats for the three model stages.
- If custom code exposes `max_num_neighbors`, ensure it is actually passed to `PN_graph_construction_and_featurization`; distance bins alone do not control neighbor count.

## Splits and Evaluation

Supported split concepts from the binding example:

- `random`: split by random indices.
- `scaffold`: split by ligand scaffolds using `dataset.ligand_mols` and no RDKit sanitization in the splitter call.
- `stratified`: split by `dataset.labels` for the single binding task.
- `temporal`: sort by `release_year` and split chronologically.
- `sequence` and `structure`: agglomerative splits supplied for PDBBind v2007 refined data.

Training/evaluation planning notes:

- Normalize labels with training-set mean and standard deviation before MSE loss, then evaluate metrics on original scale through `Meter`.
- Binding examples report `r2` and `mae`; higher is better for `r2`, lower is better for `mae`.
- For a refined-to-core evaluation plan, load refined for train/validation and load core as test with `frac_train=0`, `frac_val=0`, `frac_test=1`.
- Use CPU and `num_workers=0` or `1` for smoke checks before scaling workers or moving to GPU.

## Native Evidence Candidates

Useful native verification candidates for a future verifier are:

- ACNN model shape behavior on one downloaded example complex, if networked fixture download is allowed.
- ACNN complex graph construction node/edge feature assertions, if fixture download is allowed.
- `load_molecule` behavior for `.sdf`, `.mol2`, `.pdbqt`, `.pdb`, missing conformers, and hydrogen removal.

Skip full PDBBind downloads and long training runs unless the user explicitly approves those costs.

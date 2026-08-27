# Molecule Data Formats

Use this reference to decide how to structure user data before passing it into DGL-LifeSci data classes or graph constructors.

## Custom CSV for Supervised Molecule Tasks

`MoleculeCSVDataset` expects a pandas `DataFrame` with:

- One SMILES column, commonly `smiles`.
- One or more task columns containing numeric labels.
- Missing labels represented as blank cells or `NaN` when multitask masks are needed.
- Optional non-task metadata columns only if `task_names` is explicitly provided; otherwise every non-SMILES column becomes a task.

Recommended schema:

```text
smiles,solubility,toxicity
CCO,0.13,0
c1ccccc1,-1.20,1
CCN(CC)CC,,0
```

When creating the dataset:

- Pass `smiles_column='smiles'` or the actual header.
- Pass `task_names=[...]` whenever the CSV contains metadata, identifiers, fold labels, or comments.
- Keep task columns numeric. Convert string categories to numeric labels before calling `MoleculeCSVDataset`.
- Set `init_mask=True` for multitask missing-label handling.
- Use `error_log='invalid_smiles.csv'` if you need a row-level record of invalid molecules.

## TXT or CSV for Inference

Use `UnlabeledSMILES` when labels are not required.

TXT format:

```text
CCO
c1ccccc1
CCN(CC)CC
```

CSV inference format:

```text
smiles
CCO
c1ccccc1
CCN(CC)CC
```

`UnlabeledSMILES` filters invalid SMILES and canonicalizes valid strings. If the output count is smaller than the input count, inspect inputs for invalid rows before aligning predictions back to the original file.

## SMILES Validity Expectations

DGL-LifeSci relies on RDKit parsing for SMILES inputs. A valid row must:

- Be non-empty after trimming whitespace.
- Parse with `rdkit.Chem.MolFromSmiles`.
- Produce the expected atom count after any explicit-hydrogen or canonical-order options.

Invalid SMILES are usually skipped by DGL-LifeSci datasets rather than represented as failed samples. For user-facing workflows, validate first with `../scripts/validate_molecule_inputs.py` so row-level failures are visible.

## Graph Feature Expectations

Common graph/feature contracts:

- Canonical molecular graphs use `smiles_to_bigraph` or `mol_to_bigraph` plus `CanonicalAtomFeaturizer()` and often `CanonicalBondFeaturizer()`.
- Canonical atom features are stored in `g.ndata['h']` with width 74.
- Canonical bond features are stored in `g.edata['e']` when an edge featurizer is supplied.
- Complete graphs connect all atom pairs; use them only for models expecting complete graph inputs.
- Pretraining-style GIN features use `PretrainAtomFeaturizer` and `PretrainBondFeaturizer` fields such as `atomic_number`, `chirality_type`, `bond_type`, and `bond_direction_type`, not canonical `h`/`e` fields.
- AttentiveFP-style models typically expect AttentiveFP atom/bond featurizers and both node and edge features.

## Built-In Dataset Inputs and Caches

MoleculeNet-style dataset classes such as `Tox21`, `ESOL`, `FreeSolv`, `Lipophilicity`, `PCBA`, `MUV`, `HIV`, `BACE`, `BBBP`, `ToxCast`, `SIDER`, and `ClinTox` can download or read benchmark data and cache processed graphs. Use them when the task explicitly targets benchmark datasets and downloads/caches are acceptable.

Cache rules:

- `load=False` rebuilds processed graphs from raw data.
- `load=True` reuses `cache_file_path` when present.
- Do not reuse a cache after changing `smiles_to_graph`, atom featurizer, bond featurizer, explicit hydrogens, self-loops, or virtual node settings.
- Put caches in task-owned output directories, not in shared source or skill directories.

## PDBBind-Style Protein-Ligand Data

`PDBBind` and complex graph helpers expect molecule structure files and 3D conformations rather than simple SMILES-only CSVs. Key expectations:

- Ligand/protein files must be readable by RDKit/OpenBabel-backed loading supported by the installed environment.
- `load_molecule` supports `.mol2`, `.sdf`, `.pdbqt`, and `.pdb` paths and can request sanitization, charge calculation, hydrogen removal, and conformation use.
- ACNN/PotentialNet graph helpers need ligand and protein molecules with coordinates.
- Dataset construction can be expensive and may need local PDBBind data via `local_path`; do not trigger downloads in a tiny input-validation task.

Prepare PDBBind-style inputs only as far as validating file presence, molecule loading, and coordinate availability in this sub-skill. Route model architecture and full binding-affinity training to `../binding-affinity/SKILL.md`.

## Split-Ready Dataset Contract

Splitter utilities work best when a dataset has:

- `__len__` and `__getitem__`.
- `dataset.smiles` for scaffold and molecular-weight splitters.
- Optional precomputed RDKit `mols` list aligned one-to-one with `dataset.smiles`.
- `dataset.labels` shaped `(N, T)` for `SingleTaskStratifiedSplitter`.

For very small datasets, fractions such as `0.8/0.1/0.1` can produce empty validation or test sets after integer truncation. For tiny fixtures, use them only to validate callability, not to judge statistical quality.

## Example Safe Fixture

A small labeled fixture that should pass offline validation:

```text
smiles,task1,task2
CCO,0,1
CO,2,
c1ccccc1,1,0
```

Validate it from this sub-skill directory with:

```bash
python scripts/validate_molecule_inputs.py \
  --input fixture.csv --format csv --smiles-column smiles --tasks task1,task2 \
  --require-labels --graph bigraph
```

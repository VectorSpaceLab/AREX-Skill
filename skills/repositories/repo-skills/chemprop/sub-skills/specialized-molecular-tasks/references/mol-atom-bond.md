# MolAtomBond Targets and Constraints

MolAtomBond workflows train Chemprop models that can predict molecule-level, atom-level, and bond-level targets in one model. Use this reference when a dataset has per-atom or per-bond labels, constrained atom/bond outputs, or extra atom/bond descriptors.

## Target Column Families

Use MolAtomBond-specific target flags instead of ordinary `--target-columns`:

- `--mol-target-columns` for molecule-level target columns.
- `--atom-target-columns` for atom-level target columns.
- `--bond-target-columns` for bond-level target columns.

At least one of molecule, atom, or bond predictors must be present. Molecule targets require a graph aggregation internally; atom and bond targets use learned node and edge embeddings.

```bash
chemprop train \
  -i mab.csv \
  --smiles-columns smiles \
  --mol-target-columns mol_y1 mol_y2 \
  --atom-target-columns atom_y1 atom_y2 \
  --bond-target-columns bond_y1 bond_y2 \
  --weight-column weight \
  --keep-h \
  --reorder-atoms \
  --save-dir mab_model
```

## Atom Target Cell Format

Each atom target cell is parsed as a Python/JSON-like list. For one atom target column, each row has one list with one value per atom:

```csv
smiles,atom_charge
[C:1][N:2],"[0.1, -0.1]"
[N:2][C:1],"[0.1, -0.1]"
```

Use `--reorder-atoms` when mapped SMILES atom order differs from the desired atom-map order. Without `--reorder-atoms`, atom target values follow the RDKit atom order from the input SMILES. With `--reorder-atoms`, mapped atoms are reordered by atom map number. This does not reorder bonds.

## Bond Target Cell Format

Bond targets can be given as a list with one value per bond in input bond order:

```csv
smiles,bond_order
CC#N,"[1, 3]"
```

Bond targets can also be provided as a list of lists representing an `n_atoms x n_atoms` matrix. The parser converts each matrix into bond-order values by looking up the begin and end atom indices for each RDKit bond:

```csv
smiles,bond_y
N#CC=N,"[[0, 3, 0, 0], [3, 0, 1, 0], [0, 1, 0, 2], [0, 0, 2, 0]]"
```

Predicted bond values are still returned as a list following Chemprop's bond order, not as the original matrix.

## Bounded Atom/Bond Targets

Bounded tasks can use strings containing `<` or `>` inside atom or bond target lists. The parser strips the bound marker into numeric values and creates less-than / greater-than masks. For bounded bond targets, use list-form bond targets rather than matrix-form targets because bounded list-of-list bond parsing is not supported.

Example cell values:

```csv
smiles,atom_y,bond_y
CCO,"[\"<0.2\", \"0.4\", \">0.8\"]","[\"1.0\", \">1.5\"]"
```

## Constrained Prediction

Use constraints when atom or bond properties must sum to a molecule-level quantity, such as atomic partial charges summing to molecular charge.

Input target CSV:

```csv
smiles,atom_charge,bond_energy
[C:1][O:2],"[0.2, -0.2]","[12.3]"
```

Constraint CSV, same row order as the input CSV and no SMILES column:

```csv
total_charge,total_bond_energy
0.0,12.3
```

Training command:

```bash
chemprop train \
  -i mab.csv \
  --smiles-columns smiles \
  --atom-target-columns atom_charge \
  --bond-target-columns bond_energy \
  --constraints-path constraints.csv \
  --constraints-to-targets atom_charge bond_energy \
  --reorder-atoms \
  --save-dir constrained_mab_model
```

`--constraints-to-targets` entries are the target column names corresponding to the constraints CSV columns, in order. Every name should be one of the columns passed to `--atom-target-columns` or `--bond-target-columns`. Missing constraints for a target are represented internally as `nan`; do not invent placeholder target names.

## Extra Features and Descriptors

MolAtomBond supports the same broad extra input families as molecule models, plus bond descriptors:

- `--descriptors-path` for datapoint-level descriptors concatenated after message passing.
- `--descriptors-columns` for descriptor columns in the CSV.
- `--molecule-featurizers morgan_binary|morgan_count|rdkit_2d|v1_rdkit_2d|v1_rdkit_2d_normalized|charge` for generated molecule descriptors.
- `--atom-features-path` for atom features before message passing.
- `--atom-descriptors-path` for atom descriptors after message passing.
- `--bond-features-path` for bond features before message passing.
- `--bond-descriptors-path` for bond descriptors after message passing.
- `--no-*-scaling` flags when pre-normalized feature spaces should not be scaled.

For single-component MolAtomBond commands, a bare feature path is interpreted as component `0`. For indexed syntax, pass `index path` pairs, but MolAtomBond itself is not a multicomponent model.

## Prediction Pattern

Prediction requires the model path and the same specialized input flags needed to parse the data. Include descriptor and feature paths when the model was trained with them.

```bash
chemprop predict \
  -i mab_to_score.csv \
  --smiles-columns smiles \
  --model-path constrained_mab_model/model_0/best.pt \
  --atom-descriptors-path atom_descs.npz \
  --bond-descriptors-path bond_descs.npz \
  -o mab_predictions.csv
```

## Python API Orientation

The CLI builds a `MolAtomBondMPNN` with one shared message-passing block and up to three predictors: molecule, atom, and bond. Bond predictor outputs are averaged across the two directed edge representations. Optional atom and bond constrainers adjust predictions to satisfy per-molecule constraints.

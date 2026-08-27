# Three-D Graph Data Formats

## QM93D

- Each sample is a PyG `Data` object with `pos`, `z`, `y`, and target columns such as `mu`, `alpha`, `homo`, `lumo`, `gap`, `r2`, `zpve`, `U0`, `U`, `H`, `G`, and `Cv`.
- `get_idx_split(data_size, train_size, valid_size, seed)` returns `train`, `valid`, and `test` index tensors.

## MD17

- Each sample stores `pos`, `z`, `y`, and `force`.
- The dataset constructor name selects one molecule archive such as `aspirin` or `benzene_old`.

## ECdataset and FOLDdataset

- Inputs are protein graph hdf5 files organized by split text files and protein/function mappings.
- `Data` objects include residue/node features and coordinate embeddings for backbone and side-chain torsion features.
- These datasets are only useful when the expected hdf5, split, and mapping files are already prepared locally.

## QM93DGEN

`QM93DGEN.get(idx)` returns a dictionary with keys:

- `atom_type`
- `position`
- `batch`
- `focus`
- `c1_focus`
- `c2_c1_focus`
- `new_atom_type`
- `new_dist`
- `new_angle`
- `new_torsion`
- `cannot_focus`

Use `collate_fn` to batch these dictionaries into the format expected by G-SphereNet.

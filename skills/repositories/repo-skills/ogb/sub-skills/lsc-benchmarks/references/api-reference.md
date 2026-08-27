# LSC API reference

## Public names

- `PCQM4MDataset(root='dataset', smiles2graph=..., only_smiles=False)`
- `PCQM4MEvaluator()`
- `PCQM4Mv2Dataset(root='dataset', smiles2graph=..., only_smiles=False)`
- `PCQM4Mv2Evaluator()`
- `MAG240MDataset(root='dataset')`
- `MAG240MEvaluator()`
- `WikiKG90MDataset(root='dataset')`
- `WikiKG90MEvaluator()`
- `WikiKG90Mv2Dataset(root='dataset')`
- `WikiKG90Mv2Evaluator()`

## PCQM4M / PCQM4Mv2 notes

- `__getitem__` returns either a SMILES string or a graph/label pair depending
  on `only_smiles`.
- `get_idx_split()` returns the official split dictionary.
- The evaluators expect 1-D arrays for MAE.
- Submission helpers write `y_pred_pcqm4m*.npz` files with the official naming
  convention.

## MAG240M notes

- `get_idx_split()` returns the official split dictionary.
- `to_pyg_hetero_data()` builds a PyG `HeteroData` object when PyG is installed.
- `MAG240MEvaluator.eval()` expects 1-D label and prediction arrays.

## WikiKG90M / WikiKG90Mv2 notes

- The dataset classes expose `train_hrt`, `valid_dict`, and `test_dict`-style
  accessors.
- The evaluators consume top-10 ranked predictions.
- Submission helpers write `t_pred_wikikg90m*.npz` files.

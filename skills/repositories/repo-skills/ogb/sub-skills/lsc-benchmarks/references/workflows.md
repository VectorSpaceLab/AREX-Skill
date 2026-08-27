# LSC workflows

## Dataset families

### PCQM4M / PCQM4Mv2

- Molecular regression tasks.
- `PCQM4M` is deprecated; use `PCQM4Mv2` for new work.
- Both datasets can operate in an `only_smiles=True` mode when you want the raw
  molecules without graph conversion.

### MAG240M

- Heterogeneous node classification.
- Supports `to_pyg_hetero_data()` for PyG conversion.
- Uses `split_test()` internally to split the official test set when needed.

### WikiKG90M / WikiKG90Mv2

- Knowledge-graph completion with top-10 ranked predictions.
- `WikiKG90M` is deprecated; use `WikiKG90Mv2` for new work.
- The evaluator checks candidate arrays rather than ordinary class labels.

## Common loader pattern

```python
from ogb.lsc import PCQM4Mv2Dataset, PCQM4Mv2Evaluator

dataset = PCQM4Mv2Dataset(root="dataset", only_smiles=True)
split_idx = dataset.get_idx_split()
```

The dataset classes often download large archives on first use. Expect prompts
before large downloads and plan for significant disk usage.

## Evaluator patterns

- `PCQM4MEvaluator` / `PCQM4Mv2Evaluator` -> MAE.
- `MAG240MEvaluator` -> accuracy.
- `WikiKG90MEvaluator` / `WikiKG90Mv2Evaluator` -> MRR.

## When to use the smoke helper

If you only need to verify the evaluator API or the shape checks, the bundled
smoke script is usually enough and avoids any dataset download.

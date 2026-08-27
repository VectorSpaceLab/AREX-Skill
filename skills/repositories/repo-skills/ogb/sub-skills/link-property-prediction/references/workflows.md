# Link property workflows

## Choose the right dataset

Use this workflow for `ogbl-*` tasks.
The official families are:

- `ogbl-ppa`
- `ogbl-collab`
- `ogbl-citation2`
- `ogbl-wikikg2`
- `ogbl-ddi`
- `ogbl-biokg`
- `ogbl-vessel`

## Common loader pattern

```python
from ogb.linkproppred import LinkPropPredDataset, Evaluator

dataset = LinkPropPredDataset(name="ogbl-collab")
split_edge = dataset.get_edge_split()
graph = dataset[0]
```

The PyG and DGL wrappers follow the same dataset name but require the matching
backend packages to be installed.

## Evaluator patterns

- `hits@K` datasets consume positive and negative score vectors.
- `mrr` datasets also consume positive and negative score vectors, but the
  shapes and ranking logic are different.
- `rocauc` for `ogbl-vessel` still uses positive and negative edge scores.

## Common decisions

- Use the library-agnostic loader when you only need the official graph and
  edge split.
- Use the PyG or DGL wrappers only when the backend package is installed and
  the task needs those data structures.
- Check the split dictionary keys before assuming every dataset uses the same
  nested structure.

## KG-completion caveats

- `ogbl-biokg` and `ogbl-wikikg2` are knowledge-graph completion workflows.
- Their evaluator inputs are ranking-oriented, not ordinary binary labels.
- Top-k duplication errors are usually a sign that the candidate list was built
  incorrectly.

## Common mistakes

- Mixing up `y_pred_pos` and `y_pred_neg`.
- Giving the evaluator a matrix when it expects a vector, or vice versa.
- Forgetting that `hits@K` and `mrr` are not interchangeable.

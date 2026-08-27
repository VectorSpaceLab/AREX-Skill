# Link property troubleshooting

## Shape mismatches

- `y_pred_pos` and `y_pred_neg` must have the shapes described by the evaluator.
- `mrr` uses a 2-D negative matrix; `hits@K` uses a 1-D negative vector.
- If the evaluator complains about dimension count, check whether you passed a
  matrix to a vector-based task.

## Duplicate candidates

Top-10 duplication errors for KG completion usually mean the candidate list was
built incorrectly. Remove duplicates before calling the evaluator or the
submission helper.

## Metric confusion

- `hits@K` is not the same as `mrr`.
- `rocauc` only applies to the datasets that document it.
- Do not assume a node-classification evaluator will accept link scores.

## Wrapper imports

If PyG or DGL imports fail, the core OGB link loader still works through the
library-agnostic path.

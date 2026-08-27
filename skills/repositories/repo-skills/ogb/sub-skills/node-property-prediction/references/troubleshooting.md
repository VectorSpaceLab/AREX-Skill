# Node property troubleshooting

## Heterogeneous label handling

If `ogbn-mag` or another hetero dataset returns dicts, do not try to coerce the
labels into a flat tensor. Keep the dict structure keyed by node type.

## Split loading issues

- A missing `split_dict.pt` is not necessarily an error; the loader can fall
  back to the CSV split files.
- If the dataset says it has been updated, the cached release marker is stale.

## Shape errors

- The evaluator expects matching 2-D `y_true` and `y_pred` arrays.
- Accuracy and ROC-AUC are not interchangeable.

## Large dataset notes

- `ogbn-papers100M` is the large binary/raw workflow; it is not a small smoke
  dataset.
- Do not treat the one-graph node datasets as batching examples.

## Wrapper imports

If PyG or DGL imports fail, the core OGB node loader still works through the
library-agnostic path.

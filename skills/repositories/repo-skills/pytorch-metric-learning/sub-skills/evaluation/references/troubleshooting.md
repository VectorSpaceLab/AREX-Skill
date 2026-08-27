# Evaluation and inference troubleshooting

## Common symptoms and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `faiss` import error | The faiss dependency is missing | Install the `with-hooks-cpu` extra or the documented faiss package. |
| Accuracy metrics look wrong | `k`, `ref_includes_query`, or the label comparison function is misconfigured | Check the metric definition and the reference/query split relationship. |
| `mean_average_precision_at_r` or `r_precision` seems inconsistent | `k` is too small for the label distribution | Use `k=None`, `k="max_bin_count"`, or a large enough `k`. |
| Custom labels are treated as distinct when they should match | A custom `label_comparison_fn` is missing or wrong | Supply a comparison function that matches the label schema. |
| `Custom label comparison` plus clustering metrics fail | `NMI` / `AMI` do not mix with the chosen comparison function | Exclude clustering metrics or use equality-style labels. |
| `InferenceModel` says the index is uninitialized | `train_knn` was never called and no preloaded index was provided | Train the k-NN index or load a saved one before querying. |
| GPU k-NN search warns about `k` being too large | GPU-backed faiss has a max-k limit | Use CPU search or a smaller `k`. |
| Evaluation works on the query split but not on a ref split | The split names or `splits_to_eval` structure are wrong | Confirm the dataset dict keys and the query/reference mapping. |

## Recovery checklist

1. Confirm the query and reference embeddings have the same feature dimension.
2. Confirm labels have the expected rank and hierarchy depth.
3. If you are using a custom label comparison function, test it on a tiny pair of label tensors first.
4. If the metric needs retrieval neighbors, make sure `k` and the reference population are large enough.
5. If you are using inference, confirm that the index was trained or loaded before searching.

## When to read the script

Run `scripts/smoke_evaluation.py` to confirm a tiny `AccuracyCalculator` + tester + inference path without touching a real dataset.

# Tabular workflows

## 1. Pick the algorithm family

Use the target and the shape of the task to choose a route:

- Numeric target and supervised prediction: `regression_query_ann(..., save_model=False)` for smoke/inspection runs, or `neural_network_query(...)`.
- Categorical target and supervised prediction: `classification_query_ann(...)`, `svm_query(...)`, `nearest_neighbor_query(...)`, `decision_tree_query(...)`, `xgboost_query(...)`, or `neural_network_query(...)`.
- No target and unlabeled structure: `kmeans_clustering_query(...)`.
- Catalog-style text columns: `content_recommender_query(...)` followed by `recommend(...)`.

## 2. Prepare the instruction

Libra finds the target column by comparing words in the instruction with dataset column names. Keep the wording close to the actual column:

```python
c.decision_tree_query("predict ocean proximity")
```

If the instruction is too vague, refine it toward the exact column name. For text workflows, pass `label_column` explicitly when the default column name is not present.

## 3. Use the right preprocessing knobs

- `preprocess=True` is the default and usually the right starting point.
- Use `drop=[...]` for identifiers or leakage columns.
- Use `text=[...]` when a tabular dataset contains text columns that should be embedded.
- Use `ca_threshold` only when the tabular feature space has many categorical values.
- Use `test_size`/`random_state` to stabilize comparisons.

## 4. Inspect the run

After a query, inspect the stored dictionary:

```python
c.decision_tree_query("predict ocean proximity")
print(c.latest_model)
print(c.info())
print(c.model().keys())
print(c.accuracy())
print(c.losses())
print(c.target())
```

Use `analyze()` when you want Libra to add metrics and plots that were not created during the initial run.

## 5. Tune a trained model

Once a supported ANN or CNN is in `client.models`, call `tune()` on that model key or leave `model_to_tune` unset to use `latest_model`.

```python
c.classification_query_ann("predict ocean proximity", epochs=3)
c.tune(model_to_tune="classification_ANN", max_trials=2, epochs=2)
```

## 6. Build recommendations

For recommender workflows, choose a stable indexer column and the text-like feature columns to fold into the similarity soup:

```python
c.content_recommender_query(feature_names=["genre", "actors", "plot"], indexer="title")
print(c.recommend("Coco")["recommendations"])
```

## 7. Launch the dashboard last

`dashboard()` is best used after you have confirmed the data file path and are happy with any generated side effects. It is a launch action, not a modeling action.

## Synthetic smoke pattern

The bundled `scripts/smoke_tabular_decision_tree.py` is the preferred safe proof that the root import, target matching, and decision-tree route still work on a tiny CSV.

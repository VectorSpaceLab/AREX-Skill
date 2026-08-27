# Data and feature troubleshooting

Use this checklist before changing model code. Most LightFM data failures come from mismatched mappings, incomplete feature rows, or changing feature-column counts after training.

## Common failures

| Symptom or message | Likely cause | Safe fix |
| --- | --- | --- |
| `You must call fit first...`, or an empty `(0, 0)` matrix appears | The `Dataset` has no fitted user/item mappings. Some empty-build paths can return empty matrices instead of failing early. | Always call `fit(users, items, ...)` before building interactions or features, even for tiny smoke tests. |
| `User id ... not in user id mapping` | An interaction or user-feature record contains a user id that was not supplied to `fit`/`fit_partial`. | Rebuild the id collection from the same data source, include feature-only cold-start users if needed, then call `fit` again before building matrices. |
| `Item id ... not in item id mapping` | An interaction or item-feature record contains an item id that was not fitted. | Include all interaction items and all candidate/metadata-only items in the fitted item id set. |
| `Feature ... not in feature mapping. Call fit first.` | A feature record contains a label that was not supplied via `user_features` or `item_features` during `fit`/`fit_partial`. | Build a complete feature vocabulary first. For production streams, reserve fallback labels such as `tag:unknown` rather than inventing unseen labels at prediction time. |
| `Expected tuples of (user_id, features)` or `(item_id, features)` | A feature datum is not a 2-tuple/list. | Use `(id, [features])` or `(id, {feature: weight})`; in JSONL, use `[id, features]` or `{user_id/item_id, features}`. |
| Feature name appears to be split into characters | A single string was passed where a list of feature strings was intended. Python iterates strings character by character. | Wrap single features in a list: `['genre:drama']`. |
| `Cannot normalize feature matrix: some rows have zero norm` | `normalize=True` and at least one fitted user/item row has no stored identity or metadata features. This often happens when identity features are disabled and metadata is missing for some rows. | Provide at least one nonzero feature for every row, re-enable identity features for that side, or call `build_user_features(..., normalize=False)` / `build_item_features(..., normalize=False)` only after confirming zero rows are intentional. |
| Feature rows have sums different from expected | `normalize=True` L1-normalizes rows after identity features and metadata features are inserted. | Use `normalize=False` when absolute feature weights must be preserved; otherwise design weights with post-normalization semantics in mind. |
| Duplicate interaction pairs inflate counts or weights | `build_interactions` stores duplicate COO entries. | Aggregate duplicates before building, or explicitly call sparse duplicate coalescing and document whether weights should be summed, clipped, or averaged. |
| `Number of user feature rows does not equal the number of users` or `Number of item feature rows does not equal the number of items` | A feature matrix row count is smaller than the interaction shape required by the model call. | Use one `Dataset` mapping for interactions and features. Ensure `user_features.shape[0] >= interactions.shape[0]` and `item_features.shape[0] >= interactions.shape[1]`. |
| `Incorrect number of features in user_features` / `item_features`, or more feature columns than estimated embeddings | The feature vocabulary changed after the model allocated embeddings. | Compare `dataset.model_dimensions()` with the feature matrix columns used when the model was trained. Retrain or intentionally resize/reinitialize through [model-training](../../model-training/SKILL.md); do not silently append feature columns to an existing model. |
| Predictions or evaluation look wrong after using metadata | Feature matrices were passed to `fit` but omitted from `predict`, `predict_rank`, or evaluation. | Pass compatible `user_features` and/or `item_features` to every model operation that used them during training. Evaluation details route to [evaluation-splitting](../../evaluation-splitting/SKILL.md). |
| Built-in fetcher raises `Dataset missing.` | `download_if_missing=False` and the cache/data home does not contain the expected archive. | Prepopulate the cache or provide a `data_home` with the dataset file, then retry. In no-network workflows, prefer tiny local fixtures and the bundled [JSONL helper](../scripts/build_lightfm_dataset.py). |
| Built-in MovieLens fetcher reports a corrupted download | A cached archive is incomplete or invalid. | Remove the bad cached file and retry only when network access is allowed; otherwise point `data_home` at a known-good local cache. |
| StackExchange fetch uses excessive memory or time | StackOverflow is extremely large; even CrossValidated is much larger than a unit test fixture. | Use a synthetic JSONL fixture for quick checks, or use a smaller cached dataset and avoid network downloads in bounded runs. |

## Identity-feature tradeoffs

| Choice | Helps | Hurts / watch for |
| --- | --- | --- |
| Keep identity features enabled (default) | Learns per-user/per-item embeddings and usually improves warm-start collaborative filtering. Feature matrices are complete even without metadata records. | Adds many feature columns; item/user cold-start does not generalize through unseen identity columns. Metadata labels can collide with raw ids unless namespaced. |
| Disable item identity features | Lets item representations come from item metadata only, useful for item cold-start. Adding new item rows with known feature columns can keep model dimensions stable. | Every item row needs metadata when building normalized features. Pure collaborative signal may underfit if metadata is too coarse. |
| Disable user identity features | Lets user representations come from user metadata only, useful for user cold-start. | Every user row needs metadata when building normalized features. Sparse or weak metadata can underfit. |
| Use identity plus metadata | Combines warm-start memorization with shared feature signals. | Cold-start items/users still need a strategy for missing identity embeddings; feature-column counts become larger and must stay consistent across model calls. |

## Quick validation checklist

Before passing matrices to training or evaluation:

1. `interactions.shape == weights.shape`.
2. `user_features is None or user_features.shape[0] >= interactions.shape[0]`.
3. `item_features is None or item_features.shape[0] >= interactions.shape[1]`.
4. `dataset.model_dimensions()` matches the feature-column counts expected by the model.
5. `mapping()` can invert every row/column id needed by recommendation output.
6. No new feature names are introduced after model training unless a retraining/resizing workflow is planned.

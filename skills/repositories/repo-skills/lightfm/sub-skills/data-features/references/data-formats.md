# Data formats and conversion recipes

Use this reference to normalize local records into the shapes documented in [API reference](api-reference.md). The bundled [JSONL helper](../scripts/build_lightfm_dataset.py) follows these same conventions and never downloads data.

## Interaction records

LightFM `Dataset.build_interactions` accepts Python tuples or lists:

```python
('user-1', 'item-9')        # unit weight
('user-1', 'item-9', 2.5)   # explicit weight
```

For JSONL conversion, use one record per line in either array or object form:

```jsonl
["user-1", "item-9"]
["user-1", "item-10", 2.5]
{"user_id": "user-2", "item_id": "item-9", "weight": 1.0}
```

Guidelines:

- Collect all users and items before calling `fit`, including feature-only cold-start candidates that need rows in feature matrices.
- Use numeric weights only. Omitted weights become `1.0`.
- Decide duplicate semantics explicitly. `Dataset` stores duplicate pairs as duplicate COO entries; aggregate first if one row/column pair should have one final weight.
- For implicit-feedback workflows, positive events usually become nonzero entries. Loss, weighting, and negative/zero semantics belong in [model-training](../../model-training/SKILL.md).

## User and item feature records

LightFM feature records are `(entity_id, features)` where `features` is either a list of feature names or a dict of feature-name weights:

```python
('book-1', ['author:Octavia Butler', 'year:1993'])
('book-2', {'author:Ursula Le Guin': 1.0, 'genre:science-fiction': 2.0})
```

Equivalent JSONL forms accepted by the bundled helper:

```jsonl
{"item_id": "book-1", "features": ["author:Octavia Butler", "year:1993"]}
{"item_id": "book-2", "features": {"author:Ursula Le Guin": 1.0, "genre:science-fiction": 2.0}}
["book-3", ["author:N. K. Jemisin", "genre:fantasy"]]
```

For user features, use `user_id` instead of `item_id` in object records.

Guidelines:

- Wrap single features in a list: `['genre:fantasy']`, not `'genre:fantasy'`.
- Namespace features (`genre:`, `tag:`, `country:`, `author:`) so metadata labels do not collide with raw user/item ids used for identity features.
- List features all get weight `1.0`; dict features preserve supplied weights.
- With `normalize=True` (the default), the built matrix is L1-normalized per row after identity and metadata features are inserted.
- If identity features are disabled for a side, every row on that side needs at least one known feature when normalization remains enabled.

## Built-in dataset dictionaries

### MovieLens

`fetch_movielens(...)` returns a dictionary with:

```python
{
    'train': train_interactions,          # COO, users x movies
    'test': test_interactions,            # COO, same shape
    'item_features': item_feature_matrix, # CSR, movies x item-feature columns
    'item_feature_labels': labels,        # labels for item_feature columns
    'item_labels': movie_titles,          # labels for item ids / columns
}
```

Common feature modes:

- `indicator_features=True, genre_features=False`: item identity features only.
- `indicator_features=False, genre_features=True`: genre metadata only; useful when testing metadata-only behavior.
- `indicator_features=True, genre_features=True`: identity plus genre metadata.

Use `min_rating` to drop ratings below a threshold. The stored values are ratings that pass the threshold, not a mandatory binarization step.

### StackExchange

`fetch_stackexchange(...)` returns a dictionary with:

```python
{
    'train': train_interactions,          # COO, users x questions
    'test': test_interactions,            # COO, same shape
    'item_features': item_feature_matrix, # CSR, questions x item-feature columns
    'item_feature_labels': labels,        # question ids and/or tag labels
}
```

Common feature modes:

- `indicator_features=True, tag_features=False`: question identity features only.
- `indicator_features=False, tag_features=True`: tag metadata only; preferred for item cold-start demonstrations.
- `indicator_features=True, tag_features=True`: identity plus tags.

The split is chronological, so later questions/interactions are in the test set. This makes tag-only item features useful for testing whether a model can score new items from metadata.

## Custom no-network conversion recipe

This recipe adapts the useful local-parsing pattern from the repository examples while removing all download and checkout assumptions.

1. Load local records from CSV, JSON, JSONL, a database export, or in-memory lists.
2. Materialize or reopen iterators when they must be traversed more than once. Generators consumed by `fit` cannot be reused by `build_interactions` unless recreated.
3. Collect ids and feature vocabularies:

```python
users = sorted({row['user_id'] for row in interactions})
items = sorted({row['item_id'] for row in interactions} | {row['item_id'] for row in item_metadata})
item_feature_names = sorted({f"author:{row['author']}" for row in item_metadata})
```

4. Fit the dataset:

```python
from lightfm.data import Dataset

dataset = Dataset(user_identity_features=True, item_identity_features=True)
dataset.fit(users, items, item_features=item_feature_names)
```

5. Build matrices:

```python
interactions_matrix, weights_matrix = dataset.build_interactions(
    (row['user_id'], row['item_id'], row.get('weight', 1.0))
    for row in interactions
)

item_features = dataset.build_item_features(
    (row['item_id'], [f"author:{row['author']}"])
    for row in item_metadata
)
```

6. Save sparse matrices with `scipy.sparse.save_npz` and mappings from `dataset.mapping()` with a JSON-safe structure such as lists of `(id, index)` pairs.

The bundled helper implements these steps for tiny JSONL files:

```bash
python scripts/build_lightfm_dataset.py --demo
python scripts/build_lightfm_dataset.py --interactions interactions.jsonl --item-features items.jsonl --output-dir matrices
```

Run the commands from this sub-skill directory or adjust the script path accordingly.

## Cold-start hybrid feature strategy

For item cold-start:

1. Disable item identity features when the goal is to score items from metadata only:

```python
dataset = Dataset(item_identity_features=False)
```

2. Fit all stable item feature names before training. New item rows may be added later only if they use already-known feature columns.
3. Include cold-start candidate item ids in `fit` or `fit_partial` so their rows exist in `item_features`.
4. Build an `item_features` matrix that contains both training items and candidate items.
5. Train and score with the same feature-column vocabulary. Pass `item_features` to `fit`, `predict`, `predict_rank`, and evaluation.

Important limits:

- Adding new item ids with `item_identity_features=False` adds rows but not new feature columns; this can be compatible with an already-trained model when the feature vocabulary is unchanged.
- Adding new feature names after model training changes `model_dimensions()` and requires retraining or a model-side resize/reinitialization workflow; route that decision to [model-training](../../model-training/SKILL.md).
- Unknown metadata at prediction time needs a planned fallback feature such as `tag:unknown`, or the model must be retrained with an expanded vocabulary.

For user cold-start, apply the same pattern with `user_identity_features=False`, stable user metadata feature names, and `user_features` passed consistently to every model operation.

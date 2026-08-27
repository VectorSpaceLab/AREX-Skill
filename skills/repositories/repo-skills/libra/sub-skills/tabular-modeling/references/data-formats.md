# Tabular data formats

## Accepted file types
`DataReader` accepts:
- `.csv`
- `.xlsx`
- `.json`

It returns a pandas DataFrame and may trim the data on CPU-only machines to keep runs lightweight.

## Column assumptions

### Supervised tabular tasks
- The instruction should point to the target column.
- If the target column name is not obvious from the instruction, use wording that is closer to the actual column name.
- Use `drop=[...]` to remove IDs, leakage columns, or image/text helpers that should not be modeled directly.
- Use `text=[...]` when a tabular table contains text-like columns that should pass through the text embedding branch.

### ANN classification
- The target must contain at least two classes.
- The stored dictionary includes the one-hot encoder, class count, loss history, and accuracy history.

### ANN regression
- The target is treated as numeric and scaled with `StandardScaler` before training.

### Clustering
- `kmeans_clustering_query` can work without a target column.
- If the table contains text columns, only include them when you want them to influence clustering.

### Content recommender
- Provide a stable `indexer` column such as `title`.
- Provide feature columns that can be folded into a similarity soup, usually string-like categorical columns.
- The default behavior tries to use categorical columns and excludes obvious `id` fields.

## Practical fixtures
A good tabular fixture is a tiny CSV with:
- one numeric column
- one categorical target column
- one leakage or ID column that should be dropped
- optionally one text column for embedding tests

The bundled smoke script creates exactly that kind of synthetic table.

## Data generation side effects
The tabular workflows do not usually rewrite the source data file, but they can create:
- saved model artifacts
- tuned-model directories
- plot images
- dashboard output or launch state

Use temporary output directories for smoke checks.

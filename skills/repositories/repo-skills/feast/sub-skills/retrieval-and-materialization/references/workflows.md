# Retrieval and Materialization Workflows

## Local historical retrieval

Use this when building a training dataset or batch-scoring table from offline data.

1. Confirm the feature repo has valid definitions and has been applied.
2. Build an entity dataframe with all join keys and an `event_timestamp` column.
3. Include label, target, or request columns in the entity dataframe if they should appear in the output.
4. Select features with a production `FeatureService` or experimental feature refs.
5. Call `get_historical_features(...).to_df()` and assert expected entity, timestamp, label, and feature columns.

```python
from datetime import datetime
import pandas as pd
from feast import FeatureStore

store = FeatureStore(repo_path=".")
entity_df = pd.DataFrame(
    {
        "driver_id": [1001, 1002],
        "event_timestamp": [datetime(2025, 1, 1), datetime(2025, 1, 2)],
        "trip_success": [1, 0],
    }
)

training_df = store.get_historical_features(
    entity_df=entity_df,
    features=["driver_hourly_stats:conv_rate"],
).to_df()

assert {"driver_id", "event_timestamp", "trip_success", "conv_rate"}.issubset(
    training_df.columns
)
```

Point-in-time expectations:

- Feast scans feature rows backward from each entity row timestamp.
- Values outside the feature view TTL are not joined.
- Feature rows after the entity timestamp are excluded to prevent leakage.
- Multiple feature views can join into one dataset when join keys and timestamps line up.

## Online retrieval after materialization

Use this for real-time inference or online batch checks.

```bash
feast apply
feast materialize 2025-01-01T00:00:00 2025-01-02T00:00:00
```

```python
from feast import FeatureStore

store = FeatureStore(repo_path=".")
features = store.get_online_features(
    features=["driver_hourly_stats:conv_rate"],
    entity_rows=[{"driver_id": 1001}],
).to_dict()

print(features)
```

Validation checklist:

- The feature view has `online=True`.
- The offline source contains the join key columns used by the feature view entities.
- The materialization window includes the feature rows expected for retrieval.
- The online store path or service is the same one used by retrieval.
- `full_feature_names=True` changes output names from `conv_rate` to namespaced forms such as `driver_hourly_stats__conv_rate`.

## Incremental materialization

Use full materialization for an initial load and incremental materialization for subsequent refreshes.

```bash
feast materialize 2025-01-01T00:00:00 2025-01-02T00:00:00
feast materialize-incremental 2025-01-03T00:00:00
```

```python
store.materialize(start_date=start, end_date=end)
store.materialize_incremental(end_date=next_end)
```

A common local pattern is to assert online results after each step: after the first command, results should match rows up to the first end date; after the incremental command, results should match rows up to the new end date.

## Push ingestion workflow

Use push ingestion when a stream or application process writes rows into Feast directly.

1. Define a `PushSource` and feature view in the feature-definition layer.
2. Apply the repo.
3. Build a pandas dataframe containing join keys, event timestamp, and feature columns.
4. Call `store.push(push_source_name, df, to=PushMode.ONLINE)`.
5. Retrieve the same entity with `get_online_features`.

```python
from feast.data_source import PushMode

store.push("driver_stats_push_source", push_df, to=PushMode.ONLINE)
actual = store.get_online_features(
    features=["driver_stats:conv_rate"],
    entity_rows=[{"driver_id": 1001}],
).to_dict()
```

If a feature service uses `precompute_online=True`, materialization and push refresh its stored feature vectors for affected entities.

## Saved datasets

Use saved datasets when a historical retrieval result should become a reusable training artifact.

General pattern:

1. Build and validate a historical retrieval job.
2. Save the result using the dataset APIs available in the installed Feast version.
3. List or inspect saved datasets with the CLI.

```bash
feast saved-datasets --help
```

Saved datasets are outputs of retrieval jobs; they are not feature views or data sources. Keep feature-definition changes in `../../feature-definitions/SKILL.md`.

## DQM and monitoring basics

Use `feast validate` and `feast monitor` for quality checks when the repo config and definitions enable validation references, data sources, or monitoring.

```bash
feast validate --help
feast monitor --help
```

Retrieval-focused quality checks:

- Compare historical output row count with the input entity dataframe row count.
- Assert feature columns exist and null rates are acceptable.
- Check timestamp windows and TTL explain any missing values.
- Validate online values after materialization against source rows for a small entity set.
- Record backend credentials, optional extras, or service prerequisites before running cloud-backed checks.

For optional integrations, custom stores, and broader backend selection, route to `../../integrations-and-extensibility/SKILL.md`.

## Tiny local end-to-end case

A future agent can test a minimal local repo without relying on source examples:

1. Create a feature repo with `provider: local`, file offline store, SQLite online store, and a file registry.
2. Define one entity `driver` with join key `driver_id`.
3. Define one file-backed feature view with `driver_id`, `event_timestamp`, and one numeric feature.
4. Apply the repo.
5. Run historical retrieval with two entity rows and assert joined feature columns.
6. Materialize the same time range.
7. Run online retrieval for one materialized entity and assert the feature is non-null.

Use `scripts/local_retrieval_smoke.py --repo-path <repo>` before destructive commands to inspect the local setup and print safe next commands.

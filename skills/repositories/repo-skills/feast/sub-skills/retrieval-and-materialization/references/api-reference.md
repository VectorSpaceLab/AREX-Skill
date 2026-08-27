# Retrieval and Materialization API Reference

## SDK entry points

Instantiate a store against an applied feature repository:

```python
from feast import FeatureStore

store = FeatureStore(repo_path=".")
```

Verified `FeatureStore` signatures for this Feast build:

```python
FeatureStore(repo_path=None, config=None, fs_yaml_file=None)

store.get_historical_features(
    entity_df=None,
    features=[],
    full_feature_names=False,
    start_date=None,
    end_date=None,
)

store.get_online_features(
    features,
    entity_rows,
    full_feature_names=False,
    include_feature_view_version_metadata=False,
)

store.materialize(
    start_date,
    end_date,
    feature_views=None,
    disable_event_timestamp=False,
    full_feature_names=False,
    version=None,
)

store.materialize_incremental(
    end_date,
    feature_views=None,
    full_feature_names=False,
    version=None,
)

store.push(
    push_source_name,
    df,
    allow_registry_cache=True,
    to=PushMode.ONLINE,
    transform_on_write=True,
)
```

## Historical retrieval

Use historical retrieval for training data and offline batch scoring. The returned object is a retrieval job; call an output method such as `.to_df()` when you need local pandas data.

```python
from datetime import datetime
import pandas as pd
from feast import FeatureStore

store = FeatureStore(repo_path=".")
entity_df = pd.DataFrame(
    {
        "driver_id": [1001, 1002],
        "event_timestamp": [
            datetime(2025, 1, 1, 12, 0, 0),
            datetime(2025, 1, 1, 12, 5, 0),
        ],
    }
)

training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "driver_hourly_stats:conv_rate",
        "driver_hourly_stats:acc_rate",
    ],
).to_df()
```

Point-in-time behavior: for each entity row, Feast joins the latest feature value with source event time at or before the row's `event_timestamp`, subject to the feature view TTL. Keep label/target columns in `entity_df`; Feast preserves them in the output.

Entity-less historical retrieval is supported only by selected offline stores such as Postgres, Dask, Spark, and Ray. Do not mix `entity_df` with `start_date`/`end_date` in the same call.

```python
training_df = store.get_historical_features(
    features=["driver_hourly_stats:conv_rate"],
    start_date=datetime(2025, 7, 1),
    end_date=datetime(2025, 7, 2),
).to_df()
```

## Feature selection

Prefer `FeatureService` for production model contracts and feature refs for experiments.

```python
service = store.get_feature_service("driver_activity_v1")
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=service,
).to_df()

online = store.get_online_features(
    features=service,
    entity_rows=[{"driver_id": 1001}],
).to_dict()
```

Feature refs use `<feature_view>[@version]:<feature>`:

```python
features = [
    "driver_hourly_stats:conv_rate",
    "driver_hourly_stats@v2:acc_rate",
    "driver_hourly_stats@latest:avg_daily_trips",
]
```

Version-qualified online reads require registry support and are currently tied to SQLite online-store support in the referenced Feast docs.

## Online retrieval

Online retrieval reads from the online store. It does not scan offline source files on demand, so the online store must be populated through materialization or push ingestion.

```python
response = store.get_online_features(
    features=[
        "driver_hourly_stats:conv_rate",
        "driver_hourly_stats:acc_rate",
    ],
    entity_rows=[{"driver_id": 1001}, {"driver_id": 1002}],
    full_feature_names=False,
)

as_dict = response.to_dict()
as_df = response.to_df()
```

Expected output behavior:

- Entity columns are included with returned feature values.
- Missing online rows can still include requested feature keys, often with null-like values.
- Missing required join keys raise a key error naming required and provided join keys.
- Bad feature view names raise feature-view lookup errors before retrieval.
- `.to_tensor()` is available when tensor dependencies are present; string features may remain Python lists.

## Materialization

Materialization scans offline sources and writes values into the online store.

```python
from datetime import datetime, timezone

store.materialize(
    start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
    end_date=datetime(2025, 1, 2, tzinfo=timezone.utc),
)

store.materialize_incremental(
    end_date=datetime(2025, 1, 3, tzinfo=timezone.utc),
)
```

Limit work to selected feature views when needed:

```python
store.materialize(
    start_date=start,
    end_date=end,
    feature_views=["driver_hourly_stats"],
)
```

CLI equivalents:

```bash
feast materialize 2025-01-01T00:00:00 2025-01-02T00:00:00
feast materialize-incremental 2025-01-03T00:00:00
```

Local E2E behavior verified by Feast tests: file offline sources can be materialized into local online storage, `materialize-incremental` extends the populated range, and online retrieval should reflect the latest materialized end date.

## Push ingestion

Use `push` when a feature view is backed by a push source and rows should be written as they arrive.

```python
import pandas as pd
from feast.data_source import PushMode

push_df = pd.DataFrame(
    {
        "driver_id": [1001],
        "event_timestamp": [pd.Timestamp.utcnow()],
        "conv_rate": [0.42],
    }
)

store.push(
    push_source_name="driver_stats_push_source",
    df=push_df,
    to=PushMode.ONLINE,
)
```

`transform_on_write=True` applies on-write transformations before storing. Push can also refresh precomputed online feature-service vectors when they are enabled.

## CLI commands

These Feast CLI commands are available in this build for this area:

```bash
feast get-historical-features
feast get-online-features
feast materialize
feast materialize-incremental
feast saved-datasets
feast validate
feast monitor
```

Use `feast --help` and `feast <command> --help` to confirm exact command flags for the installed package.

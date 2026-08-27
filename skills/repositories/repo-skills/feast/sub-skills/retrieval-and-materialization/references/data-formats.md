# Retrieval Data Formats

## Entity dataframe for historical retrieval

`get_historical_features` usually receives a pandas dataframe or a supported offline-store query string. The dataframe must contain:

- One column for every required entity join key.
- An `event_timestamp` column used as the point-in-time upper bound.
- Optional label, target, request, or pass-through columns that should remain in the joined output.

```python
entity_df = pd.DataFrame(
    {
        "driver_id": [1001, 1002],
        "event_timestamp": [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-02")],
        "label": [1, 0],
    }
)
```

Timestamp guidance:

- Use timezone-aware timestamps when your sources and backend expect them.
- Keep source event timestamp columns aligned with feature-view source configuration.
- Remember TTL is evaluated relative to each entity row timestamp, not relative to the current clock.

## Entity rows for online retrieval

`get_online_features` receives `entity_rows` as either a list of dictionaries or a mapping of join-key names to value sequences.

```python
rows = [{"driver_id": 1001}, {"driver_id": 1002}]

features = store.get_online_features(
    features=["driver_hourly_stats:conv_rate"],
    entity_rows=rows,
).to_dict()
```

For multi-entity feature views, each row must provide every join key used by requested features.

```python
rows = [{"customer_id": "5", "driver_id": 1}]
```

Feast can coerce some value types during retrieval, but future agents should avoid relying on implicit string/integer conversion when debugging joins.

## Feature refs

Feature refs identify feature values as strings:

```text
<feature_view>:<feature>
<feature_view>@<version>:<feature>
<feature_view>@latest:<feature>
```

Examples:

```python
features = [
    "driver_hourly_stats:conv_rate",
    "driver_hourly_stats:acc_rate",
    "driver_hourly_stats@v2:avg_daily_trips",
]
```

Use `full_feature_names=True` when joining features from different views that share feature names and you need deterministic namespaced output.

## FeatureService inputs

A `FeatureService` groups model-facing features. It is the preferred selector for training and serving workflows because it tracks a model contract.

```python
service = store.get_feature_service("driver_activity_v1")
training = store.get_historical_features(entity_df=entity_df, features=service).to_df()
online = store.get_online_features(features=service, entity_rows=rows).to_dict()
```

`precompute_online=True` on a feature service stores the service features as a single online vector per entity. Materialization and push refresh these vectors. There is no silent fallback to per-feature-view reads if precomputed vectors are missing.

## Retrieval outputs

Historical retrieval returns a retrieval job. Common output conversions include:

```python
job = store.get_historical_features(entity_df=entity_df, features=features)
df = job.to_df()
```

Online retrieval returns an online response. Common conversions include:

```python
response = store.get_online_features(features=features, entity_rows=rows)
as_dict = response.to_dict()
as_df = response.to_df()
```

Expected online response shape:

```python
{
    "driver_id": [1001],
    "conv_rate": [0.42],
}
```

Missing online values may appear as `None`, `NaN`, empty tensors, or backend-specific nulls depending on output conversion and feature dtype.

## Local store defaults and files

A safe local setup generally uses:

```yaml
project: demo
provider: local
registry: data/registry.db
offline_store:
  type: file
online_store:
  type: sqlite
  path: data/online_store.db
```

Local file sources commonly point to Parquet files and declare timestamp columns in feature definitions:

```python
from feast import FileSource

source = FileSource(
    path="data/driver_stats.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)
```

Local materialization writes from file-backed offline data into the SQLite online store. If the SQLite file is deleted or a different repo path/config is used, online retrieval can return nulls even though historical retrieval still works.

## Backend families

Offline stores provide historical scans and point-in-time joins. Online stores provide low-latency key-value lookups after materialization or push.

Common offline-store families in Feast include local file, DuckDB, BigQuery, Snowflake, Redshift, Spark, Dask, Postgres, Ray, Trino, Athena, ClickHouse, MSSQL, Oracle, MongoDB, Couchbase, and remote offline store.

Common online-store families include SQLite, Redis-compatible stores, DynamoDB, Bigtable, Cassandra/Scylla, Datastore, Postgres, MySQL, Snowflake, MongoDB, Couchbase, HBase, Hazelcast, Elasticsearch, Dragonfly, SingleStore, remote online store, and vector-capable stores. Route backend selection and optional extras to `../../integrations-and-extensibility/SKILL.md` unless the user is debugging retrieval behavior itself.

# Feature Definitions API Reference

This reference captures the verified public constructor shape for Feast definition objects used in Python feature repos. Prefer keyword arguments because these constructors are keyword-only.

## Imports

Common definition imports:

```python
from datetime import timedelta
from feast import Entity, FeatureService, FeatureView, Field, FileSource, RequestSource, PushSource
from feast.on_demand_feature_view import on_demand_feature_view
from feast.types import Float32, Float64, Int64, String, Array
from feast.value_type import ValueType
```

Some sources and transformation classes live in provider-specific modules. If an import fails for a backend source, install the matching Feast extra or route backend setup to `../../integrations-and-extensibility/SKILL.md`.

## Verified Signatures

- `Entity(*, name: str, join_keys: Optional[List[str]] = None, value_type: Optional[ValueType] = None, description: str = '', tags: Optional[Dict[str, str]] = None, owner: str = '')`
- `Field(*, name: str, dtype: FeastType, description: str = '', tags: Optional[Dict[str, str]] = None, vector_index: bool = False, vector_length: int = 0, vector_search_metric: Optional[str] = None)`
- `FeatureView(*, name: str, source=None, sink_source=None, schema=None, entities=None, ttl=timedelta(0), online=True, offline=False, description='', tags=None, owner='', org='', mode=None, enable_validation=False, version='latest', enabled=True)`
- `BatchFeatureView(*, name: str, mode='python', source=None, sink_source=None, entities=None, ttl=None, tags=None, online=False, offline=False, description='', owner='', org='', schema=None, udf=None, udf_string='', feature_transformation=None, batch_engine=None, aggregations=None, enable_validation=False, version='latest')`
- `StreamFeatureView(*, name: str, source, sink_source=None, entities=None, ttl=timedelta(0), tags=None, online=True, offline=False, description='', owner='', org='', schema=None, aggregations=None, mode='python', timestamp_field='', udf=None, udf_string='', feature_transformation=None, stream_engine=None, enable_tiling=False, tiling_hop_size=None, enable_validation=False, version='latest')`
- `OnDemandFeatureView(*, name: str, entities=None, schema=None, sources=None, input_schema=None, udf=None, udf_string='', feature_transformation=None, mode='pandas', description='', tags=None, owner='', org='', write_to_online_store=False, singleton=False, track_metrics=False, aggregations=None, version='latest', enabled=True)`
- `on_demand_feature_view(*, name=None, entities=None, schema, sources=None, input_schema=None, aggregations=None, mode='pandas', description='', tags=None, owner='', org='', write_to_online_store=False, singleton=False, track_metrics=False, explode=False, version='latest')`
- `FeatureService(*, name: str, features: List[FeatureView | OnDemandFeatureView | LabelView], tags=None, description='', owner='', logging_config=None, precompute_online=False)`
- `RequestSource(*, name: str, schema: List[Field], timestamp_field=None, description='', tags=None, owner='')`
- `PushSource(*, name: str, batch_source=None, description='', tags=None, owner='')`
- `FileSource(*, path: str, name='', event_timestamp_column='', file_format=None, created_timestamp_column='', field_mapping=None, s3_endpoint_override=None, description='', tags=None, owner='', timestamp_field='')`

## Entities

An entity names the business key used to join and serve features.

```python
driver = Entity(
    name="driver",
    join_keys=["driver_id"],
    value_type=ValueType.INT64,
    description="Driver account identifier",
)
```

Important behavior:

- If `join_keys` is omitted, the join key defaults to the entity name.
- Only one join key is currently accepted; multiple join keys raise `ValueError`.
- Omitting `value_type` currently works but emits a deprecation warning; provide it for stable definitions.
- The entity `value_type` must match any declared schema field with the same join key.

## Fields and Feast Types

Use `Field` for feature columns and request-time input schema. `dtype` expects a Feast type object, not a raw Python type.

```python
schema = [
    Field(name="conv_rate", dtype=Float32),
    Field(name="lifetime_orders", dtype=Int64),
    Field(name="driver_name", dtype=String),
]
```

Vector fields are definition metadata for vector-capable stores and RAG workflows:

```python
embedding = Field(
    name="embedding",
    dtype=Array(Float32),
    vector_index=True,
    vector_length=384,
    vector_search_metric="COSINE",
)
```

Validation tips:

- If `vector_index=True`, set a positive `vector_length` and use a vector-compatible `dtype`, typically an array/list type.
- `Field.__eq__` compares `vector_length` but does not compare `vector_index` or `vector_search_metric`; do not rely on equality alone to detect vector metadata drift.
- Nested collection and struct metadata may be persisted in internal tags during protobuf conversion; keep user tags independent of system metadata.

## Data Sources

A source supplies event-time feature data to a feature view.

```python
driver_stats_source = FileSource(
    name="driver_stats_source",
    path="data/driver_stats.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created",
)
```

Source rules:

- Do not use the same column for `timestamp_field` and `created_timestamp_column`; the base `DataSource` constructor raises `ValueError`.
- `field_mapping` maps physical source column names to Feast feature names. Use it for feature columns, not entity or timestamp columns.
- `RequestSource` is for request-time inputs to ODFVs and requires a `schema` list of `Field` objects.
- `PushSource` should usually wrap a `batch_source`; stream feature views and historical retrieval need that batch backing.

## Feature Views

A feature view groups schema, entities, source, TTL, and online/offline behavior.

```python
driver_stats_fv = FeatureView(
    name="driver_stats",
    entities=[driver],
    ttl=timedelta(days=7),
    schema=[Field(name="conv_rate", dtype=Float32)],
    source=driver_stats_source,
    online=True,
    offline=False,
    tags={"team": "risk"},
)
```

Constructor behavior:

- `source` may be a `DataSource`, another `FeatureView`, or a list of `FeatureView`s for derived definitions.
- `entities=None` creates an internal dummy entity for entityless views.
- `ttl=timedelta(0)` means values live forever and can make historical queries expensive. Prefer a bounded TTL when point-in-time freshness matters.
- `online=True` enables online retrieval/materialization for the view; `offline=True` enables writes to an offline sink path for derived/batch workflows.
- `enable_validation=True` enables schema validation during materialization. Missing required columns raise `ValueError`; type mismatches are warning-oriented in supported compute engines.
- `version='latest'` is the default version tag; use explicit versions for staged definition migration.

## Feature Services

A feature service is a named projection of feature views, ODFVs, and label views for model-facing retrieval.

```python
fraud_model_v1 = FeatureService(
    name="fraud_model_v1",
    features=[driver_stats_fv[["conv_rate"]]],
    owner="ml-platform",
    precompute_online=False,
)
```

Rules:

- Feature service `features` must contain feature views, ODFVs, label views, or projections from them.
- A projection like `driver_stats_fv[["conv_rate"]]` selects specific fields.
- If `precompute_online=True`, Feast maintains one serialized online vector per entity for the service.
- `precompute_online=True` is incompatible with an `OnDemandFeatureView` whose `write_to_online_store=False`; `FeatureService.validate()` raises `ValueError`.

## Labels and Permissions Basics

Label views and permission objects are registry definitions that can be referenced from feature services and protected endpoints. For modeling tasks:

- Treat labels like model-facing definitions with source, schema, entities, and conflict-policy concerns; label retrieval and UI behavior belongs to retrieval/server skills.
- Treat permissions as metadata definitions for allowed actions and resources. Auth/RBAC enforcement and server failure handling belongs to `../../servers-and-remote/SKILL.md`.

## Safe Local Checks

Definition objects often expose local validation or serialization hooks. Safe checks before apply include:

```python
for obj in [driver_stats_fv, fraud_model_v1]:
    if hasattr(obj, "ensure_valid"):
        obj.ensure_valid()
    if hasattr(obj, "validate") and obj.__class__.__name__ == "FeatureService":
        obj.validate()
    if hasattr(obj, "to_proto"):
        obj.to_proto()
```

For a whole file, use `../scripts/validate_feature_definitions.py` from this sub-skill instead of writing ad hoc introspection.

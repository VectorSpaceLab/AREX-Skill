# Data Modeling Patterns

Use these patterns when authoring or reviewing Feast definitions. They are definition-only patterns; applying, planning, and registry lifecycle are routed to `../../feature-repos-and-cli/SKILL.md`.

## Minimal Batch Feature View

```python
from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int64
from feast.value_type import ValueType

customer = Entity(name="customer", join_keys=["customer_id"], value_type=ValueType.INT64)

customer_source = FileSource(
    name="customer_stats_source",
    path="data/customer_stats.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)

customer_stats = FeatureView(
    name="customer_stats",
    entities=[customer],
    ttl=timedelta(days=14),
    schema=[
        Field(name="total_orders", dtype=Int64),
        Field(name="avg_order_value", dtype=Float32),
    ],
    source=customer_source,
    online=True,
)
```

Checklist:

- Entity join key appears in the source data and uses a stable type.
- Event timestamp is a real event-time column; created timestamp is only for deduplication.
- TTL is bounded unless the feature is intentionally timeless.
- Schema fields name feature columns, not entity/timestamp columns, unless you intentionally need entity schema validation.

## Entityless Definitions

If `entities` is omitted, Feast uses an internal dummy entity. Entityless views are useful for global features but can surprise users expecting entity-keyed online retrieval.

```python
global_stats = FeatureView(
    name="global_stats",
    schema=[Field(name="market_volatility", dtype=Float32)],
    source=customer_source,
    ttl=timedelta(hours=6),
)
```

Use entityless feature views only when the feature value is not keyed by a real business object. For keyed features, define an `Entity` and pass it explicitly.

## Field Types and Schema Design

Prefer explicit schema when possible:

```python
from feast.types import Array, Float32, Int64, String

schema = [
    Field(name="age_days", dtype=Int64),
    Field(name="segment", dtype=String),
    Field(name="embedding", dtype=Array(Float32), vector_index=True, vector_length=128),
]
```

Guidance:

- Use Feast types from `feast.types`, not native `int`, `float`, or `str`.
- Add descriptions and tags when definitions will be shared across teams.
- For vector fields, keep model embedding dimension in `vector_length` and use a consistent metric expected by the selected vector store.
- Type inference can fill schemas from supported stores, but explicit schema catches drift earlier and supports selected feature-service projections.

## Source Selection

Use the narrowest source that matches the data path:

- `FileSource`: local/S3/GCS/Azure file-backed batch data such as Parquet.
- Warehouse sources such as BigQuery, Snowflake, Redshift, and Postgres: use provider-specific modules and extras.
- `RequestSource`: request-time data for on-demand transformations.
- `PushSource`: application-pushed events, usually with a batch backing source for offline history.
- Kafka/Kinesis stream sources: use stream-specific source classes and a `batch_source` when building stream feature views.

Base source validation signals:

- Same `timestamp_field` and `created_timestamp_column` raises `ValueError`.
- Missing optional extra can appear as `ImportError` for provider-specific classes.
- Unsupported source type in a `StreamFeatureView` raises `ValueError` naming supported stream sources.

## Request and Push Sources

Request-time inputs for ODFVs:

```python
request = RequestSource(
    name="request_context",
    schema=[
        Field(name="transaction_amount", dtype=Float32),
        Field(name="merchant_category", dtype=String),
    ],
)
```

Push source backed by batch history:

```python
fraud_events_push = PushSource(
    name="fraud_events_push",
    batch_source=FileSource(
        name="fraud_events_batch",
        path="data/fraud_events.parquet",
        timestamp_field="event_timestamp",
    ),
)
```

Push ingestion behavior itself belongs to `../../retrieval-and-materialization/SKILL.md`; this sub-skill only models the source objects.

## Feature Services and Projections

Use a feature service to capture the exact feature contract for a model version:

```python
risk_v2 = FeatureService(
    name="risk_v2",
    features=[
        customer_stats[["total_orders", "avg_order_value"]],
    ],
    tags={"model": "risk", "version": "v2"},
)
```

Projection tips:

- Project only the fields a model needs to reduce accidental coupling.
- Give services model/version-oriented names, even when feature views use source-oriented names.
- If selecting features from a view with inferred schema, inference must happen before the projection can be validated against actual fields.
- Set `precompute_online=True` only for latency-critical online services and validate ODFV compatibility.

## Labels

Label views are useful when labels are registered and managed alongside features. In definition work:

- Model label entities, source, schema, and metadata with the same care as feature views.
- Keep conflict-policy and labeler semantics explicit if multiple labelers can write values for the same entity.
- A feature service may include label views, but model training/retrieval workflow belongs to `../../retrieval-and-materialization/SKILL.md`.

## Permission Metadata

Permissions are definition objects that describe allowed actions/resources for protected endpoints. Keep this distinction clear:

- Definition authoring can include permission object names, tags, roles, resources, and intended actions.
- Runtime enforcement, 401/403 diagnosis, server auth config, and token/client behavior belong to `../../servers-and-remote/SKILL.md`.

## Versioning Definitions

`FeatureView`, `OnDemandFeatureView`, `BatchFeatureView`, and `StreamFeatureView` accept `version='latest'` by default. Use explicit version strings when migrating schema or transformations:

```python
customer_stats_v2 = FeatureView(
    name="customer_stats",
    version="v2",
    entities=[customer],
    ttl=timedelta(days=14),
    schema=[Field(name="avg_order_value", dtype=Float32)],
    source=customer_source,
)
```

Versioning notes:

- Versioning separates definition snapshots for a feature view name.
- Publishing/promoting versions is a repo lifecycle operation; route to `../../feature-repos-and-cli/SKILL.md`.
- Version-qualified retrieval and materialization behavior is retrieval-side; route to `../../retrieval-and-materialization/SKILL.md`.
- For side-by-side testing without relying on registry version support, use separate project names or distinct feature view names.

## Design Review Checklist

Before apply, ask:

- Do entity join keys, source columns, and request-time inputs line up by name and type?
- Does each feature view have the right TTL for online freshness and historical point-in-time windows?
- Are `online` and `offline` flags intentionally set for the desired writes and retrievals?
- Are vector fields dimensioned and routed to vector workflow guidance if retrieval is requested?
- Does every ODFV have valid sources or `input_schema` and a compatible transformation mode?
- Does each model-facing feature service project only the intended fields?

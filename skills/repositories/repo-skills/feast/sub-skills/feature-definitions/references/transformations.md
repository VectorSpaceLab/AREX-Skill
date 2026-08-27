# Transformations, Validation, and Versioning

This reference covers definition-time transformation objects. Running retrievals, materialization, or push ingestion belongs to `../../retrieval-and-materialization/SKILL.md`.

## On-Demand Feature Views

On-demand feature views define transformations over existing feature views, projections, and request-time data. They can be built with the class constructor or the decorator.

```python
import pandas as pd
from feast import Field, RequestSource
from feast.on_demand_feature_view import on_demand_feature_view
from feast.types import Float32

request = RequestSource(
    name="request_context",
    schema=[Field(name="transaction_amount", dtype=Float32)],
)

@on_demand_feature_view(
    sources=[customer_stats, request],
    schema=[Field(name="order_value_ratio", dtype=Float32)],
    mode="pandas",
)
def order_value_features(inputs: pd.DataFrame) -> pd.DataFrame:
    output = pd.DataFrame()
    output["order_value_ratio"] = inputs["transaction_amount"] / inputs["avg_order_value"]
    return output
```

Definition rules:

- Provide either `sources` or `input_schema`; otherwise construction raises `ValueError`.
- `sources` may contain `FeatureView`, `FeatureViewProjection`, or `RequestSource` objects.
- `input_schema` creates an internal request source for request-time inputs and is useful for source-free request transforms.
- Source names must be unique across feature views/projections and request sources.
- If `write_to_online_store=True`, the ODFV needs entity context and is meant to store transformed values for faster online reads.
- `singleton=True` only works with `mode='python'`; other modes raise `ValueError`.
- ODFVs without aggregations need a valid UDF or `feature_transformation`; otherwise `ensure_valid()` raises `ValueError`.

## ODFV With Input Schema Only

Use `input_schema` when the transformation consumes request-time fields that are not stored as a named `RequestSource`.

```python
@on_demand_feature_view(
    input_schema=[
        Field(name="amount", dtype=Float32),
        Field(name="baseline", dtype=Float32),
    ],
    schema=[Field(name="normalized_amount", dtype=Float32)],
    mode="pandas",
)
def normalize_amount(inputs: pd.DataFrame) -> pd.DataFrame:
    output = pd.DataFrame()
    output["normalized_amount"] = inputs["amount"] / inputs["baseline"]
    return output
```

If aggregations are supplied with `input_schema`, aggregation columns must exist in the input schema; unknown columns raise `ValueError` naming the missing columns and available fields.

## Write-Time vs Read-Time ODFVs

`write_to_online_store` controls when transformed values are stored:

- `False` default: transformation runs during reads. This is flexible but adds online serving compute.
- `True`: transformation runs during ingestion/write and transformed values are stored in the online store. This improves read latency but requires compatible entity/source setup and ingestion workflow.

Feature service compatibility:

```python
service = FeatureService(
    name="low_latency_service",
    features=[write_time_odfv],
    precompute_online=True,
)
service.validate()
```

If the service includes an ODFV with `write_to_online_store=False`, `validate()` raises an error because serve-time transforms cannot be pre-computed.

## Batch Feature Views

`BatchFeatureView` extends feature view modeling with batch transformation metadata and optional sink behavior.

```python
from feast.batch_feature_view import BatchFeatureView

weekly_customer_features = BatchFeatureView(
    name="weekly_customer_features",
    source=customer_stats,
    sink_source=FileSource(
        name="weekly_customer_features_sink",
        path="data/weekly_customer_features.parquet",
        timestamp_field="event_timestamp",
    ),
    entities=[customer],
    ttl=timedelta(days=30),
    schema=[Field(name="weekly_avg_order_value", dtype=Float32)],
    online=False,
    offline=True,
    mode="python",
    version="v1",
)
```

Guidance:

- Use `source` for the base data or upstream feature views.
- Use `sink_source` when the derived batch output should be written to a data source.
- Defaults differ from `FeatureView`: verified `BatchFeatureView` has `online=False` and `offline=False` in the live constructor, while convenience decorators may show different defaults. Set both flags explicitly.
- `enable_validation=True` requests schema validation during materialization in supported engines.

## Stream Feature Views

`StreamFeatureView` requires a stream source such as `KafkaSource`, `PushSource`, or a custom source.

```python
from feast.stream_feature_view import StreamFeatureView

live_driver_stats = StreamFeatureView(
    name="live_driver_stats",
    source=fraud_events_push,
    entities=[customer],
    ttl=timedelta(hours=2),
    schema=[Field(name="recent_event_count", dtype=Int64)],
    online=True,
    offline=False,
)
```

Validation behavior:

- Passing a non-stream source such as plain `FileSource` directly to `StreamFeatureView` raises `ValueError` naming supported stream sources.
- If `aggregations` are configured, `timestamp_field` is required.
- If `enable_tiling=True` with windowed aggregations, `tiling_hop_size` must be smaller than the minimum aggregation window; otherwise a `ValueError` explains the invalid hop/window relationship.
- Stream transformations support modes including Python, pandas, Spark SQL, Spark, and Flink when the corresponding environment is available.

## Schema Validation

`enable_validation=True` on feature views, batch feature views, or stream feature views enables validation during materialization in supported compute engines. Definition-time checks can only catch obvious local mistakes; data-dependent validation happens later.

Expected signals:

- Missing required source columns raise `ValueError` during materialization.
- Type mismatches may be logged as warnings rather than blocking execution.
- Unsupported optional store/compute dependencies surface as import or backend errors before validation can run.

Use the bundled script for definition-level checks, then route materialization validation to `../../retrieval-and-materialization/SKILL.md`.

## Transformations and UDF Strings

Constructors accept either callable UDFs or explicit transformation objects.

- If `feature_transformation` is provided, it has precedence over `udf` and `udf_string`.
- `udf_string` is useful for diffing and display, but the callable/transformation must still be valid.
- For stream transformations, import dependencies inside the UDF if the target runtime needs self-contained functions.
- Keep transformation output column names exactly aligned with declared `schema` fields.

## Converting an Older Snippet to Versioned ODFV + Service

When a user has an older plain feature view or read-time transform and asks for a versioned ODFV plus service:

1. Preserve the base `Entity`, `Field`, and source definitions.
2. Add explicit `version` to the base feature view and ODFV, such as `version='v2'`.
3. Decide whether ODFV should be read-time or write-time. Use `write_to_online_store=True` only if ingestion/materialization should store transformed values.
4. Define the ODFV with `sources` or `input_schema`, explicit output `schema`, and a compatible `mode`.
5. Create a `FeatureService` with projected base features plus the ODFV.
6. Call safe local checks (`ensure_valid`, `FeatureService.validate`, `to_proto`) before routing apply/retrieval work.

Skeleton:

```python
@on_demand_feature_view(
    name="risk_transform",
    sources=[customer_stats_v2, request],
    schema=[Field(name="risk_score", dtype=Float32)],
    mode="pandas",
    write_to_online_store=False,
    version="v2",
)
def risk_transform(inputs: pd.DataFrame) -> pd.DataFrame:
    output = pd.DataFrame()
    output["risk_score"] = inputs["avg_order_value"] * inputs["transaction_amount"]
    return output

risk_service_v2 = FeatureService(
    name="risk_service_v2",
    features=[customer_stats_v2[["avg_order_value"]], risk_transform],
)
```

## Versioning Notes

- Version parameters exist on standard, on-demand, batch, and stream feature views.
- Version promotion, `--no-promote`, staged apply, and registry support are not definition-only concerns; route them to `../../feature-repos-and-cli/SKILL.md`.
- Version-qualified retrieval and online store limitations belong to `../../retrieval-and-materialization/SKILL.md`.
- If a user only needs deterministic modeling without registry versioning, unique object names can be simpler than shared names with version strings.

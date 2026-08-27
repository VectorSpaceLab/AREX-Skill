# Conversions

qdrant-client exposes generated REST pydantic models and generated gRPC protobuf messages. The conversion layer translates between them for client methods that can use either transport.

Use this reference when a task needs to debug model shape, verify REST/gRPC parity, or convert a request/response object without sending it to a server.

## Direction Matters

```python
from qdrant_client.conversions.conversion import RestToGrpc, GrpcToRest
```

- `RestToGrpc.convert_*` accepts generated REST pydantic models from `qdrant_client.models` or `qdrant_client.http.models` and returns protobuf messages from `qdrant_client.grpc`.
- `GrpcToRest.convert_*` accepts protobuf messages and returns REST pydantic models.
- Helper names usually mirror model names in snake case, such as `convert_filter`, `convert_vector_params`, `convert_query_request`, and `convert_query_interface`.
- Some request conversions need context that is not stored in the REST object, such as `collection_name` for `convert_query_request` and `convert_query_points`.

Minimal one-object conversion:

```python
from qdrant_client import models
from qdrant_client.conversions.conversion import RestToGrpc, GrpcToRest

filter_ = models.Filter(
    must=[models.FieldCondition(key="kind", match=models.MatchValue(value="article"))]
)
grpc_filter = RestToGrpc.convert_filter(filter_)
rest_filter = GrpcToRest.convert_filter(grpc_filter)
```

## Common Type Aliases

`qdrant_client.conversions.common_types` defines type aliases accepted by higher-level client code. Important aliases include:

- `Filter = rest.Filter | grpc.Filter`
- `SearchParams = rest.SearchParams | grpc.SearchParams`
- `PayloadSelector = rest.PayloadSelector | grpc.WithPayloadSelector`
- `Distance = rest.Distance | int` because gRPC enums are integer-like.
- `PointId = int | str | UUID | grpc.PointId`
- `Points = Batch | Sequence[rest.PointStruct | grpc.PointStruct]`
- `PointsSelector = list[PointId] | rest.Filter | grpc.Filter | rest.PointsSelector | grpc.PointsSelector`
- `VectorParams`, `SparseVector`, `VectorInput`, `Prefetch`, `Document`, `Image`, and `QueryRequest` map to their REST classes unless explicitly noted.

Aliases are helpful for method typing, but conversion helpers still require the concrete direction: REST model into `RestToGrpc`, protobuf message into `GrpcToRest`.

## Payload Values

Payload conversion helpers are deterministic:

```python
from qdrant_client.conversions.conversion import payload_to_grpc, grpc_to_payload

grpc_payload = payload_to_grpc({"n": 1, "ok": True, "tags": ["a", "b"]})
plain_payload = grpc_to_payload(grpc_payload)
```

Supported JSON-like values are `None`, `bool`, `int`, `float`, `str`, lists/tuples, dictionaries, `date`, and `datetime`. Dates and datetimes are serialized to JSON-compatible strings through the pydantic compatibility layer. Protobuf integer values can appear as strings in generic protobuf JSON, but qdrant-client converts them back to Python `int`.

## Datetime Conversion

`RestToGrpc.convert_datetime()` accepts `datetime` or `date`:

- A `date` becomes a midnight `datetime` before protobuf timestamp conversion.
- A `datetime` is passed to protobuf `Timestamp.FromDatetime`.
- `GrpcToRest.convert_timestamp()` converts protobuf timestamps to timezone-aware UTC datetimes.
- `DatetimeRange` fields `lt`, `gt`, `gte`, and `lte` are converted field-by-field.

When debugging timezone issues, inspect both the original Python object and the resulting protobuf timestamp. Prefer timezone-aware UTC datetimes when exact instants matter.

## Filters and `min_should`

`RestToGrpc.convert_filter()` normalizes single conditions and condition lists:

- `must`, `must_not`, and `should` may be one condition or a list.
- `min_should` must be `models.MinShould(conditions=[...], min_count=...)`.
- Nested REST `Filter` objects are converted into gRPC `Condition(filter=...)` when used as conditions.
- `GrpcToRest.convert_filter()` returns lists for repeated condition fields and reconstructs `MinShould` when the protobuf field is set.

Debug nested mismatches by converting the smallest condition first with `convert_condition()`, then the enclosing `Filter`.

## Vectors and Batches

Dense vectors are Python lists of floats. Sparse vectors use `models.SparseVector(indices=[...], values=[...])`, where indices are unique and `indices` and `values` have the same length.

Useful conversion helpers:

- `convert_vector_input()` handles dense vectors, multi-dense vectors, sparse vectors, `Document`, `Image`, and `InferenceObject` query inputs.
- `convert_sparse_vector()` returns a protobuf sparse vector.
- `convert_sparse_vector_to_vector()` wraps a sparse vector in a protobuf vector oneof.
- `convert_vector_struct()` handles unnamed vectors, named vectors, and sparse named vectors.
- `convert_batch_vector_struct(batch, num_records)` expands vector batches into one protobuf `Vectors` message per record.

For batch debugging, check that every named vector has the same number of records as `num_records`. Empty list and empty dict batches are valid but mean different vector shapes.

## Query Interfaces and Prefetch

`RestToGrpc.convert_query_interface()` dispatches high-level query inputs into a gRPC `Query` message. Common inputs include dense vectors, sparse vectors, point IDs, `NearestQuery`, `RecommendQuery`, `DiscoverQuery`, `ContextQuery`, `FusionQuery`, `SampleQuery`, `FormulaQuery`, `RrfQuery`, and relevance-feedback queries.

`RestToGrpc.convert_prefetch_query()` converts one `models.Prefetch` recursively:

- A nested single `Prefetch` becomes a one-item list of nested prefetch queries.
- A nested list remains a list.
- `query`, `using`, `filter`, `params`, `score_threshold`, `limit`, and `lookup_from` are converted independently.

`RestToGrpc.convert_query_request(query_request, collection_name=...)` returns gRPC `QueryPoints`. A single top-level `QueryRequest.prefetch` becomes a one-item `prefetch` list; `with_payload` and `with_vector` are converted to selector messages when present.

## Generated gRPC Surface

The `qdrant_client.grpc` namespace contains generated protobuf modules and service stubs. Use those types only when a task already needs low-level protobuf messages or raw stub access. For ordinary application code, construct REST models via `qdrant_client.models` and let client methods or conversion helpers translate them.

Route raw channel/stub lifecycle, `client.grpc_points`, `client.grpc_collections`, and transport configuration to `connection-and-transport`.

## Conversion Debugging Checklist

1. Print or inspect the REST model class and fields before conversion.
2. Convert the smallest nested object first, such as `FieldCondition`, `SparseVector`, or `Prefetch`.
3. Confirm converter direction: REST pydantic model into `RestToGrpc`, protobuf message into `GrpcToRest`.
4. Pass required context parameters such as `collection_name`.
5. If a protobuf oneof looks empty, inspect which field is set rather than relying on generic dict output.
6. Round-trip with `GrpcToRest` only when the reverse converter exists and no transport-only metadata is expected.

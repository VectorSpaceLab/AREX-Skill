# Troubleshooting Models and Conversions

## Pydantic Rejects an Extra Field

Symptom: constructing a model raises a validation error for an unexpected keyword, extra input, or forbidden field.

Likely causes:

- Generated REST classes such as `VectorParams`, `PointStruct`, `Filter`, `Prefetch`, and `QueryRequest` are strict pydantic models.
- The code uses REST JSON field spelling that does not match the Python constructor field.
- A field belongs on another model, such as `with_payload` on `QueryRequest` rather than `Prefetch`.

Fixes:

- Check the nearest model reference and use exact constructor fields.
- Build nested models explicitly instead of passing a large raw dict during debugging.
- Use normal constructors for user data; reserve pydantic compatibility `construct()` for trusted internal tooling.

## Enum or String Mismatch

Symptom: validation rejects a string value, a REST/gRPC conversion produces the wrong enum, or serialized output has unexpected capitalization.

Likely causes:

- REST enum classes often inherit from `str`, while gRPC enum values are integer-like.
- API values are case-sensitive and may not match Python member names.
- The wrong enum family is used, such as `PayloadSchemaType` versus gRPC `FieldType`.

Fixes:

- Prefer enum members, for example `models.Distance.COSINE`, `models.Fusion.RRF`, and `models.PayloadSchemaType.KEYWORD`.
- Use payload schema helpers when translating schema enums: `grpc_payload_schema_to_field_type()` and `grpc_field_type_to_payload_schema()`.
- Do not compare REST enum objects directly with raw gRPC integer enum values unless the alias explicitly allows it.

## Sparse Vector Size or Shape Mismatch

Symptom: sparse vectors fail validation, conversion output is empty, or batch conversion has unexpected record counts.

Likely causes:

- `SparseVector.indices` and `SparseVector.values` have different lengths.
- Sparse indices are repeated or are not integers.
- A named batch has a different number of vector records than `num_records`.
- A sparse vector is passed where a named vector dictionary or `NamedSparseVector` is expected.

Fixes:

- Construct sparse vectors as `models.SparseVector(indices=[...], values=[...])` with equal lengths.
- For point vectors, use a named dictionary such as `{"sparse": models.SparseVector(...)}` when the collection has named sparse vectors.
- Test batch shapes with `RestToGrpc.convert_batch_vector_struct(batch, num_records)` before calling upload/upsert code.

## REST Model and Protobuf Type Confusion

Symptom: `RestToGrpc` rejects an object, `GrpcToRest` rejects an object, or a client method behaves differently between REST and gRPC transport.

Likely causes:

- A protobuf message from `qdrant_client.grpc` was passed to a `RestToGrpc` converter.
- A pydantic REST model from `qdrant_client.models` was passed to a `GrpcToRest` converter.
- A higher-level client method accepts alias types, but a low-level converter expects one concrete side.

Fixes:

- Use `RestToGrpc.convert_*` only for REST pydantic models.
- Use `GrpcToRest.convert_*` only for protobuf messages.
- When in doubt, print `type(value)` and convert one level at a time.
- Route raw stub/channel questions to `connection-and-transport`.

## Datetime Timezone Conversion Surprise

Symptom: converted datetime values shift timezone, dates become midnight timestamps, or round-trip output is timezone-aware when input was not.

Likely causes:

- `date` values are converted to midnight datetimes.
- Protobuf timestamp conversion stores instants, and `GrpcToRest` returns UTC-aware datetimes.
- Payload conversion serializes date/datetime values to JSON-compatible strings, while `DatetimeRange` conversion uses protobuf timestamps.

Fixes:

- Prefer timezone-aware UTC `datetime` objects for `DatetimeRange` when exact instants matter.
- Use date values only when midnight semantics are intended.
- Distinguish payload datetime strings from filter datetime range timestamps during debugging.

## Nested Filter or `min_should` Conversion Mismatch

Symptom: a nested filter converts but the resulting gRPC message has conditions in a different shape than expected.

Likely causes:

- `Filter.must`, `should`, and `must_not` accept either a single condition or a list, but gRPC stores repeated lists.
- `min_should` requires a `MinShould` object with `conditions` and `min_count`.
- A nested `Filter` used as a condition becomes a gRPC `Condition(filter=...)` oneof.

Fixes:

- Normalize your Python examples to lists for readability.
- Convert the condition with `RestToGrpc.convert_condition()` before converting the full filter.
- Round-trip with `GrpcToRest.convert_filter()` to confirm the semantic structure rather than exact object identity.

## Flat Prefetch Normalization Surprise

Symptom: `QueryRequest.prefetch=models.Prefetch(...)` becomes a list in gRPC output, or nested prefetch recursion appears flattened differently than expected.

Likely causes:

- Top-level `QueryRequest` conversion wraps a single `Prefetch` into a one-item gRPC repeated field.
- Nested `Prefetch.prefetch` also accepts a single `Prefetch` or list and converts recursively.
- `Prefetch` and `QueryRequest` share many fields, but `offset`, `with_vector`, `with_payload`, and `shard_key` are top-level request fields.

Fixes:

- Use `prefetch=[...]` explicitly in complex examples.
- Keep `with_payload` and `with_vector` on `QueryRequest` unless a specific client method documents otherwise.
- Inspect `RestToGrpc.convert_prefetch_query()` for one nested prefetch and `RestToGrpc.convert_query_request()` for the full request.

## Inference Schema Parser Finds No Paths

Symptom: `ModelSchemaParser.parse_model()` succeeds but `_cache[model_name]` is empty.

Likely causes:

- The model has no `Document`, `Image`, or `InferenceObject` fields.
- Recursive references that do not contain inference objects, such as many filter paths, are intentionally excluded.
- The parser cache already contains a result for that model.

Fixes:

- Parse models known to contain query/vector inputs, such as `PointStruct`, `Batch`, `Prefetch`, `QueryRequest`, or `QueryRequestBatch`.
- Treat the parser as a schema-inspection tool; use the `inference` sub-skill for embedding execution and optional dependency issues.

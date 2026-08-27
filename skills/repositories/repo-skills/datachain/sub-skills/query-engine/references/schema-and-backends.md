# Schema Mapping and Backend-Sensitive Behavior

## Purpose

Read this before diagnosing nested-field bugs, schema mismatches, SQL type
conversion issues, null behavior, vector/function failures, or any query result
that was checked only on local SQLite. DataChain presents one logical API over
multiple SQL warehouse backends, so schema and backend assumptions must be made
explicit.

## Logical Signals vs Physical Columns

DataChain carries two schema views at the same time:

- **Logical schema**: a Python / Pydantic model tree. `SignalSchema` is the
  source of truth and is serialized with dataset versions.
- **Physical schema**: flattened database columns plus backend-specific SQL
  types.

A signal is a typed column: either a scalar/list/dict-like type or a DataChain
`DataModel`. Nested `DataModel` fields flatten into database columns by joining
path components with `__`.

| Logical user field | Physical database column |
| --- | --- |
| `id` | `id` |
| `file.path` | `file__path` |
| `response.usage.prompt_tokens` | `response__usage__prompt_tokens` |
| `maybe_response` as `Optional[DataModel]` | an internal `_type_tag` sentinel plus flattened leaves |

Prefer dot paths in public API examples (`"file.path"`, `dc.C("file.path")`).
Treat raw `__` names as a debugging view unless a lower-level API explicitly
expects physical column names.

## `SignalSchema` Resolution Rules

Important `SignalSchema` behaviors for query work:

- `resolve("a.b")` returns a schema for the requested signal or nested field and
  raises a signal resolution error when any path segment is absent.
- `db_signals()` returns physical leaf columns. With `as_columns=True`, the
  returned `Column` objects carry SQL types derived from the logical schema.
- `user_signals()` returns dot-path leaves for user-facing display and schema
  comparison.
- `select("parent.leaf")` and `select_except("parent.leaf")` build partial
  models so a selected parent object remains logically structured.
- Selecting all leaves under a model reuses the original model type; selecting a
  subset creates a generated partial model.
- Names containing the physical delimiter `__` are risky for logical model
  hydration. Use ordinary Python/Pydantic field names and let DataChain map dots
  to `__`.

Use the bundled [schema_probe.py](../scripts/schema_probe.py) helper to print a
small tree, user signal list, and physical column list.

## Column Expressions and Type Enrichment

`dc.C("col")` / `dc.Column("col")` produces a SQLAlchemy-style column
expression. The initial expression may be untyped, so DataChain enriches
expression trees against the current `SignalSchema` before using them in
`mutate`, `group_by`, `select`, and function calls.

Practical consequences:

- Referenced columns must exist in the current chain schema.
- Complex object columns cannot be passed to scalar SQL functions; choose a leaf
  such as `"rec.i"` or use a Python UDF workflow.
- If SQLAlchemy reports a `NullType` or DataChain cannot infer a result type,
  use a schema-backed column reference, `dc.func.cast(...)`, or a simpler typed
  expression.
- Derived expressions over nullable scalar inputs are themselves nullable and
  must be represented as nullable in the logical schema so values round-trip.

## Python-to-SQL and SQL-to-Python Conversion

DataChain maps Python annotations to DataChain SQL types when flattening schemas
and maps SQL expression types back to Python types when inferring derived signal
schemas.

| Python / annotation input | Query type behavior |
| --- | --- |
| `int`, `float`, `str`, `bool`, `bytes`, `datetime` | Mapped to numeric, string, boolean, binary, or datetime SQL types. |
| `Literal[...]` and `Enum` | Stored as strings. |
| `dict` / mapping types | Stored as JSON. |
| `list[...]` / sequence annotations | Stored as arrays; element type is preserved when possible. |
| `list[DataModel]` | Stored as an array of JSON-like objects. |
| `Optional[T]` for scalar `T` | Uses the same SQL type with DataChain nullability metadata. |
| Unions of string literals | Stored as strings. |
| Heterogeneous or object-heavy list/union shapes | Fall back toward JSON-like representation. |

`sql_to_python` uses the SQL expression's `python_type`; decimal-like SQL values
are normalized to `float`, typed arrays become `list[item_type]`, and unsupported
SQL types fall back to `str` for inference.

## Nullability and Optional Models

Nullability is a high-risk area because warehouses disagree on defaults and
costs.

- Most warehouses are nullable by default; ClickHouse is not. DataChain marks
  nullable scalar leaves so the backend converter can emit an appropriate
  nullable physical type.
- `Optional[scalar]` stores real `NULL` where the backend supports it.
- `Optional[DataModel]` gets an internal `_type_tag` discriminator plus leaf
  columns. The sentinel marks whether the model is present or absent; absent
  leaves occupy physical slots so the flattened row shape remains stable.
- Outer/full joins widen scalar leaves on unmatched sides to nullable where
  DataChain can represent that safely. Collections and complex models require
  extra care; do not assume a full join proves every backend preserves the same
  null semantics.
- Ordering nullable columns uses explicit `NULLS LAST` in DataChain-controlled
  `order_by` / window ordering paths, because SQLite and stricter warehouses do
  not order nulls identically by default.

## Backend Divergences to Preserve

DataChain's public API aims for identical user-visible behavior across
backends, but the implementation must design for the set of backends rather than
for one convenient engine.

| Backend axis | What to remember |
| --- | --- |
| SQLite | Local default and permissive. It can mask strict-backend bugs. SQLite stores `NaN` as `NULL`, so an `Optional[float]` `NaN` may read back as `None` locally while other backends keep `NaN` distinct from `NULL`. |
| ClickHouse | Studio/SaaS backend with non-null defaults and explicit costly `Nullable(T)`. Nullability must be propagated through expressions instead of patched at individual leaves. |
| BigQuery / Snowflake / Postgres | Future or additional SQL backends should be treated as first-class targets. Keep shared logic SQL-standard and push dialect quirks into backend converters. |
| Collections | ClickHouse and BigQuery cannot represent nullable array/map values in the same way as nullable scalars. Do not encode meaning in collection `None` versus empty collection across backends; lift that state into a nullable scalar or model discriminator. |
| Hashing | Hash functions use backend implementations. Do not compare exact hashes across engines unless that function is explicitly defined to match. |
| Regex | Regex dialects and flags can differ. Inline `(?i)` can express case-insensitive matching in DataChain examples, but edge cases still need target-backend checks. |
| RNG / random sampling | Random values and sampling order are backend-local. Do not assert exact random values across engines. |
| Vector functions | Local SQLite vector distance may rely on optional vector dependencies or loadable support; other backends may compile or execute vector functions differently. |
| Expression over joins | Backends can diverge on expression evaluation across joins and null-padded rows. Verify actual read-back values, not only declared schema. |

## Backend Verification Mindset

For query-engine changes or high-confidence answers:

1. Enumerate the paths involved: `filter`, `order_by`, `mutate`, `group_by`,
   `distinct`, `merge`, `subtract`, `union`, `window`, terminal aggregates, and
   relevant export/read-back paths if the result leaves the Query Engine.
2. Include degenerate rows: empty input, one row, all-null, mixed null/non-null,
   present-on-one-side-only joins, duplicate keys, and both `union` arm orders.
3. Test nested fields both as bare leaves and inside composed expressions such
   as `(dc.C("a.b") + 1).label("x")`.
4. Verify values read back on the strict backend. A local SQLite smoke is useful
   for basic API shape but is not backend parity evidence.
5. Treat a backend crash separately from a value divergence. Re-run suspected
   shared-warehouse crashes in a small isolated case before calling them product
   bugs.

## Practical Schema Debugging Checklist

- Print `chain.signals_schema.user_signals()` to see logical dot paths.
- Print `chain.signals_schema.db_signals()` only when debugging physical SQL
  column names.
- Use `select("parent.leaf")` to keep a partial logical object instead of
  flattening everything into unrelated top-level fields.
- Use `dc.C("parent.leaf")` in expressions and functions; avoid mixing dot and
  `__` forms in the same public example.
- When a query changes nullability or schema shape, verify the actual rows after
  `save` / reload on the backend you are claiming, not only the in-memory schema
  object.

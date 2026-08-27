# Schema and Backend Change Matrix

Read this before changing DataChain code that maps logical signals to physical
columns, stores schema metadata, exports nested values, or depends on warehouse
backend behavior.

## Core Invariants

- A signal is a typed column: a scalar type or a Pydantic/DataChain model.
- Nested model fields flatten into physical database columns while the logical
  `SignalSchema` remains the source of truth.
- `SignalSchema` and SQL type information are serialized with every dataset
  version and must reload consistently.
- Chain methods return a new chain and must not mutate the receiver; chains are
  reused in later code.
- There is no single mapping chokepoint. Similar-looking code paths can drift.

## Mapping Paths to Audit

For every signal→column, type-conversion, hidden-field, nullability, or nested
model change, enumerate these paths explicitly:

| Path | What to verify |
| --- | --- |
| Ingestion from readers | `read_storage`, `read_values`, `read_records`, CSV/JSON/Parquet/database/HF/Zarr readers produce expected logical schema and stored values. |
| UDF outputs | `map`, `gen`, `agg`, batched/parallel UDFs, multi-output UDFs, setup values, and Pydantic model outputs store and hydrate correctly. |
| Query operations | `filter`, `select`, `select_except`, `mutate`, `merge`, `group_by`, `aggregate`, `distinct`, `union`, `subtract`, `diff`, `window`, and composed expressions preserve schema and values. |
| Object hydration | `to_values`, `to_list`, `results`, and object-returning reads rebuild Python values correctly. |
| Flat exports | `to_pandas`, `to_parquet`, `to_csv`, `to_json`, `to_jsonl`, `to_records`, `to_database`, and `to_storage` flatten names consistently and omit internal/hidden fields when required. |
| Dataset serialization | Save, reload, version range selection, schema metadata, SQL types, non-importable models, and backward-compatible reads. |
| Backend conversion | SQLite local, ClickHouse/Studio, and any selected future backend converters agree where they are supposed to, and document real limitations where they cannot. |

## Backend Divergence Checklist

| Axis | Local/SQLite behavior | Backend risk |
| --- | --- | --- |
| Nullability | SQLite is permissive and can store `NaN` as `NULL`. | ClickHouse is not-null by default and uses explicit `Nullable(T)`. Derived expressions over nullable inputs must remain nullable. |
| NaN vs None | SQLite may read optional float `NaN` as `None`. | Other backends usually preserve IEEE NaN separately from null. Do not force all backends to mimic SQLite. |
| Collections | Local behavior may distinguish empty and `None`. | ClickHouse and BigQuery cannot represent nullable arrays/maps cleanly; optional collections may collapse to empty. |
| Hash/regex/RNG | Backend-local implementations may differ. | Do not compare hash/RNG outputs across backends or assume regex dialect edge cases match. |
| Join/filter expression semantics | SQLite may accept coercions a stricter backend rejects. | Verify expression read-back on the strict backend when correctness depends on type or null behavior. |
| Export naming | Local flat export may appear unique. | Hidden/internal columns and flattened names must remain unique across all export paths. |

## Composition Axes for Tests

When testing a new signal type, nullability change, flattening change, or
backend-sensitive expression, include adversarial compositions:

- signal as the only user signal in the chain;
- nested field, whole model, subclass, two models with the same class name in
  different modules, and an invalid value that must error rather than drop;
- all-null, all-empty, single-row, mixed-null, and present-only-on-one-join-side
  inputs;
- `filter`, `order_by`, `mutate`, `group_by`, aggregates over null rows,
  `distinct`, `merge` on the signal and carried through a join, `subtract`, and
  `window` using both readable names and slot forms;
- `union` in both arm orders, because it is not symmetric;
- `.label()` / aliases and a leaf inside a composed `Func`, not only a bare leaf;
- every export path separately: pandas, parquet, CSV, JSON/JSONL, records,
  database, and storage;
- UDF shapes: generator, aggregator, batched, multi-output, and cross-process
  clone/serialize;
- special signal types such as `File`, not only plain Pydantic models;
- reloading a dataset saved before the change, including cases where the
  referenced Python type is not importable.

## Permanent Test Rule

A probe is not done. For each affected matrix cell:

1. create or extend a permanent pytest test;
2. assert read-back values, not only declared schema;
3. parameterize over backend(s) where the backend is part of the claim;
4. isolate suspected backend crashes from harness load artifacts by rerunning the
   smallest reproducer alone;
5. document explicit limitations instead of silently weakening the contract.

## Practical Workflow

1. Identify the logical schema operation and every physical column path it
   touches.
2. Search for parallel mapping code in readers, UDF flattening, query schema,
   export code, storage serializers, and SQL backend converters.
3. Write the matrix before coding; tick cells only when a permanent test reads
   values back.
4. Run focused tests locally first, then strict/remote backend tests when the
   changed behavior depends on them.
5. If another repository owns a backend converter, coordinate that change before
   claiming end-to-end support.

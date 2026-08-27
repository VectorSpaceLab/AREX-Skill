# Query Engine Troubleshooting

## Purpose

Use this when a DataChain query fails, produces a surprising schema, or works on
local SQLite but is uncertain on a stricter backend. Start with the symptom,
then choose the smallest diagnostic that preserves the user's chain laziness and
backend constraints.

## Missing Columns and Bad Field Paths

**Symptoms**

- `SignalResolvingError` with text like `cannot resolve signal name 'x': is not found`.
- `KeyError` or a backend SQL error mentioning a missing physical column.
- A nested field such as `"file.path"` works in one API but `"file__path"` fails
  in another.

**Likely causes**

- Dot-path vs physical `__` path confusion.
- The current chain has already `select`ed or `select_except`ed away the field.
- A nested selection created a partial model, so sibling leaves are no longer in
  the logical schema.
- A merge/union renamed or rejected conflicting fields.

**Recovery**

1. Inspect logical fields with `chain.signals_schema.user_signals()`.
2. Use dot paths in public APIs: `"parent.leaf"`, `dc.C("parent.leaf")`.
3. Use `chain.signals_schema.db_signals()` only when debugging the physical SQL
   layer.
4. If a partial selection caused the gap, move `select` later or include all
   leaves needed by downstream filters, functions, or joins.
5. For a minimal schema demo independent of user data, run
   [schema_probe.py](../scripts/schema_probe.py).

## Expression Type Inference Failures

**Symptoms**

- `DataChainColumnError` saying DataChain cannot infer a type for an expression.
- `A dataset context is required to infer result type` or `infer column type`.
- Errors around `NullType`, unsupported operand values, or invalid function
  operands.

**Likely causes**

- Calling `Func.get_result_type()` / `get_column()` without a schema context for
  a column-dependent function.
- Using a raw SQLAlchemy expression whose columns were not typed by the current
  `SignalSchema`.
- Combining incompatible operand types or using unsupported Python objects inside
  SQL expressions.
- Passing strings as branch values where a column expression was intended.

**Recovery**

1. Build expressions from `dc.C("field")`, `dc.Column("field")`, or
   `dc.func.*` inside a chain method so DataChain can enrich types from schema.
2. Use `dc.func.cast(expr, target_type)` when a conversion is intended.
3. Keep SQL function arguments scalar/list/dict leaves, not entire DataModels.
4. In `case` / `ifelse`, string branch values are literals. Use `dc.C("field")`
   when the branch should return a column value.
5. Reduce a failing expression to a tiny `read_values` fixture and compare it to
   [query_smoke.py](../scripts/query_smoke.py).

## `mutate` vs `map` Confusion

**Symptoms**

- `mutate` rejects a lambda/callable.
- A user expects `mutate` to read file content, call a model, or execute Python
  code per row.
- Derived signals are unexpectedly limited to existing columns and SQL functions.

**Likely cause**

`mutate` is a native Query Engine operation. It accepts literals, `Column`,
`ColumnExpr`, and `Func` expressions, not Python callables.

**Recovery**

- Use `mutate` for column arithmetic, comparisons, path/string functions,
  conditionals, vector distances, and window expressions.
- Reroute Python callables, file reads, model calls, multi-output UDFs, or custom
  object construction to sibling sub-skill `sdk-pipelines`.
- If all you need is a rename, `mutate(new_name=dc.Column("old_name"))` can
  rename a top-level signal. Do not try to create new nested columns directly.

## Label, Alias, and Name Collision Issues

**Symptoms**

- Positional expression errors in `mutate` or `group_by`.
- Generated columns named `gr_0`, `gr_1`, etc.
- `partition_by name 'x' conflicts with aggregation column name`.
- Right-side merge columns unexpectedly prefixed with `right_` or `right_1`.

**Likely causes**

- DataChain requires keyword output names for expression-producing APIs.
- An expression partition lacked `.label(...)`.
- A partition output name collided with an aggregate output name.
- Merge protects existing roots by prefixing conflicting right-side fields.

**Recovery**

1. Name outputs with keyword arguments: `mutate(score2=...)`,
   `group_by(total=dc.func.sum("score"), partition_by=...)`.
2. Label function or expression partitions when their output name matters:
   `partition_by=dc.func.path.file_ext("path").label("ext")`.
3. Keep aggregate output names distinct from partition names.
4. Set `rname="some_prefix_"` in `merge` when the default right prefix would be
   confusing, and inspect the resulting logical signals before downstream code.

## Complex Object in SQL Functions

**Symptoms**

- Error text like `Function min doesn't support complex object columns`.
- `collect("rec")`, `min("rec")`, or a scalar function over an entire DataModel
  fails.

**Likely cause**

SQL functions operate over physical scalar/list/dict leaves. A whole DataModel
has no single scalar SQL column.

**Recovery**

- Use a leaf field: `dc.func.min("rec.score")`, `dc.func.collect("rec.label")`.
- For operations that require the whole Python object, use `map`, `gen`, or UDF
  aggregation guidance from `sdk-pipelines`.
- If the object is optional, include absent/present edge cases and verify
  read-back values, not just schema.

## Delta Restrictions with Non-Local Operations

**Symptoms**

- `NotImplementedError` mentioning `Cannot use <operation> with delta datasets`
  and `delta_unsafe=True`.
- A delta-enabled chain fails when using `agg`, `distinct`, `group_by`, `merge`,
  `union`, `subtract`, `diff`, or `file_diff`.

**Likely cause**

Those operations can combine or summarize rows in ways that break safe delta
replay unless every participating delta source explicitly opts into unsafe
behavior.

**Recovery**

1. Do not set `delta_unsafe=True` casually. It is an informed consistency tradeoff.
2. If the workflow can be expressed as safe per-row filtering, selection, or
   mutation before the delta boundary, do that first.
3. Otherwise reroute to `sdk-pipelines` for delta/retry pipeline design and make
   the consistency risk visible to the user.

## Merge, Union, Subtract, and Diff Mismatches

**Symptoms**

- `Cannot perform union... only present in left/right`.
- Merge errors saying `on` / `right_on` cannot resolve or lengths differ.
- `subtract(): no common columns` or `right_on` provided without `on`.
- Diff results miss expected changes or show unexpected `A`, `D`, `M`, `S` statuses.

**Likely causes**

- `union` requires matching user-visible schemas. Column order is aligned, but
  missing or extra signals are rejected.
- `merge` predicates must resolve on the correct side; `right_on` must match the
  arity of `on`.
- `subtract` defaults to common columns only when `on` / `right_on` are omitted.
- `diff` comparison columns may be too broad, too narrow, or mismatched between
  sides.

**Recovery**

1. Compare `left.signals_schema.user_signals()` and
   `right.signals_schema.user_signals()` before `union`.
2. Normalize both sides with `select(...)` / `select_except(...)` / compatible
   `mutate(...)` before unioning.
3. For `merge`, write explicit `on` and `right_on` when column names differ, and
   prefer leaf paths for complex signals.
4. For `subtract`, provide explicit `on` / `right_on` when common-column behavior
   is ambiguous.
5. For `diff`, provide explicit `compare` / `right_compare` and request
   `status_col` when the caller needs to distinguish added, deleted, modified,
   and same rows.

## Backend-Specific Failures

**Symptoms**

- A query passes locally but differs in Studio / ClickHouse or another backend.
- Vector distance functions raise a missing SQL vector dependency error.
- Regex, hash, random, null ordering, or `NaN` results differ by backend.
- A full/outer join or union involving optional values reads back differently
  from the declared schema.

**Likely causes**

- Local SQLite is permissive and can mask stricter backend behavior.
- ClickHouse requires explicit nullable types; derived expressions over nullable
  inputs must remain nullable.
- SQLite stores `NaN` as `NULL`; most other backends keep `NaN` distinct.
- ClickHouse and BigQuery cannot represent nullable collections like nullable
  scalars.
- Hash functions, regex dialects, and RNG are backend-local.
- Local vector distance execution may need DataChain's vector optional extra.

**Recovery**

1. Do not generalize from local SQLite alone. State the backend actually tested.
2. Verify actual read-back values on the target backend, especially for null,
   `NaN`, collection, join-padding, union, and window cases.
3. Avoid relying on exact hash/random/regex edge-case equality across engines.
4. If vector functions are unavailable locally, install the vector optional extra
   or run the query on a backend with vector support.
5. For schema-sensitive changes, enumerate the affected operation matrix before
   claiming the bug is fixed.

## Fast Triage Flow

1. **Can the operation be native?** If yes, stay in this sub-skill; if it needs
   Python/file/model logic, reroute to `sdk-pipelines`.
2. **Does the current schema contain the referenced fields?** Check logical
   signals first, then physical columns only if debugging internals.
3. **Are all expressions typed?** Prefer `dc.C`, `dc.func`, keywords, labels, and
   `cast` over raw untyped SQL fragments.
4. **Does the operation combine rows or chains?** For `group_by`, `merge`,
   `union`, `subtract`, or `diff`, compare schemas and nullability explicitly.
5. **Is the claim backend-sensitive?** If yes, local smoke checks are not enough;
   require target-backend read-back evidence or document the uncertainty.

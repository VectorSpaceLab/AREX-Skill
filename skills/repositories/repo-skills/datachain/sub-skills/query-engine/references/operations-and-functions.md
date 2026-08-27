# Query Operations and Function Expressions

## Purpose

Read this when choosing a DataChain Query Engine operation, composing
`datachain.func` expressions, debugging `mutate` / `group_by` / window behavior,
or ranking vectors. The examples use tiny `read_values` fixtures only so the
patterns are copyable without external data.

## Native Query Engine vs Python UDF

Use native Query Engine operations when the transformation can be expressed from
existing columns with comparisons, arithmetic, SQL-style functions, joins,
projection, grouping, or ordering. Native operations execute in the warehouse;
they do not spin up a Python runtime for each row and do not read file contents.

Use Python UDF workflows (`map`, `gen`, or UDF aggregation) only when the task
needs Python callables, file bytes/text/images, model inference, network/API
calls, arbitrary objects, or logic that is not expressible with `dc.C(...)`,
`ColumnExpr`, and `dc.func`.

```python
import datachain as dc

chain = dc.read_values(
    path=["a/cat.jpg", "b/dog.png", "notes.txt"],
    score=[0.93, 0.81, 0.10],
    grp=["image", "image", "text"],
)

# Native: all derived columns and filters run in the Query Engine.
rankable = (
    chain
    .mutate(
        ext=dc.func.path.file_ext("path"),
        score_pct=dc.C("score") * 100,
        label=dc.func.ifelse(dc.C("score") >= 0.9, "high", "review"),
    )
    .filter(dc.C("score_pct") > 50)
    .order_by("score_pct", descending=True)
)
```

## Operation Catalog

Every operation below returns a new chain.

| Operation | Use it for | Notes and gotchas |
| --- | --- | --- |
| `filter(*conditions)` | Keep rows matching SQL-style boolean expressions. | Multiple conditions are combined as an AND-style filter. Combine expressions explicitly with `&`, `|`, `~`, or `dc.func.and_` / `or_` / `not_` when precedence matters. |
| `select(*signals, **exprs)` | Keep named signals or create expression aliases and keep them. | Nested selections such as `"response.usage.prompt_tokens"` preserve the parent object through a partial model. Keyword expressions are first added like `mutate`, then selected. |
| `select_except(*signals)` | Drop named top-level or nested signals. | Nested exclusions create partial models for the remaining leaves. No arguments returns the same chain. |
| `order_by(*cols, descending=False)` | Sort before `limit`, `offset`, display, export, or assertion. | If a chain is unordered, `limit` / `offset` pick undefined rows. Nullable columns are ordered with explicit `NULLS LAST` where DataChain can identify them. |
| `distinct(*signals_or_exprs, **exprs)` | Deduplicate by one or more signals or named expressions. | The DataChain API expects at least one signal/expression; expression keyword arguments are first materialized. |
| `group_by(..., partition_by=..., **aggregates)` | Aggregate rows by zero or more partitions. | Aggregates must be keyword `Func` values. `partition_by` accepts a string, `Func`, `ColumnExpr`, or sequence. At least one aggregate is required. |
| `mutate(**exprs)` | Add, replace, or rename signals using native literals, columns, funcs, or column expressions. | Does not accept lambdas or callables. Use `map` for Python. A top-level `Column("old")` rename drops the old signal; nested leaves are kept to preserve object integrity. |
| `merge(right, on, right_on=None, inner=False, full=False, rname="right_")` | Join two chains. | `on` / `right_on` can be strings, functions, expressions, or sequences of matching length. Conflicting right signal roots are prefixed with `rname`; sys signals are not carried through. |
| `union(other)` / `left | right` | Vertically concatenate chains. | User-visible schemas must match. Optional scalar/model widening is handled for matching schemas, but validate both arm orders for backend-sensitive changes. |
| `subtract(other, on=None, right_on=None)` | Remove rows in another chain. | Without `on`, DataChain uses common columns and errors when no common columns exist. `right_on` requires `on` and equal arity. |
| `diff(other, on, ...)` | Compare chains and return added/deleted/modified/same rows. | `status_col` stores `A`, `D`, `M`, `S` when requested. `compare` defaults to comparable columns. |
| `file_diff(other, on="file", ...)` | File-level change detection. | Matches file `source` and `path`; compares file `version` and `etag`. Useful for incremental file listings. |
| `similarity_search(column, query, k=10, metric="cosine", score_column=None)` | Rank vector rows by distance. | Shortcut for distance `mutate` + `order_by` + optional `limit`. Metrics: `"cosine"`, `"euclidean"`, and `"l2"` (alias for Euclidean). |
| `limit(n)` / `offset(n)` | Page ordered results. | Apply an explicit `order_by` first when row identity matters. |
| `shuffle()` / `sample(n)` | Randomize or sample rows. | `shuffle` orders by regenerated `sys.rand`; `sample` is not deterministic and can sample with replacement in streamed/paginated or multi-worker contexts. |
| `count()`, `sum(col)`, `avg(col)`, `min(col)`, `max(col)` | Terminal aggregate values. | Use dot paths for nested leaves, e.g. `"response.usage.prompt_tokens"`; these return Python values rather than chains. |

## Column and Expression Basics

- Prefer user-facing dot paths in public examples: `"file.path"`,
  `dc.C("file.path")`, or `dc.Column("file.path")`.
- `dc.C("a.b")` and `dc.Column("a.b")` create physical column references for
  `a__b`. Use these for arithmetic, comparisons, SQL pattern operators, and
  labelable expressions.
- `Column` supports SQLAlchemy expression methods plus DataChain helpers such as
  `.glob(pattern)` and `.regexp(pattern)`. `like` and `ilike` are available via
  the SQL expression interface.
- `Func.label("alias")` controls the output alias when a function is selected,
  mutated, or used as a `group_by(partition_by=...)` expression.
- Use keyword arguments for named expression APIs. Positional `Func` / expression
  arguments in `mutate` and aggregate outputs are rejected to avoid ambiguous
  output names.

## `mutate` Patterns

```python
import datachain as dc
from datachain import func

chain = dc.read_values(
    path=["imgs/cat.jpg", "imgs/dog.png", "notes/readme.txt"],
    score=[0.95, 0.72, 0.31],
    count=[3, 2, 1],
)

derived = chain.mutate(
    ext=func.path.file_ext("path"),
    parent=func.path.parent("path"),
    weighted=dc.C("score") * dc.C("count"),
    is_image=dc.C("path").regexp(r"(?i)\.(jpg|png)$"),
    label=func.case(
        (dc.C("score") >= 0.9, "high"),
        (dc.C("score") >= 0.5, "medium"),
        else_="low",
    ),
)
```

Remember:

- literals may be `bool`, `str`, `int`, or `float`;
- `Func` and `ColumnExpr` values are type-enriched against the current schema;
- creating a new nested path directly, such as `mutate("obj.new_leaf"=...)`, is
  not allowed; create a top-level signal or use a Python DataModel-producing UDF;
- a `Column("old")` value renames a top-level signal and drops the old one, but
  renaming a nested leaf keeps the original parent object intact.

## `group_by` Patterns

```python
import datachain as dc
from datachain import func

chain = dc.read_values(
    path=["a/cat.jpg", "b/dog.jpg", "c/readme.txt", "d/cat.jpg"],
    bytes=[10, 20, 5, 30],
)

by_ext = (
    chain
    .group_by(
        files=func.count(),
        total_bytes=func.sum("bytes"),
        avg_bytes=func.avg("bytes"),
        partition_by=func.path.file_ext("path").label("ext"),
    )
    .order_by("total_bytes", descending=True)
)
```

Rules that matter in bug reports:

- `group_by` does not accept positional output expressions. Put aggregate outputs
  in keyword arguments.
- `partition_by` may be a single value or a sequence of strings/functions/column
  expressions. Unlabeled expression partitions receive generated names such as
  `gr_0`; label them when the result needs a stable field name.
- If `partition_by` names a complex signal, DataChain expands its physical leaf
  columns. If it names a nested leaf, the resulting logical schema may contain a
  partial model for just the selected subtree.
- Supported aggregate families include `count`, `sum`, `avg`, `min`, `max`,
  `any_value`, `collect`, `concat`, and the hash/fingerprint-oriented `xor_agg`.

## Window Functions

Window functions run inside `mutate`; they require `over(func.window(...))`.

```python
import datachain as dc
from datachain import func

chain = dc.read_values(
    item=["a", "b", "c", "d"],
    grp=["x", "x", "y", "y"],
    score=[10, 30, 5, 15],
)

w = func.window(partition_by="grp", order_by="score", desc=True)
ranked = chain.mutate(
    row_in_group=func.row_number().over(w),
    rank_in_group=func.rank().over(w),
    dense_rank_in_group=func.dense_rank().over(w),
    top_item=func.first("item").over(w),
)
```

Notes:

- `func.window(partition_by=..., order_by=..., desc=False)` accepts strings or
  expressions; string paths are converted to physical column names.
- `row_number`, `rank`, `dense_rank`, and `first` are the main window helpers.
- Window ordering applies `NULLS LAST` so local SQLite ordering better matches
  stricter backends, but backend parity still requires backend evidence.
- If a window function lacks `.over(window_spec)`, DataChain raises a parameter
  error.

## Function Families

Access functions via `dc.func` after `import datachain as dc`. Only a subset is
exported directly from `dc.func`; use module namespaces for clarity when names
can collide.

| Family | Common functions | Typical use |
| --- | --- | --- |
| Aggregate | `count`, `sum`, `avg`, `min`, `max`, `any_value`, `collect`, `concat`, `xor_agg` | `group_by` outputs and terminal aggregate methods. |
| Array | `array.length`, `array.contains`, `array.slice`, `array.join`, `array.get_element`, `cosine_distance`, `euclidean_distance`, `sip_hash_64` | List/array analytics and vector distances. Direct `func.length` is array-oriented; use `func.string.length` for strings. |
| Conditional | `case`, `ifelse`, `isnone`, `and_`, `or_`, `not_`, `greatest`, `least` | Branching, null checks, and boolean expression composition. |
| Numeric / bit | `bit_and`, `bit_or`, `bit_xor`, `bit_hamming_distance`, `int_hash_64` | Bitwise features, fingerprints, and integer-distance logic. |
| String | `string.length`, `string.split`, `string.replace`, `string.regexp_replace`, `byte_hamming_distance`, `string_hash` | Text cleanup and string metrics. Regex behavior is backend-local; test edge cases on the target backend. |
| Path | `path.parent`, `path.name`, `path.file_stem`, `path.file_ext` | POSIX-style path parsing from string columns. |
| Random | `rand` | Randomized derived values. RNG is backend-local; do not compare exact values across backends. |
| Window | `window`, `row_number`, `rank`, `dense_rank`, `first` | Partitioned analytics without materializing in Python. |
| Conversion | `cast(col, type_)` | Cast column/expression values to Python target types such as `int`, `float`, `str`, `bool`, `bytes`, or `datetime`. |

Conditional string literals inside `case` / `ifelse` are treated as literal
values. If the branch result should be another column, pass `dc.C("column")`.

## Path, String, and Conditional Example

```python
import datachain as dc
from datachain.func import string

chain = dc.read_values(
    path=["images/CAT_001.JPG", "images/dog_002.png", "notes/todo.txt"],
    score=[0.97, 0.61, 0.20],
)

clean = chain.mutate(
    ext=dc.func.path.file_ext("path"),
    stem=dc.func.path.file_stem("path"),
    parent=dc.func.path.parent("path"),
    lowerish=string.regexp_replace("path", r"(?i)cat", "cat"),
    bucket=dc.func.case(
        (dc.C("score") >= 0.9, "accept"),
        (dc.C("score") >= 0.5, "review"),
        else_="reject",
    ),
)
```

## Vector Distance Pattern

Embedding generation usually belongs to Python UDF or ML pipeline guidance; the
Query Engine owns the distance/ranking step once embeddings are already stored
as list-valued columns.

```python
import datachain as dc

query_embedding = [1.0, 0.0, 0.0]

# Explicit distance pattern.
top = (
    chain
    .mutate(dist=dc.func.cosine_distance("embedding", query_embedding))
    .order_by("dist")
    .limit(10)
    .select("id", "dist")
)

# Equivalent convenience API with selectable metric and optional score output.
top = chain.similarity_search(
    "embedding",
    query_embedding,
    k=10,
    metric="cosine",
    score_column="dist",
)
```

Use `metric="euclidean"` for Euclidean distance; `metric="l2"` is accepted by
`similarity_search` as an alias for Euclidean. Current public function exports
include `cosine_distance` and `euclidean_distance`; inspect the installed package
before relying on older recipes that mention a separate `l2_distance` function.

Local vector execution may require the package's vector optional dependencies.
If a query raises a missing SQL vector function error, install the vector extra
or run on a backend that provides the required function support.

## Minimal Local Diagnostics

- Run [query_smoke.py](../scripts/query_smoke.py) to verify that an installed
  DataChain package can execute a tiny `read_values` → `mutate` → `filter` →
  `group_by` → `order_by` chain.
- Run [schema_probe.py](../scripts/schema_probe.py) to inspect how a tiny nested
  `DataModel` maps from logical dot paths to physical `__` columns.

# Hail Table and Expression API Reference

This compact reference focuses on common row-indexed `Table` work. Verified installed facts identify Hail distribution `0.2.138` and confirm the public `hl.import_table` and `hl.read_table` signatures shown here.

## Import and Read

### `hl.import_table`

```python
hl.import_table(
    paths,
    key=None,
    min_partitions=None,
    impute=False,
    no_header=False,
    comment=(),
    delimiter="\t",
    missing="NA",
    types={},
    quote=None,
    skip_blank_lines=False,
    force_bgz=False,
    filter=None,
    find_replace=None,
    force=False,
    source_file_field=None,
) -> Table
```

Common patterns:

```python
ht = hl.import_table("input.tsv.bgz", types={"id": hl.tstr, "x": hl.tfloat64})
ht = hl.import_table("input.csv", delimiter=",", missing=".", quote='"')
ht = hl.import_table("headerless.tsv", no_header=True)
ht = hl.import_table(["part1.tsv", "part2.tsv"], source_file_field="source_file")
```

Notes:

- Default imported field type is `str` unless `types` or `impute=True` changes it.
- `impute=True` parses input twice and inferred types should be reviewed.
- `key=` can key imported data, but many pipelines use `key_by` after cleaning names and types.
- `missing` is the text token that represents missing data, not a Hail expression.

### `hl.read_table`

```python
hl.read_table(
    path,
    *,
    _intervals=None,
    _filter_intervals=False,
    _n_partitions=None,
    _assert_type=None,
    _load_refs=True,
    _create_row_uids=False,
) -> Table
```

Use plain `hl.read_table(path)` for native Hail Table data unless deliberately working with advanced interval or partition internals.

## Table Inspection and Preview

```python
ht.describe()          # prints globals, row fields, and key
ht.row.dtype           # row struct type
ht.globals.dtype       # global struct type
ht.key                 # key struct expression
ht.count()             # local row count
ht.head(10)            # smaller Table with first rows
ht.show(n=10)          # prints first rows
ht.take(5)             # local list of row Struct values
```

Preview safely:

```python
ht.head(5).show(width=120, truncate=80)
rows = ht.select("id", "status").take(3)
```

Avoid large `take`, `collect`, `show`, `to_pandas`, or unbounded `hl.agg.collect` on large data.

## Field Access and Structs

```python
ht.id                  # valid identifier-like field names
ht["sample-id"]        # spaces, punctuation, dots, hyphens, and method-name collisions
ht.row                 # row StructExpression
ht.row_value           # row fields excluding key fields
```

Struct operations:

```python
ht = ht.annotate(meta=hl.struct(source="study1", batch=ht.batch))
ht = ht.annotate(meta=ht.meta.annotate(pass_qc=ht.score > 0))
ht = ht.annotate(meta=ht.meta.drop("batch"))
ht = ht.select(id=ht.id, pass_qc=ht.meta.pass_qc)
```

Local row structs from `take` support both access styles:

```python
row = ht.take(1)[0]
row.id
row["sample-id"]
```

## Row Transformations

### `Table.annotate`

```python
ht = ht.annotate(new_field=expression, other_field=expression)
```

Adds or replaces row fields. Annotation expressions should be row-indexed by the current table, globals, scalar expressions, or valid joins/lookups. Do not reuse field expressions from an old table object after rebinding transformations.

### `Table.filter`

```python
ht = ht.filter(predicate)
ht = ht.filter(predicate, keep=False)
```

`predicate` must be a Boolean Hail expression. Filtering keyed native tables by key fields can be optimized; filtering text imports or filtering after reshuffling operations usually reads more data.

### `Table.select`

```python
ht = ht.select("field_a", "field_b", renamed=ht.old_name, computed=ht.x + 1)
```

Keeps selected row fields and computed fields. Key fields are preserved automatically. Complex expressions must be keyword arguments:

```python
ht.select(score2=ht.score * 2)  # correct
```

### Related Selection Methods

```python
ht = ht.drop("field_a", "field_b")
ht = ht.transmute(new=ht.x + ht.y)   # add new field and drop referenced non-key fields
ht = ht.rename({"old": "new"})
ht = ht.flatten()                    # flatten nested structs into top-level fields
```

Check `ht.key` after reshaping methods when key state matters.

## Keys and Joins

### `Table.key_by`

```python
ht = ht.key_by("id")
ht = ht.key_by("id", "visit")
ht = ht.key_by(clean_id=ht.raw_id.replace(" ", "_"))
ht = ht.key_by()  # remove key
```

Rules:

- Positional arguments are field names or top-level field expressions.
- Computed keys need keyword syntax.
- Changing keys sorts by the new key and can be expensive.
- Key order and Hail types matter for joins and indexing.

### `Table.join`

```python
joined = left.join(right, how="inner")
joined = left.join(right, how="left")
joined = left.join(right, how="right")
joined = left.join(right, how="outer")
```

Rules:

- Both sides must be keyed with the same number of key fields and corresponding key types.
- Key names may differ; key order and types must match.
- Left key fields are preserved; right key fields are omitted.
- Right non-key field conflicts are renamed with unique suffixes.
- Duplicate keys can produce more output rows than either input.
- Missing key values never match.

### Bracket Index and `Table.index`

Preferred shorthand:

```python
lookup = lookup.key_by("id")
ht = ht.key_by("id")
ht = ht.annotate(extra=lookup[ht.key].extra)
ht = ht.annotate(extra=lookup[ht.id].extra)
```

Explicit form:

```python
row_value_expr = lookup.index(ht.id)
ht = ht.annotate(extra=row_value_expr.extra)
```

Rules:

- Index arguments must be Hail expressions, not Python literals.
- Scalar expressions cannot index a table; the index expression must come from a table or matrix axis.
- Index expression types must match the lookup table key types, except supported prefix and interval behavior.
- The result is a `StructExpression` containing row-value fields, not a `Table`.
- Missing or unmatched keys produce missing lookup fields.
- `all_matches=True` is experimental and returns arrays of matches for interval-style uses.

## Aggregation

### `Table.aggregate`

```python
result = ht.aggregate(hl.struct(
    n=hl.agg.count(),
    mean_x=hl.agg.mean(ht.x),
    n_positive=hl.agg.count_where(ht.x > 0),
))
```

Returns a local Python value and supports aggregation over table rows.

### `Table.group_by(...).aggregate(...)`

```python
result_ht = (
    ht.group_by(group=ht.status)
      .aggregate(n=hl.agg.count(), mean_x=hl.agg.mean(ht.x))
)
```

Returns a keyed `Table` grouped by the group fields.

### Common `hl.agg` Helpers

```python
hl.agg.count()
hl.agg.count_where(predicate)
hl.agg.fraction(predicate)
hl.agg.mean(expr)
hl.agg.sum(expr)
hl.agg.min(expr)
hl.agg.max(expr)
hl.agg.stats(expr)
hl.agg.counter(expr)
hl.agg.filter(condition, aggregator)
hl.agg.take(expr, n, ordering=optional_expr)
hl.agg.group_by(group_expr, aggregator)
```

Keep local aggregation results bounded. Prefer grouped tables over collecting large Python dictionaries when group cardinality may be high.

## Missingness and Expression Helpers

```python
hl.is_defined(expr)
hl.is_missing(expr)
hl.missing(hl.tint32)
hl.coalesce(expr, fallback)
hl.or_else(expr, fallback)
hl.or_missing(predicate, value)
hl.if_else(predicate, consequent, alternate, missing_false=False)
hl.case(missing_false=False).when(predicate, value).default(fallback)
hl.switch(expr).when(value, result).default(fallback)
hl.literal({"case": 1, "control": 0})
hl.struct(field=value, nested=other_value)
```

Missing predicates usually propagate missingness. Use `missing_false=True`, `hl.coalesce`, or explicit `hl.is_defined` checks when missing should behave as false or as a fallback value.

## Write and Export

### `Table.write`

```python
ht.write("prepared.ht", overwrite=True)
```

Writes native Hail Table format for later `hl.read_table`. Use this for cached intermediates and reusable Hail data.

### `Table.export`

```python
ht.export("output.tsv.bgz", delimiter="\t", header=True)
```

Exports text. Large text exports should use a `.bgz` output name. Nested structures are exported as JSON; use `flatten()` or select nested values into top-level fields when needed.

### Expression Export

```python
ht.score.export("scores.tsv.bgz")
```

`Expression.export` is useful for one row field or a selected expression. For whole tables, prefer `Table.export`.

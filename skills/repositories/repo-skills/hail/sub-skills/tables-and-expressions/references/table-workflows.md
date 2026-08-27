# Hail Table Workflows

This reference covers row-indexed `Table` pipelines and expression basics. It deliberately excludes MatrixTable, VDS, backend setup, Batch orchestration, and cloud CLI operations.

## Import and Schema Triage

Use `hl.import_table` for TSV, CSV, and other delimited text data.

```python
import hail as hl

ht = hl.import_table(
    "samples.tsv.bgz",
    delimiter="\t",
    missing="NA",
    impute=False,
    types={"sample_id": hl.tstr, "age": hl.tint32, "score": hl.tfloat64},
)
```

First checks after import:

```python
ht.describe()
print(ht.row.dtype)
print(ht.globals.dtype)
print(ht.key)
ht.head(5).show(width=120, truncate=80)
```

Use explicit `types` for production pipelines. `impute=True` is useful for exploration, but it parses text twice and may turn identifiers with leading zeroes into numbers.

Common import options:

- CSV: `delimiter=","` and often `quote='"'`.
- Headerless data: `no_header=True`, then rename generated fields such as `f0`, `f1` with `select` or `rename`.
- Alternate missing token: `missing="."`, `missing=""`, or the observed token.
- Comments: `comment=("#",)`.
- Multiple files: pass a list of paths; add `source_file_field="source_file"` when provenance matters.
- Odd field names: use `ht["sample id"]`, `ht["case.status"]`, or `ht["PT-ID"]`, not dot access.

Example headerless repair:

```python
ht = hl.import_table("samples.tsv", no_header=True, missing=".")
ht = ht.select(
    sample_id=ht.f0,
    phenotype=ht.f1,
    score=hl.float64(ht.f2),
).key_by("sample_id")
```

Use `hl.read_table` for a native Hail Table written by `Table.write` or `checkpoint`:

```python
ht = hl.read_table("prepared_samples.ht")
```

Native reads preserve schema, key metadata, partitioning metadata, and reference genome metadata when present. Filtering a keyed native table by key fields can avoid reading unrelated partitions; re-keying or grouping before filtering can block that optimization.

## Row Expressions

A Hail expression is lazy and carries a Hail type plus source/index information. A row field such as `ht.score` is indexed by rows of that exact table.

```python
ht = ht.annotate(
    score_z=(ht.score - 10.0) / 2.5,
    is_case=ht["case.status"] == "case",
    score_bucket=(
        hl.case()
        .when(ht.score < 0, "low")
        .when(ht.score < 10, "mid")
        .default("high")
    ),
)
```

Rules that prevent common expression bugs:

- Use `&`, `|`, and `~` instead of Python `and`, `or`, and `not`.
- Parenthesize comparisons: `(ht.age >= 18) & (ht.is_case)`.
- Use `hl.if_else`, `hl.case`, or `hl.switch`; Python `if` cannot branch on a Hail expression.
- Missing values propagate through most expressions; use `hl.is_defined`, `hl.is_missing`, `hl.or_missing`, `hl.coalesce`, or `missing_false=True` intentionally.
- Use `hl.literal` for small Python lookup dictionaries or arrays, then index with a table expression.

```python
status_map = hl.literal({"case": 1, "control": 0})
ht = ht.annotate(status_code=status_map.get(ht["case.status"], -1))
```

## Selecting, Annotating, and Struct Fields

Use `annotate` to add or update row fields; use `select` to keep a focused set of fields. `select` preserves key fields. Use `key_by` to change keys.

```python
ht = ht.annotate(
    qc=hl.struct(
        has_age=hl.is_defined(ht.age),
        nonnegative_score=ht.score >= 0,
    )
)

ht = ht.select(
    "sample_id",
    "age",
    score=ht.score,
    qc=ht.qc,
)
```

Nested `Struct` fields are updated by transforming the struct expression and assigning it back:

```python
ht = ht.annotate(qc=ht.qc.annotate(pass_qc=ht.qc.has_age & ht.qc.nonnegative_score))
ht = ht.annotate(qc=ht.qc.drop("nonnegative_score"))
```

Local rows returned by `take` are `Struct` values:

```python
rows = ht.select("sample_id", "case.status").take(3)
first_id = rows[0].sample_id
first_status = rows[0]["case.status"]
```

## Keys and Joins

### Choose Keys Explicitly

Imported tables are unkeyed unless `key=` is supplied or `key_by` is called. Most join and lookup patterns require keys.

```python
left = left.key_by("sample_id")
right = right.key_by("sample_id")
print(left.key)
print(right.key)
```

Compound key order matters. A table keyed by `("sample_id", "visit")` does not match a table keyed by `("visit", "sample_id")` unless re-keyed. `key_by` sorts by the new key and can be expensive on large data, so avoid repeated key changes.

### `Table.join`

Use `Table.join` when the output should include row fields from both keyed tables.

```python
joined = left.join(right, how="left")
```

Join semantics:

- `inner`: only matching keys.
- `left`: all left rows; right fields are missing when no match exists.
- `right`: all right rows; left fields are missing when no match exists.
- `outer`: all keys from either side; fields from the absent side are missing.
- Missing key values never match.
- Duplicate keys produce a Cartesian product and can increase row count.
- Right-side non-key fields with overlapping names are automatically renamed with unique suffixes such as `_1`.

Rename or select right-side fields before joining when names overlap:

```python
right = right.select(
    annotation_status=right["case.status"],
    annotation_score=right.score,
)
joined = left.join(right, how="left")
```

### Bracket-Index Annotation Join

Use bracket indexing when annotating one table with fields from a keyed lookup table.

```python
lookup = lookup.key_by("sample_id")
ht = ht.key_by("sample_id")
lookup_row = lookup[ht.key]
ht = ht.annotate(
    phenotype=lookup_row.phenotype,
    lookup_score=lookup_row.score,
)
```

This is a left-annotation pattern. Unmatched lookup rows produce missing annotated values. The index expression types must match the lookup key types. For invalid lookup field names, use item access on the lookup row:

```python
ht = ht.annotate(case_status=lookup[ht.key]["case.status"])
```

## Grouping and Aggregation

### Aggregate Rows Into a Local Value

`Table.aggregate` returns a local Python value and expects row aggregators.

```python
summary = ht.aggregate(hl.struct(
    n=hl.agg.count(),
    n_cases=hl.agg.count_where(ht.is_case),
    mean_score=hl.agg.mean(ht.score),
    score_hist=hl.agg.counter(ht.score_bucket),
))
```

Keep local results small. Avoid `hl.agg.collect` on large tables unless the result is bounded.

### Aggregate Per Group Into a New Table

`ht.group_by(...).aggregate(...)` returns a new `Table` keyed by group fields.

```python
by_status = (
    ht.group_by(status=ht["case.status"])
      .aggregate(
          n=hl.agg.count(),
          mean_score=hl.agg.mean(ht.score),
          n_missing_age=hl.agg.count_where(hl.is_missing(ht.age)),
      )
)
```

Group expressions can be named computed expressions. Aggregation expressions may use row fields from the grouped table. If a grouping name collides with an aggregation output name, rename one side.

Useful table-row aggregators include `hl.agg.count`, `count_where`, `fraction`, `mean`, `sum`, `min`, `max`, `stats`, `counter`, `filter`, `take`, and `group_by`.

## Intervals and Range-Like Lookup

A keyed table can use interval keys. A common pattern is importing or constructing interval data, keying by an interval field, then indexing with a point expression.

```python
intervals = intervals.key_by("interval")
ht = ht.annotate(interval_annotation=intervals[ht.position].annotation)
```

Remember:

- Interval indexing is a lookup against a table keyed by interval type.
- The index expression must have the interval point type.
- `all_matches=True` on `Table.index` can return all interval matches, but it is experimental and should be bounded and validated.
- Genomic locus interval workflows should route to `../genomics-analysis/SKILL.md`.

## Export and Native Writes

Use native Table format for intermediate or reusable Hail data:

```python
ht.write("prepared_samples.ht", overwrite=True)
ht = hl.read_table("prepared_samples.ht")
```

Use `Table.export` for text output for other tools:

```python
ht.select("sample_id", "score", "score_bucket").export(
    "scores.tsv.bgz",
    delimiter="\t",
    header=True,
)
```

For large text exports, prefer a `.bgz` output name. Nested structures are exported as JSON; use `flatten()` or select nested fields into top-level fields if downstream tools need one column per field. Do not export to a path that is being read by the same pipeline.

## Local Preview Limits

Safe preview patterns:

```python
ht.head(10).show(width=120, truncate=80)
small_rows = ht.select("sample_id", "score").take(5)
```

Avoid unbounded local collection in normal pipelines:

- `ht.collect()` on large data.
- `ht.take(1000000)` without proving the table is tiny.
- `hl.agg.collect(ht.field)` unless the collected values are known to be bounded.
- `to_pandas()` except for deliberately small results.

## Bundled Template

The bundled `scripts/table_pipeline_template.py` is a dry-run-first starter. It prints a JSON plan by default and only emits runnable Hail code when requested.

```bash
python scripts/table_pipeline_template.py --help
python scripts/table_pipeline_template.py --print-template
python scripts/table_pipeline_template.py --dry-run --input samples.tsv.bgz --key sample_id --types-json '{"sample_id": "str", "score": "float64"}'
python scripts/table_pipeline_template.py --emit-code --input samples.tsv.bgz --output prepared_samples.ht --key sample_id
```

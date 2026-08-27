# Hail Table and Expression Troubleshooting

Use this reference when a table pipeline fails with expression-source errors, aggregation-scope errors, unexpected joins, import parsing surprises, missing-value behavior, excessive collection, or write/export issues.

## Wrong Expression Source or Index

Symptoms:

- `Cannot combine expressions from different source objects`
- `Found fields from ... objects`
- `source mismatch`, `scope violation`, `Invalid fields`, or `Problematic field(s)`
- A pipeline fails after chaining transformations and reusing an older field expression.

Cause: Hail expressions remember the exact source table and axes they came from. After creating a new `Table`, use fields from the new object.

Problem pattern:

```python
old_x = ht.x
ht = ht.filter(ht.keep)
ht = ht.select(old_x)  # old_x came from the previous table object
```

Repair:

```python
ht = ht.filter(ht.keep)
ht = ht.select(ht.x)
```

Checklist:

- Rebind after each table-returning operation: `ht = ht.filter(...)`, then use `ht.field` from the rebound object.
- Do not mix row expressions from unrelated tables except through `join` or bracket-index lookup.
- For `Table.filter`, the predicate must be row-indexed by that table or scalar/globals.
- For `Table.aggregate`, row fields must appear inside aggregators such as `hl.agg.mean(ht.x)`.
- For `Table.annotate` and `Table.select`, expressions should come from the current table, globals/scalars, or valid lookup expressions.

## Aggregation in the Wrong Context

Symptoms:

- `Table.annotate does not support aggregation`
- `Table.filter does not support aggregation`
- `scope violation` mentions aggregation axes
- A local Python value appears where a table was expected, or an aggregator expression is used as if it were row-indexed.

Repairs:

Use `Table.aggregate` for a local value:

```python
mean_score = ht.aggregate(hl.agg.mean(ht.score))
```

Use `group_by(...).aggregate(...)` for a grouped table:

```python
by_status = ht.group_by(status=ht.status).aggregate(mean_score=hl.agg.mean(ht.score))
```

Attach a global summary back to rows with a two-step pattern:

```python
mean_score = ht.aggregate(hl.agg.mean(ht.score))
ht = ht.annotate(centered_score=ht.score - mean_score)
```

Do not put `hl.agg.mean(ht.score)` directly in `ht.annotate(...)` or `ht.filter(...)` unless the method explicitly supports aggregation over that axis.

## Unkeyed or Mismatched Joins

Symptoms:

- `Must have non-empty key to index`
- `Key type mismatch: cannot index table with given expressions`
- `'join': key mismatch`
- Join result has too many rows.
- Join fields are missing unexpectedly.

Repairs:

Check both keys:

```python
print(left.key)
print(right.key)
print(left.key.dtype)
print(right.key.dtype)
```

Key both sides with matching Hail types and order:

```python
left = left.key_by("sample_id")
right = right.key_by("sample_id")
joined = left.join(right, how="left")
```

For compound keys, match order:

```python
left = left.key_by("sample_id", "visit")
right = right.key_by("sample_id", "visit")
```

If text import inferred one key as `int32` and another as `str`, cast or import with explicit `types`:

```python
right = right.annotate(sample_id=hl.str(right.sample_id)).key_by("sample_id")
```

If row counts grow unexpectedly, test for duplicate keys before joining:

```python
key_counts = ht.group_by(*ht.key.values()).aggregate(n=hl.agg.count())
dupes = key_counts.filter(key_counts.n > 1)
dupes.head(10).show()
```

For bracket-index annotation joins, the lookup table must be keyed and the index expression must come from the table being annotated:

```python
lookup = lookup.key_by("sample_id")
ht = ht.key_by("sample_id")
ht = ht.annotate(phenotype=lookup[ht.key].phenotype)
```

## Overlapping Field Names in Joins

Symptoms:

- Right-side fields appear with suffixes such as `_1`.
- Downstream field references fail because a joined name changed.

Cause: `Table.join` preserves left fields. Right non-key field names that collide with left field names are renamed.

Repairs:

Rename or select right fields before joining:

```python
right = right.select(
    annotation_status=right.status,
    annotation_score=right.score,
)
joined = left.join(right, how="left")
```

Or use bracket-index annotation with explicit output names:

```python
right = right.key_by("sample_id")
left = left.key_by("sample_id")
left = left.annotate(
    annotation_status=right[left.key].status,
    annotation_score=right[left.key].score,
)
```

## Field Name and Dot-Access Surprises

Symptoms:

- `Table instance has no field ...`
- A field appears in `describe()` but `ht.field_name` fails.
- Dot access resolves a method, reserved attribute, or invalid Python identifier instead of a field.
- Imported fields contain spaces, dots, hyphens, punctuation, or names such as `select`, `key`, or `show`.

Repairs:

Use item access:

```python
ht["sample id"]
ht["case.status"]
ht["PT-ID"]
ht["select"]
```

Rename fields early for maintainability:

```python
ht = ht.select(
    sample_id=ht["sample id"],
    case_status=ht["case.status"],
    pt_id=ht["PT-ID"],
)
```

For local `Struct` rows from `take`, use `row["field-name"]` for non-identifier names.

## Imputation Mistakes

Symptoms:

- Numeric fields are imported as `str`.
- IDs with leading zeros become integers.
- Mixed values cause unexpected inferred types.
- Import is slower than expected.

Cause: `impute=True` parses text input twice and guesses types. It can infer inconvenient or unsafe types for identifiers.

Repairs:

Prefer explicit `types` for stable pipelines:

```python
ht = hl.import_table(
    "samples.tsv.bgz",
    types={"sample_id": hl.tstr, "age": hl.tint32, "score": hl.tfloat64},
    missing="NA",
)
```

Keep sample IDs, zip codes, and codes with leading zeroes as `hl.tstr`. Cast after import only when the original parse is harmless.

## Delimiter, Header, Missing-Value, and Quote Issues

Symptoms:

- Entire rows appear as one field.
- Columns are shifted or split incorrectly.
- Header is treated as data or generated `f0`, `f1` names appear unexpectedly.
- Missing values remain literal strings such as `.` or empty text.

Repairs:

- CSV: `delimiter=","`.
- Headerless file: `no_header=True`, then `select` or `rename` generated fields.
- Non-default missing marker: `missing="."` or the observed token.
- Quoted CSV-like fields: `quote='"'`.
- Comments: `comment=("#",)`.
- Blank-line handling: adjust `skip_blank_lines` if blank records are meaningful.

Example:

```python
ht = hl.import_table(
    "samples.csv",
    delimiter=",",
    quote='"',
    missing=".",
    types={"sample_id": hl.tstr, "score": hl.tfloat64},
)
```

Inspect immediately with `describe()` and a small `head(...).show()`.

## Missingness and Boolean Logic

Symptoms:

- Python raises an error about truthiness of a Hail expression.
- Conditional fields are missing when a default value was expected.
- Filters drop rows with missing predicates unexpectedly.

Repairs:

Use Hail boolean operators and conditionals:

```python
ht = ht.filter((ht.age >= 18) & hl.is_defined(ht.score))
ht = ht.annotate(flag=hl.if_else(hl.is_defined(ht.score), ht.score > 10, False))
```

Treat missing predicates intentionally:

```python
ht = ht.annotate(
    status=hl.case(missing_false=True)
        .when(ht.score > 10, "high")
        .default("not_high")
)
```

Use `hl.coalesce(expr, fallback)` or `hl.or_else(expr, fallback)` when missing values should become defaults.

## Local Preview and Collection Pitfalls

Symptoms:

- The driver runs out of memory.
- A notebook stalls while previewing rows.
- A pipeline is slow because it collects too much data locally.

Repairs:

Use bounded previews:

```python
ht.head(10).show(width=120, truncate=80)
rows = ht.select("sample_id", "score").take(5)
```

Avoid unbounded local calls on large data:

- `collect()`
- large `take(n)`
- large `to_pandas()`
- `hl.agg.collect` without a known bound
- printing very wide tables without `width` or `truncate`

For diagnostics, select only necessary fields before previewing.

## Write and Export Pitfalls

Symptoms:

- Export is slow or creates unexpected shards.
- Nested fields appear as JSON strings in text output.
- A path validation error occurs.
- A pipeline reads and writes the same path.

Repairs:

Use native writes for Hail intermediates:

```python
ht.write("prepared.ht", overwrite=True)
```

Use text export for downstream non-Hail tools:

```python
ht.select("sample_id", "score").export("scores.tsv.bgz")
```

Guidelines:

- Prefer `.ht` native output for reusable Hail data.
- Prefer `.bgz` text output for large exported tables.
- Use `flatten()` or select nested fields into top-level columns before `export` when downstream tools cannot read JSON values.
- Do not write or export to a path that is being read in the same pipeline.
- Use `overwrite=True` only when replacing existing native output is intentional.

## Backend or Package Asset Failures

Symptoms:

- `import hail` succeeds but `hl.init()` or an action such as `show`, `count`, `write`, or `export` fails.
- Errors mention missing backend assets, local/Spark setup, Java, or generated Hail runtime files.

Route these to `../setup-and-backends/SKILL.md`. Table syntax may be correct even when the backend is unavailable.

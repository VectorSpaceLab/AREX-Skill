# Cube Queries

## When to read

Read this for a reusable metric or aggregation with declared measures,
dimensions, time dimensions, and filters.

## Discover first

```bash
wren cube list
wren cube describe revenue
```

A cube is a semantic object. Do not guess measure or dimension names from raw
columns.

## CLI flags

```bash
wren cube query \
  --cube revenue \
  --measures total,order_count \
  --dimensions status \
  --time-dimension 'order_date:month:2024-01-01,2025-01-01' \
  --filter 'status:eq:completed' \
  --limit 100 \
  --sql-only
```

- `--measures` is required unless using `--from`.
- `--dimensions` is a comma-separated list.
- `--time-dimension` is `name:granularity[:start,end]`.
- `--filter` is repeatable: `dimension:operator[:value]`.
- `in` and `not_in` filters use comma-separated values.
- `--from <file|->` accepts a CubeQuery JSON object.
- `--sql-only` prints generated SQL without execution.

Supported granularity names are `year`, `quarter`, `month`, `week`, `day`,
`hour`, and `minute`. Common operators include `eq`, `neq`, `in`, `not_in`,
`gt`, `gte`, `lt`, `lte`, `contains`, `starts_with`, `is_null`, and
`is_not_null`.

## Decision rule

Prefer a cube over raw SQL when it covers the requested aggregation. Use raw SQL
when the task needs an uncovered custom join, a window function, a CTE, a
non-aggregation query, or a new metric that has not been modeled yet.

## Recovery

- Unknown cube: rerun `wren cube list`.
- Unknown measure/dimension: inspect `wren cube describe <name>`.
- Invalid filter/time shape: correct the structured flag syntax, then use
  `--sql-only` before a live execution.
- New cube source fails validation: repair the MDL source through the
  cli-projects route; never hand-edit compiled `mdl.json`.

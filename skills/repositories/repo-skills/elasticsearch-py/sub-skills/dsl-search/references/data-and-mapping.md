# Data and mapping guidance

## Field selection

Use `Text` for analyzed full-text search, `Keyword` for exact values,
aggregations, sorting, and joins, date fields for date math/ranges, and numeric
fields for numeric comparisons/metrics. `Nested` and object fields differ in
how arrays of objects preserve relationships; select deliberately. Vector and
semantic fields have server/version and optional-dependency prerequisites; keep
them separate from a basic mapping.

## Index lifecycle

1. Define the `Document` and its `Index` metadata.
2. Review the rendered mapping/settings and create an isolated index.
3. Call `Document.init(using=client)` only after the target and privileges are
   confirmed.
4. Index a representative document and read it back.
5. Change mappings through a new index plus reindex when an existing field type
   cannot be changed in place.

Do not use `auto_refresh` or destructive index operations as a substitute for a
migration plan. Use aliases for cutovers and verify counts/mappings before
switching traffic.

## Validation and typing

The DSL validates many field/query construction details locally, but server
validation still governs index mappings and feature availability. Run
`to_dict()` in tests and use the package's type examples/type checker when
static correctness matters. When a field name is dynamic, use the documented
field access patterns or a validated allow-list rather than accepting arbitrary
user input.

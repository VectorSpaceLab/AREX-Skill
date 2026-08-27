---
name: tables-and-expressions
description: "Build Hail Table and expression pipelines for imports, keys,
  joins, aggregations, schema inspection, previews, exports, and
  expression-scope troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Hail Tables and Expressions

Use this sub-skill for Hail `Table` pipelines and row-indexed expression work: `hl.import_table`, `hl.read_table`, `Table.write`, `Table.export`, `annotate`, `filter`, `select`, `key_by`, keyed joins, `group_by`, `hl.agg`, schema inspection, small local previews, missing values, `Struct` fields, interval lookups, and expression source/index errors.

Before executing Hail queries, use `../setup-and-backends/SKILL.md` to choose and initialize the backend. This sub-skill assumes backend setup is already handled.

## Start Here

- For end-to-end import, schema, key, join, aggregation, and export recipes, read `references/table-workflows.md`.
- For compact signatures and method behavior, read `references/api-reference.md`.
- For expression-scope, missingness, import, join, preview, and write failures, read `references/troubleshooting.md`.
- For a safe dry-run-first starting point, adapt `scripts/table_pipeline_template.py`.

## Route Elsewhere

- MatrixTable rows, columns, entries, VCF/PLINK/BGEN, genotype fields, and genomic QC belong in `../genomics-analysis/SKILL.md`.
- Variant Dataset, sparse GVCF, combiner, and VDS dense/sparse conversion workflows belong in `../variant-datasets/SKILL.md`.
- Hail install/import, `hl.init`, Spark/local/Batch backend choice, Java/JAR/package asset failures, and root import troubleshooting belong in `../setup-and-backends/SKILL.md`.
- `hailtop.batch` DAGs, local/service Batch jobs, `hailctl`, Dataproc, HDInsight, and cloud CLI operations belong in `../batch-and-cli/SKILL.md`.

## Working Rules

- Rebind each table-returning transformation before using fields again: `ht = ht.filter(...)`, then reference `ht.field` from the rebound table.
- Use bracket access for imported names that are not valid identifiers or that collide with methods: `ht["sample id"]`, `ht["case.status"]`, `ht["select"]`.
- Key both sides before joins or bracket-index lookup; key count, order, and Hail types must match even when key field names differ.
- Keep `hl.agg` inside supported aggregation contexts such as `ht.aggregate(...)` and `ht.group_by(...).aggregate(...)`.
- Prefer explicit `types={...}` for stable text imports; use `impute=True` only for exploration and review inferred identifier types.
- Inspect with `describe()`, `row.dtype`, `globals.dtype`, `key`, `head(n).show()`, and small `take(n)` calls before large writes, exports, or joins.

# dlt and SaaS Data Workflow

## When to read

Read this when the source is HubSpot, Stripe, Salesforce, GitHub, Slack, or a
similar SaaS API that should be loaded through dlt before Wren models it.

## End-to-end shape

```text
SaaS API -> dlt pipeline -> local DuckDB database -> Wren project -> MDL build -> governed query
```

1. Identify the dlt source and its credential mechanism. Keep tokens outside
   chat and version control.
2. Load to DuckDB with dlt. Confirm the pipeline finished and the database file
   exists.
3. Generate a project from that local database:
   ```bash
   python scripts/introspect_dlt_project.py \
     --duckdb-path source-data.duckdb \
     --output-dir analytics-project \
     --project-name analytics
   ```
4. Review the generated model files, then build and validate:
   ```bash
   cd analytics-project
   wren context validate
   wren context build
   ```
5. Create/bind a DuckDB profile and run a small query only after the model
   references are correct.

## Important DuckDB contract

When Wren attaches a DuckDB database, the filename stem becomes the catalog
alias. A database named `stripe_data.duckdb` therefore needs model references
that use `catalog: stripe_data`. A wrong catalog commonly produces a table-not-
found error even when the file exists.

## Generator behavior

The bundled helper reads DuckDB metadata, filters dlt internal tables and common
metadata columns, writes a version-5 Wren project, and normalizes types through
the installed Wren package when available. It intentionally does not claim that
inferred relationships or business semantics are complete. Review and enrich the
project before treating it as production context.

## Avoid

- Do not run a dlt writer against the same DuckDB file while querying it.
- Do not assume generated table names are business-friendly models.
- Do not skip `wren context validate`/`build` after generation.

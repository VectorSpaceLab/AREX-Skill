# Connectors and Datasources

## When to read

Read this before a live query, dry run, or Python `query()` call. Planning can
work without a database; execution cannot.

## Installation rule

Install only the selected connector extra. Base Wren includes DuckDB; other
common connections require a corresponding extra.

```bash
pip install "wrenai[postgres]"
pip install "wrenai[bigquery]"
pip install "wrenai[snowflake]"
```

Use the root installation reference for the complete extra list. Do not install
all connectors merely because one import is missing.

## Connection contract

- The datasource comes from explicit connection information, a project-bound
  profile, or the active profile.
- Query connection fields are validated by datasource-specific Pydantic models.
- Discover exact fields with:
  ```bash
  wren docs connection-info <datasource>
  ```
- Keep secret values in environment-backed profile placeholders.

## Execution expectations

| Datasource class | What to verify before query |
| --- | --- |
| DuckDB/local files | file/directory exists; model table reference matches attached catalog behavior |
| Local service | host/port/network reachability, credentials, and connector extra |
| Cloud warehouse | connector extra, account/project fields, credentials, permissions, and cost policy |
| File/object store | source URI/access configuration and object-store credentials if applicable |

## Safe local baseline

A small DuckDB project is the best package-level smoke path. It does not prove
behavior for Postgres, Snowflake, BigQuery, or other service-backed connectors.
Treat those as separate operational environments with their own credentials and
validation.

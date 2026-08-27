# Profiles and Connections

## When to read

Read this before adding a database profile, diagnosing a missing secret, or
choosing a datasource extra.

## Profile flow

A profile stores a datasource plus connection fields. A project can bind a
profile so it does not depend on whichever profile is globally active.

```bash
wren docs connection-info postgres --format md
wren profile add analytics --from-file connection.yml
wren profile debug analytics
wren context set-profile analytics --path analytics-project
```

Use `wren profile list` to see the active profile and `wren profile switch NAME`
only when a workflow intentionally changes the global selection.

## Keep secrets external

Use `${UPPERCASE_NAME}` placeholders in profile values and set the real values
in process environment or an `.env` file. Wren resolves placeholders from the
shell first, then the current directory/project/global environment files.

```yaml
# connection.yml
 datasource: postgres
 host: ${POSTGRES_HOST}
 port: ${POSTGRES_PORT}
 database: ${POSTGRES_DATABASE}
 user: ${POSTGRES_USER}
 password: ${POSTGRES_PASSWORD}
```

Do not put secret values in model YAML, committed `.env` files, chat messages,
or `--connection-info` arguments that may enter shell history.

## Datasource selection

The profile datasource must match the project's intended dialect. Ask the CLI
for the live field definition instead of guessing keys:

```bash
wren docs connection-info duckdb
wren docs connection-info bigquery
wren docs connection-info snowflake
```

A connector may also require a package extra. Install only the needed extra,
then rerun the same `connection-info`/profile check.

## Debug order

1. Confirm project discovery and its bound profile.
2. Run `wren profile debug <name>`; sensitive fields are masked.
3. Confirm missing `${VAR}` values are available without printing them.
4. Confirm the connector extra is installed.
5. Only then attempt a live connection or query.

## DuckDB note

For DuckDB profiles, the connection value usually identifies the directory that
contains the database file. A model referencing a file-backed table must use
catalog/schema/table values consistent with the attached database name.

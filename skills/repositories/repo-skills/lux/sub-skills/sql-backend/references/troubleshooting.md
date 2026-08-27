# Lux SQL backend troubleshooting

SQL support is optional in Lux. Treat every SQL issue as a service-backed problem until the connector, PostgreSQL service, table name, permissions, and Lux SQL executor state are all confirmed.

## Start with the non-destructive probe

When the user can provide credentials, run a count/preview probe before constructing a `LuxSQLTable`:

```bash
python scripts/sql_table_probe.py --dsn "$PG_DSN" --table cars
python scripts/sql_table_probe.py --sqlalchemy-url "$DATABASE_URL" --table public.cars --preview-rows 0
```

If the probe fails, fix the service/connector/table issue first. `LuxSQLTable` metadata generation runs more queries than this probe and can make the error harder to isolate.

## Missing connector package

Symptoms:

- `ModuleNotFoundError: No module named 'psycopg2'`
- SQLAlchemy URL fails because the underlying PostgreSQL DBAPI is missing.

Fix:

```bash
pip install psycopg2-binary
# or, when using SQLAlchemy URLs:
pip install sqlalchemy psycopg2-binary
```

Some production deployments prefer compiling `psycopg2` against system PostgreSQL libraries instead of using `psycopg2-binary`; follow the deployment policy for that environment.

## PostgreSQL service connection failed

Symptoms:

- connection refused;
- timeout;
- host name cannot resolve;
- authentication failed;
- SSL or database-name errors.

Safe checks:

1. Confirm PostgreSQL 9.5 or newer is installed and running.
2. Confirm host, port, database, user, password, and SSL mode.
3. Confirm the client environment can reach the service network.
4. Test the same DSN or URL with `scripts/sql_table_probe.py`.
5. Do not paste long-lived credentials into notebooks, committed scripts, or chat transcripts.

## Table or relation does not exist

Symptoms:

- database error mentions `relation ... does not exist`;
- Lux warns that the table is not present;
- probe can connect but fails on `SELECT COUNT(1)`.

Fixes:

- Verify the table is in the connected database, not another database.
- Check schema/search-path behavior. If the table lives outside the default schema, either set the connection search path or create a simple read-only view in the active schema.
- Prefer lowercase table and column names. Lux templates quote many column names but insert table names from the `table_name` string.
- Confirm the database user has read permission on both the table/view and metadata in `information_schema.columns`.

## `LuxSQLTable` is slow or runs too many queries

`LuxSQLTable` stores metadata rather than a full local dataframe, but metadata generation can still be expensive. It may count rows, enumerate distinct non-null values, compute cardinalities, inspect data types, and compute min/max for quantitative fields.

Fixes:

- Point Lux at a narrow database view containing only columns relevant to exploration.
- Avoid very high-cardinality text/id columns when creating the view.
- Add database indexes appropriate for common filters and group-by columns.
- For exploratory demos, use a small read-only sample table or materialized view.

## Normal Pandas methods do not work

`LuxSQLTable` is not an ordinary in-memory Pandas dataframe. The SQL executor delegates work to PostgreSQL and does not pull the full table into local memory.

Fixes:

- For cleaning, joins, derived columns, or row filtering, write SQL first and expose the result as a table/view for Lux.
- If the result is small and safe to load locally, use `pandas.read_sql(...)` to create a local dataframe, then use the regular Lux Pandas workflow.
- Do not expect `head`, `tail`, `groupby`, `describe`, or arbitrary dataframe mutation to behave like Pandas on SQL-backed tables.

## Recommendations or exports do not appear

Checklist:

1. Configure the connection with `lux.config.set_SQL_connection(connection_or_engine)`.
2. Ensure SQL executor mode is active with `lux.config.set_executor_type("SQL")`.
3. Bind a valid table with `lux.LuxSQLTable(table_name="...")` or `set_SQL_table("...")`.
4. Trigger Lux recommendation maintenance through notebook display, intent setting, or constructing a `Vis`/`VisList` with the SQL table as source.
5. For code export, ensure chart data has been materialized before calling `to_code`, `to_altair`, or `to_vegalite`.

If widget rendering itself fails, switch the display question to the root/configuration guidance. SQL connectivity and metadata should be debugged separately from Jupyter widget setup.

## JOIN confusion

The SQL executor itself does not support general joins across multiple SQL tables. `JoinedSQLTable` is a separate helper that creates a database view from explicit join conditions.

Use `JoinedSQLTable` only when all of these are true:

- the user has create-view privileges;
- join table and column names are trusted and prevalidated;
- a psycopg2-style connection is available;
- the user accepts that a database view may be left behind and need cleanup;
- no more than four unique tables are involved.

Otherwise, ask the user to create a safe view with SQL outside Lux and then use `LuxSQLTable(table_name="that_view")`.

## Query-template or executor state is inconsistent

Symptoms:

- SQL executor has no templates;
- Pandas executor is active after previous operations;
- SQL connection was cleared unexpectedly.

Fix:

```python
lux.config.set_SQL_connection(connection_or_engine)
lux.config.set_executor_type("SQL")
```

To return to local Pandas workflows:

```python
lux.config.set_executor_type("Pandas")
```

## Unsupported or fragile database features

State these limitations clearly:

- Lux SQL behavior is limited and primarily tested for PostgreSQL.
- The query templates rely on PostgreSQL features such as `random()` and `width_bucket`-style binning.
- Complex quoted identifiers, schema-qualified table names, and non-PostgreSQL backends may require a normalized view.
- SQL native tests should be skipped unless a PostgreSQL service and fixture tables are explicitly prepared.

## Unsafe helper-script pattern to avoid

Do not provide runtime scripts that download remote data, hardcode local database credentials, or drop/recreate user tables. If a user needs fixture data, give a schema and ask them to create/populate a safe test database under their own credentials and policies.

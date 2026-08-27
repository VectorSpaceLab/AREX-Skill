# Lux SQL backend workflows

Lux can delegate selected visualization data processing to a PostgreSQL database through the SQL executor. This is useful when data is too large or too restricted to pull fully into a local Pandas dataframe.

This workflow is optional and service-backed. It requires a running PostgreSQL service and connector packages supplied by the user. Base Lux usage with Pandas does not require any of this SQL setup.

## Prerequisites

- Lux API installed and importable as `lux`.
- PostgreSQL version 9.5 or newer.
- A database, table, or view that already exists and is safe for read-only metadata and preview queries.
- One connector path:
  - `psycopg2` connection object or DSN; the Lux installation docs name Psycopg2 as the required SQL connector.
  - SQLAlchemy PostgreSQL engine or URL. If the URL uses the psycopg2 DBAPI, the environment still needs `psycopg2` or `psycopg2-binary` installed.
- Permission to run read queries against the target table and `information_schema.columns`.
- For `JoinedSQLTable`, permission to create a database view.

Keep credentials outside notebooks and scripts when possible; prefer environment variables, a secrets manager, or a short-lived DSN provided at runtime.

## Safe preflight probe

Before constructing a `LuxSQLTable`, check that the connector can reach the service and that the table exists:

```bash
python scripts/sql_table_probe.py --dsn "$PG_DSN" --table cars
python scripts/sql_table_probe.py --sqlalchemy-url "$DATABASE_URL" --table public.cars --preview-rows 3
```

The probe performs only `SELECT COUNT(1)` and an optional `SELECT * ... LIMIT n`. It does not create, drop, update, or insert anything, and it does not invoke Lux metadata generation.

## Connect with psycopg2

```python
import os
import lux
import psycopg2

connection = psycopg2.connect(os.environ["PG_DSN"])
lux.config.set_SQL_connection(connection)
lux.config.set_executor_type("SQL")  # explicit SQL executor/template refresh when needed

sql_tbl = lux.LuxSQLTable(table_name="cars")
sql_tbl.set_intent([lux.Clause("milespergal"), lux.Clause("weight")])
sql_tbl  # in a notebook, display triggers Lux recommendations
```

`lux.config.set_SQL_connection(connection)` stores the connection and switches Lux to the SQL executor. Calling `set_executor_type("SQL")` is useful when a session may have been switched back to Pandas or when you want to reload the SQL query templates.

## Connect with SQLAlchemy

```python
import os
import lux
from sqlalchemy import create_engine

engine = create_engine(os.environ["DATABASE_URL"])
lux.config.set_SQL_connection(engine)
lux.config.set_executor_type("SQL")

sql_tbl = lux.LuxSQLTable(table_name="cars")
```

Use a PostgreSQL URL for SQLAlchemy, for example one beginning with `postgresql://` or `postgresql+psycopg2://`. Avoid embedding passwords directly in source files.

## Bind an existing table or view

Constructor style:

```python
sql_tbl = lux.LuxSQLTable(table_name="cars")
```

Setter style:

```python
sql_tbl = lux.LuxSQLTable()
sql_tbl.set_SQL_table("cars")
```

The table name should resolve in the current database and schema search path. Lux uses the name in generated queries and also asks `information_schema.columns` for the table's columns. Prefer lower-case, unquoted identifiers or a simple read-only view with friendly column names.

## Use SQL-backed Lux intents and visualizations

After the table is bound, use the same high-level Lux intent objects that base Lux workflows use:

```python
sql_tbl.set_intent([
    lux.Clause(attribute="origin"),
    lux.Clause(attribute="horsepower", aggregation="mean"),
])

# Recommended visualizations are generated when Lux maintains recommendations,
# usually through notebook display or explicit visualization construction.
vis = lux.Vis([lux.Clause("horsepower"), lux.Clause("weight")], sql_tbl)
code = vis.to_code("python")
```

Common patterns exercised by the SQL executor include:

- no-intent recommendations such as correlation, distribution, occurrence, and temporal views;
- filter intents such as `lux.Clause(attribute="origin", filter_op="=", value="USA")`;
- aggregates such as `mean`, `sum`, and `max` for bar/line charts;
- wildcard expansion with `lux.Clause("?")` and `lux.VisList(..., sql_tbl)`;
- code export after the SQL executor has materialized chart data.

## Query-template behavior

When Lux is in SQL mode it loads PostgreSQL-oriented query templates. These templates generate:

- preview queries: `SELECT * FROM {table_name} LIMIT {num_rows}`;
- row counts: `SELECT COUNT(1) ...`;
- random samples for large scatterplots;
- grouped counts and aggregate bar/line chart queries;
- histogram and heatmap queries using PostgreSQL-style `width_bucket` logic;
- table metadata queries against `information_schema.columns`;
- min/max, cardinality, unique-value, and data-type queries.

Column names are quoted in many visualization templates, while table names are inserted as the table identifier provided to `LuxSQLTable`. If a database uses mixed-case or special-character identifiers, prefer a simple lowercase view rather than relying on complex quoting.

## JoinedSQLTable workflow

The normal SQL executor documentation states that JOIN is not supported as a general executor operation. Lux also includes a separate `JoinedSQLTable` class that creates a database view from explicit join conditions and then treats that generated view as the SQL table.

Use it only when the user understands the database-side effect and has suitable privileges:

```python
import os
import lux
import psycopg2

connection = psycopg2.connect(os.environ["PG_DSN"])
lux.config.set_SQL_connection(connection)
lux.config.set_executor_type("SQL")

joined = lux.JoinedSQLTable(
    joins=[
        "orders.customer_id = customers.id",
        "orders.product_id = products.id",
    ]
)
joined.set_intent([lux.Clause("order_total"), lux.Clause("country")])
```

Important `JoinedSQLTable` caveats:

- It builds a `CREATE VIEW lux_view_<timestamp> AS SELECT * FROM ... WHERE ...` statement from the provided table names and join strings.
- It is best matched with a psycopg2-style connection because the implementation uses a DBAPI cursor and commits the view creation.
- It warns when more than four unique tables are involved.
- Join strings are inserted into SQL text. Do not accept untrusted user input for join conditions.
- The created view may need manual cleanup by the database owner.

## Limitations to state explicitly

- SQL support is limited and tested primarily for PostgreSQL.
- SQL native tests are optional because they require a PostgreSQL service and fixture tables.
- `LuxSQLTable` is a Lux table skeleton backed by database metadata and query results, not a normal in-memory Pandas dataframe. Do not use ordinary Pandas manipulation methods on it.
- If the task requires heavy cleaning, joins, or transformations, do those operations in SQL first and point Lux at the resulting table/view; or fetch a small result into Pandas and use the Pandas Lux workflow.
- Metadata generation may run distinct-value, cardinality, min/max, and type queries across columns. On wide or high-cardinality tables, create a narrower view before handing the table to Lux.

## Distilled schema evidence from unsafe upload helpers

The original helper scripts for test/demo data download remote CSV files, hardcode local credentials, and in some cases drop and recreate tables. Do not reuse them as runtime scripts. The only safe reusable knowledge from them is schema shape:

### `cars`

```text
name text
milespergal numeric
cylinders integer
displacement numeric
horsepower integer
weight integer
acceleration numeric
year integer
origin text
brand text
```

The SQL tests use this table for aggregate, filter, wildcard, recommendation, and export examples.

### `aug_test_table`

```text
enrollee_id integer
city text
city_development_index numeric
gender text
relevent_experience text
enrolled_university text
education_level text
major_discipline text
experience text
company_size text
company_type text
last_new_job text
training_hours integer
```

The SQL tests use this table to check null handling in unique-value metadata.

### `flights`

```text
year integer
month text
day integer
weekday integer
carrier text
origin text
destination text
arrivaldelay integer
depaturedelay integer
weatherdelay integer
distance integer
```

This is a demo-table shape. It is not required for the core SQL examples.

### `airbnb`

The helper creates an `airbnb` table with Pandas `to_sql(..., if_exists="replace")` from a remote CSV and no explicit schema list. Treat it only as evidence that additional demo tables existed, not as a stable LuxSQLTable contract.

# Semantic Schema and Data Formats

## Dataset paths and schema names

Public dataset paths use:

```text
organization/dataset
```

Both segments must be lowercase, start/end with alphanumeric characters, and use
hyphens instead of spaces or underscores. Examples:

- valid: `acme-corp/sales-data`
- invalid: `Acme/sales`, `acme/sales_data`, `acme/-sales`

When a dataset is created, the dataset slug is transformed to an underscore
schema/table name. For example, `sales-data` becomes `sales_data`. Use the
schema name for generated SQL table references.

## Local source schema

A local table schema has a source type of `csv` or `parquet`:

```yaml
name: sales_data
description: Daily retail sales
source:
  type: parquet
  path: data.parquet
columns:
  - name: transaction_id
    type: string
    description: Sale identifier
  - name: quantity
    type: integer
  - name: unit_price
    type: float
```

When using `pai.create(path, df=...)`, PandasAI writes `data.parquet` and a
matching `schema.yaml` automatically.

## SQL source schema

Remote SQL-style sources require optional connector packages and credentials:

```yaml
name: health_data
description: Health rows from PostgreSQL
source:
  type: postgres
  connection:
    host: db.example.com
    port: 5432
    database: analytics
    user: ${DB_USER}
    password: ${DB_PASSWORD}
  table: patients
columns:
  - name: id
    type: integer
  - name: age
    type: integer
```

Never hardcode real passwords. Use environment variable placeholders or secret
management.

Supported source types in the schema model:

- local: `csv`, `parquet`
- remote/extension-backed: `mysql`, `postgres`, `cockroachdb`, `sqlserver`,
  `yahoo_finance`, `bigquery`, `snowflake`, `databricks`, `oracle`

## Column types

Valid column `type` values:

- `string`
- `integer`
- `float`
- `datetime`
- `boolean`

Column `expression` values are parsed as SQL expressions. Use `alias` when the
output column name should differ from the source expression.

## Transformations

Transformation entries have a `type` and optional `params`:

```yaml
transformations:
  - type: fill_na
    params:
      column: amount
      value: 0
  - type: map_values
    params:
      column: segment
      mapping:
        A: Premium
        B: Standard
```

Supported transformation types include:

`anonymize`, `convert_timezone`, `to_lowercase`, `to_uppercase`, `strip`,
`round_numbers`, `scale`, `format_date`, `to_numeric`, `to_datetime`, `fill_na`,
`replace`, `extract`, `truncate`, `pad`, `clip`, `bin`, `normalize`,
`standardize`, `map_values`, `rename`, `encode_categorical`, `validate_email`,
`validate_date_range`, `normalize_phone`, `remove_duplicates`,
`validate_foreign_key`, `ensure_positive`, and `standardize_categories`.

`rename` requires `params.new_name`.

## `group_by` rules

When `group_by` is specified:

- every non-aggregated column must appear in `group_by`;
- aggregated columns with `expression` must not appear in `group_by`;
- `group_by` entries must use the column names visible in the schema.

Example:

```yaml
columns:
  - name: region
    type: string
  - name: amount
    type: float
    expression: SUM(amount)
    alias: total_amount
group_by:
  - region
```

## View schemas

Views combine existing datasets. A view schema uses `view: true` and no `source`.
All view columns and relation endpoints must use `table.column` format with
letters, numbers, and underscores.

```yaml
name: sales_overview
view: true
columns:
  - name: orders.id
    type: integer
  - name: orders.total_amount
    type: float
  - name: customers.segment
    type: string
relations:
  - from: orders.customer_id
    to: customers.id
```

If a view references multiple tables, each table must be connected through at
least one relation. Source datasets must exist before loading the view.

## Excel files

`pai.read_excel` mirrors pandas sheet behavior:

- default `sheet_name=0`: returns one PandasAI `DataFrame`;
- named or indexed sheet: returns one `DataFrame`;
- `sheet_name=None`: returns a dict mapping sheet names to `DataFrame` objects.

An empty or nonexistent sheet name raises a pandas/ValueError-style exception.

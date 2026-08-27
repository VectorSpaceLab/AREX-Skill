# Semantic Layer Workflows

## Create a local CSV dataset

```python
import pandasai as pai

raw = pai.read_csv("sales.csv")

df = pai.create(
    path="acme-corp/sales-data",
    df=raw,
    description="Sales transactions by region",
    columns=[
        {"name": "region", "type": "string", "description": "Sales region"},
        {"name": "revenue", "type": "float", "description": "Revenue in USD"},
    ],
)

loaded = pai.load("acme-corp/sales-data")
print(loaded.schema.name)  # sales_data
```

Use the returned or loaded dataframe with the conversational-analysis sub-skill
for `.chat()`.

## Create an Excel-backed DataFrame

```python
import pandasai as pai

single = pai.read_excel("workbook.xlsx", sheet_name="Sheet1")
all_sheets = pai.read_excel("workbook.xlsx", sheet_name=None)

for sheet_name, sheet_df in all_sheets.items():
    print(sheet_name, sheet_df.schema.name)
```

When `sheet_name=None`, handle a dict. Do not pass the dict directly to
`pai.create`; select or merge sheets first.

## SQL virtual dataset

```python
import pandasai as pai

orders = pai.create(
    path="acme-corp/orders",
    description="Orders from PostgreSQL",
    source={
        "type": "postgres",
        "connection": {
            "host": "db.example.com",
            "port": 5432,
            "database": "analytics",
            "user": "${DB_USER}",
            "password": "${DB_PASSWORD}",
        },
        "table": "orders",
    },
    columns=[
        {"name": "id", "type": "integer"},
        {"name": "amount", "type": "float"},
    ],
)
```

Install the exact connector extension for the source type before executing real
queries. A SQL virtual dataset can be created from schema metadata without
fetching the entire table, but `head()` and chat execution need a working
connector and credentials.

## View over existing datasets

```python
import pandasai as pai

view = pai.create(
    path="acme-corp/sales-overview",
    description="Orders joined to customers",
    view=True,
    columns=[
        {"name": "orders.id", "type": "integer"},
        {"name": "orders.amount", "type": "float"},
        {"name": "customers.segment", "type": "string"},
    ],
    relations=[
        {"from": "orders.customer_id", "to": "customers.id"},
    ],
)
```

Create or load the dependency datasets first. For local views, dependency
sources can be different local file formats. For remote views, sources must be
compatible, such as the same connection.

## Aggregations with `group_by`

```python
summary = pai.create(
    path="acme-corp/sales-summary",
    df=raw,
    columns=[
        {"name": "region", "type": "string"},
        {"name": "revenue", "type": "float", "expression": "SUM(revenue)", "alias": "total_revenue"},
    ],
    group_by=["region"],
)
```

If `group_by` is present, every non-expression column must be listed and every
expression column must be omitted from the group-by list.

## Transformation schema

```python
cleaned = pai.create(
    path="acme-corp/clean-sales",
    df=raw,
    columns=[
        {"name": "customer_email", "type": "string"},
        {"name": "amount", "type": "float"},
    ],
    transformations=[
        {"type": "validate_email", "params": {"column": "customer_email", "drop_invalid": False}},
        {"type": "fill_na", "params": {"column": "amount", "value": 0}},
    ],
)
```

The schema validates transformation names and known parameter fields. Query
builders apply transformations to selected column expressions.

## Safe local end-to-end smoke

Run the bundled smoke to verify local create/load/chat behavior without real
LLM credentials:

```bash
python sub-skills/semantic-layer/scripts/create_local_dataset_smoke.py
```

The smoke creates a temporary project directory, writes a tiny CSV, creates a
semantic dataset, loads it, uses `FakeLLM` to query with `execute_sql_query`, and
then deletes the temporary project directory.

# MDL Source Layout

## When to read

Read this before writing or reviewing MDL YAML. It summarizes the source layout
and the distinctions that most often cause incorrect models.

## Project root

```yaml
# wren_project.yml
schema_version: 5
name: analytics_project
catalog: wren
schema: public
data_source: postgres
profile: analytics
```

`catalog` and `schema` above are Wren's own query namespace. They are not the
physical database catalog/schema.

## Physical-table model

```yaml
# models/orders/metadata.yml
name: orders
table_reference:
  catalog: warehouse
  schema: public
  table: orders
primary_key: order_id
columns:
  - name: order_id
    type: BIGINT
    is_primary_key: true
    not_null: true
  - name: customer_id
    type: BIGINT
  - name: total
    type: DECIMAL(12, 2)
```

Use `table_reference` for a physical table. Use `ref_sql` for a model defined
by SQL. Do not define both for the same model.

## Relationships

```yaml
relationships:
  - name: orders_customers
    models: [orders, customers]
    join_type: MANY_TO_ONE
    condition: orders.customer_id = customers.customer_id
```

Relationship columns can make a join path available to modeled SQL. Confirm the
cardinality and equality condition from source schema or a trusted owner; a
plausible but wrong relationship silently changes analytics results.

## Views and cubes

A view is a named SQL statement. A cube is a structured aggregation surface:

```yaml
name: revenue
base_object: orders
measures:
  - name: total
    expression: SUM(total)
    type: DOUBLE
dimensions:
  - name: status
    expression: status
    type: VARCHAR
time_dimensions:
  - name: created_at
    expression: created_at
    type: TIMESTAMP
```

Use a cube when the business concept is a reusable metric or grouped
aggregation. Validate it with both `wren context validate` and a
`wren cube query --sql-only` request.

## Snake case versus camel case

Editable YAML uses snake_case such as `table_reference`, `primary_key`, and
`is_calculated`. The compiled JSON uses camelCase such as `tableReference`,
`primaryKey`, and `isCalculated`. Let `wren context build` perform the
conversion rather than hand-editing the generated target.

## Knowledge is separate from MDL structure

Business rules and accepted NL→SQL examples belong in `knowledge/`, not in a
model's physical schema. Read the memory-knowledge sub-skill for those files.

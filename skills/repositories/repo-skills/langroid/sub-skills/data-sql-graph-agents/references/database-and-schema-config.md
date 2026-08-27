# Database and schema config

This page collects the runtime knobs that control connection setup, schema
materialization, and context size.

## SQLChatAgent

### Connection setup

Provide **one** of the following:

- `database_uri` for SQLAlchemy to create an engine, or
- `database_session` if you already have a bound SQLAlchemy session.

Use a `database_session` when you want to reuse an existing fixture or an open
transaction. Use `database_uri` when the agent should own its own engine.

### Schema/context shape

`context_descriptions` should look like this:

```python
{
    "table_name": {
        "description": "table-level meaning",
        "columns": {
            "column_a": "column meaning",
            "column_b": "column meaning",
        },
    }
}
```

Notes:

- The runtime metadata path consumes the `description` and `columns` keys.
- If you need relationship hints, fold them into the table description text.
- When `multi_schema=True`, use schema-qualified keys such as
  `schema_name.table_name`.
- If no explicit context descriptions are supplied, the agent can auto-extract
  descriptions from table and column comments for PostgreSQL and MySQL; other
  dialects fall back to empty descriptions.

### Schema helper tools

Set `use_schema_tools=True` to enable the SQL schema tools:

- `get_table_names`
- `get_table_schema`
- `get_column_descriptions`

This is useful for large or sparsely documented schemas.

### SQL helper agent

`use_helper=True` creates a helper agent automatically. It is meant to recover
from cases where the main agent seems to have intended a tool call but did not
emit one cleanly.

### Result and context limits

- `max_result_rows` limits the number of returned SQL rows.
- `max_retained_tokens` limits how much query-result text is kept in tool
  history.

## SQLite / PostgreSQL / MySQL notes

- SQLite is the easiest local choice for smoke checks and unit-style examples.
  Use URIs such as `sqlite:///file.db` or `sqlite:///:memory:`.
- PostgreSQL usually needs the SQL extra plus the native client libraries.
  If a build complains about `pg_config`, install the PostgreSQL development
  package for your platform or use `psycopg2-binary` in a trusted environment.
- MySQL works through SQLAlchemy URIs such as `mysql+pymysql://user:pass@host/db`.
  Table and column comments, when present, are used to enrich context.

## Neo4jChatAgent

### Connection setup

Use `Neo4jSettings` with:

- `uri`
- `username`
- `password`
- `database`

`Neo4jSettings` reads from the `NEO4J_` environment prefix when you want to use
environment-based configuration.

### Schema context

- `kg_schema` can seed the schema if you already know it.
- `use_schema_tools=True` keeps schema discovery in the conversational loop.
- `graph_schema_tool` remains available for schema refreshes even when the
  schema is preseeded.

## ArangoChatAgent

### Connection setup

Use `ArangoSettings` with either a prebuilt `client` and `db`, or:

- `url`
- `username`
- `password`
- `database`

`ArangoSettings` reads from the `ARANGO_` environment prefix when needed.

### Schema context

- `prepopulate_schema=True` seeds the schema before the conversation starts.
- `kg_schema` can hold a cached schema snapshot.
- `schema_sample_pct` controls how much example data is sampled when building
  schema context.
- `max_schema_fields` caps schema size before the agent trims the response.
- `max_num_results` bounds returned AQL rows.
- `max_tries` limits how many tool attempts the agent makes before giving up.

## CSVGraphAgent

- Inherits the Neo4j settings and reuses the Neo4j safety gate.
- Accepts CSV data or a DataFrame.
- Uses the header and a small sample of rows to propose graph structure.
- Sends row-wise Cypher through `PandasToKGTool`, so the argument order must
  line up with the CSV headers.

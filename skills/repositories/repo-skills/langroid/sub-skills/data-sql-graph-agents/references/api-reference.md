# API reference

This page names the structured-data entry points and the safety-sensitive
runtime objects that this sub-skill covers.

## Table and CSV analysis

| Component | Purpose | Notes |
| --- | --- | --- |
| `TableChatAgentConfig` | Config for tabular Q&A | `data` can be a DataFrame, file path, or URL. `full_eval` defaults to `False`. |
| `TableChatAgent` | Chat over a DataFrame-backed dataset | Normalizes column names, builds a dataframe summary, and enables `PandasEvalTool`. |
| `PandasEvalTool` | Evaluate a pandas expression on `df` | The expression must return a value. Use `df.assign(...)` for mutations. |

## SQL

| Component | Purpose | Notes |
| --- | --- | --- |
| `SQLChatAgentConfig` | Config for SQLAlchemy-backed DB chat | Use `database_uri` or `database_session`. Default allowlist is `['SELECT']`; `allow_dangerous_operations` defaults to `False`. |
| `SQLChatAgent` | Chat with a SQL database | Builds metadata, schema descriptions, query tools, and an optional helper agent automatically. |
| `SQLHelperAgent` | Intent-recovery helper | Created automatically when `use_helper=True`. |
| `RunQueryTool` | Execute an SQL statement | The main query tool for the agent. |
| `GetTableNamesTool` | List tables | Enabled when schema tools are active. |
| `GetTableSchemaTool` | Fetch table schema | Takes a list of table names. |
| `GetColumnDescriptionsTool` | Fetch column descriptions | Takes one table plus a comma-separated column list. |

## Neo4j

| Component | Purpose | Notes |
| --- | --- | --- |
| `Neo4jSettings` | Connection settings | Fields: `uri`, `username`, `password`, `database`. Reads from the `NEO4J_` env prefix. |
| `Neo4jChatAgentConfig` | Config for Neo4j graph chat | `allow_dangerous_operations` defaults to `False`. `use_schema_tools` defaults to `True`. |
| `Neo4jChatAgent` | Chat with a Neo4j graph | Enables graph schema, retrieval, and creation tools. |
| `GraphSchemaTool` | Inspect graph schema | Returns the schema visualization or cached schema. |
| `CypherRetrievalTool` | Read Cypher | Read-only by default. |
| `CypherCreationTool` | Write Cypher | Used for graph mutations. |
| `validate_cypher_query` | Safety gate for Cypher | Blocks unsafe queries unless the operator explicitly opts in. |

## ArangoDB

| Component | Purpose | Notes |
| --- | --- | --- |
| `ArangoSettings` | Connection settings | Fields: `client`, `db`, `url`, `username`, `password`, `database`. Reads from the `ARANGO_` env prefix. |
| `ArangoChatAgentConfig` | Config for Arango graph chat | `allow_dangerous_operations` defaults to `False`. `prepopulate_schema` defaults to `True`. |
| `ArangoChatAgent` | Chat with an ArangoDB graph | Enables schema, retrieval, and creation tools. |
| `ArangoSchemaTool` | Inspect graph schema | Can target specific collections or properties. |
| `AQLRetrievalTool` | Read AQL | Read-only by default. |
| `AQLCreationTool` | Write AQL | Used for graph or document mutations. |
| `validate_aql_query` | Safety gate for AQL | Blocks unsafe queries unless the operator explicitly opts in. |

## CSV to knowledge graph

| Component | Purpose | Notes |
| --- | --- | --- |
| `CSVGraphAgentConfig` | Config for CSV-to-KG setup | Inherits Neo4j settings and CSV input fields. |
| `CSVGraphAgent` | Build a graph from CSV rows | Infers graph structure from headers and sample rows. |
| `PandasToKGTool` | Generate row-wise Cypher | The generated Cypher must be validated before each write. |

## Safe defaults worth remembering

- Table chat sanitizes pandas expressions by default.
- SQL starts with `SELECT` only.
- Neo4j and Arango query validation are off only when the operator explicitly
  opts in.
- CSVGraphAgent reuses the Neo4j Cypher safety gate before any row write.

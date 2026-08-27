# Data agent workflows

Use the smallest workflow that matches the data shape and trust boundary.

## 1) Table / CSV / Pandas chat

Use this when the data already fits in a DataFrame or can be loaded from a CSV
or URL.

Typical shape:

```python
agent = TableChatAgent(
    TableChatAgentConfig(
        data=df_or_path_or_url,
        full_eval=False,
    )
)
```

Workflow notes:

- `TableChatAgent` normalizes column names and summarizes the dataframe before
  asking the model to reason over it.
- Keep `full_eval=False` for untrusted input.
- For data cleaning, prefer expressions that return a new dataframe, such as
  `df.assign(...)`, instead of in-place assignment.
- If the source is a delimited file, the loader can auto-detect the separator in
  most cases.

## 2) SQL database chat

Use this when the source of truth is a relational database.

Typical shape:

```python
agent = SQLChatAgent(
    SQLChatAgentConfig(
        database_uri="sqlite:///example.db",
        context_descriptions=context,
        use_schema_tools=True,
    )
)
```

Workflow notes:

- Provide `database_uri` or a bound `database_session`.
- Add `context_descriptions` when you already know the schema meaning.
- Set `use_schema_tools=True` when the schema is large or only partially known.
- Keep `use_helper=True` if you want the built-in helper agent to recover from
  missing or muddled tool intent.
- Use `allowed_statement_types` to permit a narrow write set only when writes
  are intended.

## 3) Neo4j graph chat

Use this when the data is already modeled as a property graph or when you want
Cypher-based graph reasoning.

Typical shape:

```python
agent = Neo4jChatAgent(
    Neo4jChatAgentConfig(
        neo4j_settings=Neo4jSettings(
            uri="neo4j://host:7687",
            username="neo4j",
            password="secret",
            database="neo4j",
        ),
        use_schema_tools=True,
    )
)
```

Workflow notes:

- If the schema is not already known, let the agent use `graph_schema_tool`
  first.
- Use `cypher_retrieval_tool` for reads and `cypher_creation_tool` for graph
  writes.
- When the schema is already known, seed `kg_schema` to avoid an extra schema
  round-trip.

## 4) ArangoDB graph chat

Use this when the graph lives in ArangoDB or when you want AQL-driven graph or
collection reasoning.

Typical shape:

```python
agent = ArangoChatAgent(
    ArangoChatAgentConfig(
        arango_settings=ArangoSettings(
            url="http://host:8529",
            username="root",
            password="secret",
            database="graphdb",
        ),
        prepopulate_schema=True,
    )
)
```

Workflow notes:

- Use `arango_schema_tool` before `aql_retrieval_tool` when the schema is not
  already seeded.
- `aql_retrieval_tool` is for reads; `aql_creation_tool` is for writes.
- For very large schemas, request only the collections you need or disable
  property-heavy schema output for the first pass.

## 5) CSV to knowledge graph

Use this when you have a CSV and need to infer a graph model before writing
Neo4j data.

Typical shape:

```python
agent = CSVGraphAgent(
    CSVGraphAgentConfig(
        data=csv_or_dataframe,
        neo4j_settings=Neo4jSettings(...),
    )
)
```

Workflow notes:

- The agent looks at the header and sample rows, then asks for a Cypher plan.
- `PandasToKGTool` should emit placeholders that line up with the CSV headers.
- Every generated Cypher write is validated before the first row is inserted.

## Practical selection guide

- Use TableChatAgent for local ad hoc analysis.
- Use SQLChatAgent when the database already encodes the schema.
- Use Neo4jChatAgent for labeled graph traversals and Cypher-based writes.
- Use ArangoChatAgent for AQL graph or collection workflows.
- Use CSVGraphAgent when the data starts as a flat file but needs graph shape.

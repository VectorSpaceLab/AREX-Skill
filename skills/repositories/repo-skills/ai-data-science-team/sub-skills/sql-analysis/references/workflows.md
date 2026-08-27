# SQL workflows

These workflows are distilled for future operation from an installed `ai-data-science-team` package. They avoid source-checkout dependencies and default to safe, read-only behavior.

## Metadata only: no LLM call

Use this when the user asks what is in a database, when preparing a prompt for a separate model, or when debugging table/column names before running an agent.

```python
import json
import sqlalchemy as sql
from ai_data_science_team.tools.sql import get_database_metadata

engine = sql.create_engine("sqlite:///example.db")
metadata = get_database_metadata(engine, n_samples=1)

# Redact or omit connection_url before sharing outside the local task.
metadata_for_report = dict(metadata)
metadata_for_report.pop("connection_url", None)
print(json.dumps(metadata_for_report, indent=2, default=str))
```

Expected metadata shape:

```text
{
  "dialect": "sqlite",
  "driver": "pysqlite",
  "connection_url": "...",
  "schemas": [
    {
      "schema_name": "main",
      "tables": [
        {
          "table_name": "orders",
          "columns": [{"name": "amount", "type": "FLOAT", "sample_values": [...]}],
          "primary_key": [...],
          "foreign_keys": [...],
          "indexes": [...]
        }
      ]
    }
  ]
}
```

## Direct `SQLDatabaseAgent` workflow

Use this when a caller has already chosen a model and wants the package to generate and execute one SQL query.

```python
import pandas as pd
import sqlalchemy as sql
from ai_data_science_team.agents import SQLDatabaseAgent

engine = sql.create_engine("sqlite:///example.db")
llm = ...  # caller-provided LangChain-compatible chat model

agent = SQLDatabaseAgent(
    model=llm,
    connection=engine,
    n_samples=1,
    safe_mode=True,
    log=False,
    bypass_recommended_steps=True,
    bypass_explain_code=True,
)

agent.invoke_agent(
    user_instructions="List total revenue by customer for shipped orders.",
    max_retries=3,
    retry_count=0,
)

response = agent.get_response()
if response and response.get("sql_database_error"):
    raise RuntimeError(response["sql_database_error"])

sql_query = agent.get_sql_query_code()
result = agent.get_data_sql()
result_df = pd.DataFrame(result) if isinstance(result, dict) else result
```

Operational checks after invocation:

1. Read `agent.get_sql_query_code()` and confirm it answers the question without writes.
2. Check `agent.get_response().get("sql_database_error")` before using the result.
3. Convert `get_data_sql()` to a DataFrame only after confirming it is a dictionary-like result.
4. If the query failed because a table or column was missing, rerun metadata inspection and ask the agent for a more schema-faithful query.

## Factory graph workflow

Use the factory when the caller wants direct graph control instead of the wrapper object.

```python
import sqlalchemy as sql
from ai_data_science_team.agents import make_sql_database_agent

engine = sql.create_engine("sqlite:///example.db")
llm = ...

graph = make_sql_database_agent(
    model=llm,
    connection=engine,
    n_samples=1,
    safe_mode=True,
    log=False,
)

response = graph.invoke({
    "user_instructions": "Show the 10 most recent invoices.",
    "max_retries": 3,
    "retry_count": 0,
})
```

Graph responses contain the same SQL, data, and error keys documented in [the API reference](api-reference.md#response-keys-to-check).

## Large schema or token-pressure workflow

Symptoms include provider context-length errors, very slow metadata prompts, or generated SQL that ignores relevant tables because the metadata was too large.

1. Keep `n_samples=1` or reduce it for sensitive/wide tables.
2. If the database is very large, connect to a narrower schema, view, replica, or read-only user whose visibility is already limited to task-relevant tables.
3. Turn on `smart_schema_pruning=True` only when an additional LLM call is acceptable:

```python
agent = SQLDatabaseAgent(
    model=llm,
    connection=engine,
    n_samples=1,
    safe_mode=True,
    smart_schema_pruning=True,
)
```

4. Ask for a narrower task: table names, date range, entity, and output columns.
5. If the generated query still references missing fields, run metadata-only inspection and feed the exact table/column names back into the next user instruction.

## Human-in-the-loop review

Use this only when a human review step is useful before code generation. Human review requires graph checkpointing and should not be combined with bypassing recommended steps.

```python
from langgraph.checkpoint.memory import MemorySaver
from ai_data_science_team.agents import SQLDatabaseAgent

agent = SQLDatabaseAgent(
    model=llm,
    connection=engine,
    n_samples=1,
    safe_mode=True,
    human_in_the_loop=True,
    bypass_recommended_steps=False,
    checkpointer=MemorySaver(),
)
```

The review prompt asks whether the SQL agent instructions are correct. If the user supplies modifications, the graph loops back through recommended-step generation.

## App-derived operational cues

The package's SQL app pattern is useful as a workflow cue, but app launching belongs to the sibling `multiagent-and-app-workflows` sub-skill. The distilled SQL-specific pattern is:

- Present example database questions to the user.
- Create a SQLAlchemy engine and connection from the selected database URI.
- Let the UI/session layer perform provider setup and instantiate the model.
- Instantiate `SQLDatabaseAgent(model=llm, connection=conn, n_samples=1, log=False, bypass_recommended_steps=True)`.
- Invoke asynchronously in the UI handler.
- Display the generated SQL first, then the returned table.
- Do not run or launch the app by default during non-interactive agent work.

## SQL result handoff

`SQLDatabaseAgent.get_data_sql()` returns a dictionary after the package post-processes a DataFrame with `.to_dict()`. For downstream pandas or charting work:

```python
import pandas as pd

data = agent.get_data_sql()
if data is None:
    raise RuntimeError(agent.get_response().get("sql_database_error", "No SQL data returned"))

df = pd.DataFrame(data)
```

For visualization, hand `df` and the user's chart request to the sibling `dataframe-code-agents` sub-skill. For a combined SQL-plus-visualization agent, route to the sibling `multiagent-and-app-workflows` sub-skill.

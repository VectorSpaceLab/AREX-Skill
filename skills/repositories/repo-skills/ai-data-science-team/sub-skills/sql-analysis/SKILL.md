---
name: sql-analysis
description: "Operate ai-data-science-team SQL database querying, metadata
  inspection, read-only SQL safety, and SQLDatabaseAgent workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SQL Analysis

Use this sub-skill when the task is to query a SQL database with `ai-data-science-team`, summarize database metadata, validate generated SQL for read-only safety, or operate `SQLDatabaseAgent` / `make_sql_database_agent` directly.

## Route here for

- SQLAlchemy engine or connection setup for a database that will be queried by `SQLDatabaseAgent`.
- Metadata summaries with `ai_data_science_team.tools.sql.get_database_metadata`.
- Natural-language-to-SQL workflows where the caller supplies an already configured LLM object.
- Checking that generated SQL is read-only with the package's `_validate_sql` implementation or the bundled smoke script.
- Interpreting `SQLDatabaseAgent` response fields such as `sql_query_code`, `data_sql`, `sql_database_function`, and `sql_database_error`.

## Route away

- For `SQLDataAnalyst` composition, supervisor workflows, or Streamlit app launching, use the sibling `multiagent-and-app-workflows` sub-skill.
- For charting or Plotly visualization of SQL results, use the sibling `dataframe-code-agents` sub-skill after converting the SQL result dict to a DataFrame.
- For file loading, direct DataFrame EDA, or optional EDA reports, use the sibling `data-access-and-eda` sub-skill.
- For H2O AutoML, model evaluation, or MLflow tools, use the sibling `modeling-and-mlflow` sub-skill.

## Safe operating defaults

1. Use a read-only database account or a disposable database copy whenever possible.
2. Keep `safe_mode=True` unless the user explicitly accepts the risk and the database account itself is read-only.
3. Start with `n_samples=1` for metadata; increase only when sample values are necessary and safe to share.
4. Do not launch Streamlit apps, call external LLM providers, download data, or write generated SQL logs unless the user asked for that side effect.
5. Redact hostnames, database names, usernames, and connection URLs before sharing metadata or logs outside the local task.

## Core workflow

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
agent.invoke_agent("Return sales by month for 2024", max_retries=3, retry_count=0)

query = agent.get_sql_query_code()
data = agent.get_data_sql()
frame = pd.DataFrame(data) if isinstance(data, dict) else data
error = agent.get_response().get("sql_database_error") if agent.get_response() else None
```

If the user only needs schema understanding, avoid LLM calls and use `get_database_metadata` as shown in [workflows](references/workflows.md#metadata-only-no-llm-call).

## References and bundled checks

- [API reference](references/api-reference.md): signatures, imports, response fields, and public/private boundary notes.
- [Workflows](references/workflows.md): metadata-only inspection, direct agent use, factory graph use, large-schema handling, and app-derived cues.
- [SQL safety and metadata](references/sql-safety-and-metadata.md): what `_validate_sql` does and does not guarantee, and how metadata is sampled.
- [Troubleshooting](references/troubleshooting.md): symptom/cause/recovery table for imports, validation, token pressure, connection errors, and app/provider issues.
- [Smoke script](scripts/smoke_sql_safety.py): local in-memory SQLite metadata and read-only safety check with no LLM call or external service.

# Conversational Analysis Troubleshooting

## Missing LLM configuration

**Symptom**: `.chat()` raises an error saying PandasAI API key does not include
LLM credits or asks to configure an OpenAI/LiteLLM key.

**Cause**: `pai.config.get().llm` is `None`.

**Fix**:

```python
import os
import pandasai as pai
from pandasai_litellm.litellm import LiteLLM

llm = LiteLLM(model="gpt-4.1-mini", api_key=os.environ["OPENAI_API_KEY"])
pai.config.set({"llm": llm})
```

For offline tests, use `FakeLLM`; do not require real provider keys.

## `ExecuteSQLQueryNotUsed`

**Symptom**: Generated code fails validation with a message that it must execute
SQL queries using `execute_sql_query`.

**Cause**: The generated code directly manipulated variables or pandas objects
instead of retrieving data through the package-provided SQL function.

**Fix**: Regenerate or patch the generated code:

```python
df = execute_sql_query('SELECT COUNT(*) AS total FROM table_a')
result = {'type': 'number', 'value': int(df['total'].iloc[0])}
```

For multiple tables, use the exact schema names registered on the DataFrames.

## Unauthorized table names

**Symptom**: `MaliciousQueryError: Query uses unauthorized table: ...`.

**Cause**: The generated SQL references a table name not present in the agent's
DataFrame list. File and dataset names are sanitized: hyphens and special
characters often become underscores.

**Fix**:

```python
print(df.schema.name)
```

Use that table name in generated SQL. For semantic datasets created from a path
such as `demo-org/sales-data`, the schema/table name is usually `sales_data`.

## Invalid result dictionary

**Symptom**: `InvalidOutputValueMismatch`, `NoResultFoundError`, or a response
object with the wrong type.

**Cause**: `result` is missing, has no `type`/`value` keys, uses an unsupported
`type`, or pairs a type with the wrong value shape.

**Fix**: Follow the response table in `response-formats.md`. For example:

```python
result = {'type': 'dataframe', 'value': df}
result = {'type': 'plot', 'value': 'chart.png'}
```

## Follow-up without existing conversation

**Symptom**: `ValueError: No existing conversation. Please use chat() to start a
new conversation.`

**Cause**: `pai.follow_up` or `DataFrame.follow_up` was called before a matching
`chat` call initialized an agent.

**Fix**: Start with `pai.chat(query, df)` or `df.chat(query)`, or use an explicit
`Agent` object and call `agent.chat(...)` first.

## Multi-DataFrame source incompatibility

**Symptom**: `ValueError` about incompatible dataset sources.

**Cause**: A list of virtual/semantic DataFrames mixes incompatible source
families, such as local file sources and remote SQL sources that cannot be
queried together.

**Fix**: Query compatible groups separately, materialize data into a common local
format, or create a semantic view only from compatible sources.

## Chart display problems

**Symptom**: A chart response tries to open a GUI viewer or fails in headless CI.

**Cause**: `ChartResponse.__str__()` calls display behavior.

**Fix**: Avoid printing the whole response in automation. Use:

```python
if response.type == 'chart':
    response.save('output.png')
```

## Legacy wrapper warning

**Symptom**: `DeprecationWarning` from `SmartDataframe` or `SmartDatalake`.

**Fix**: For new code, migrate to `pai.DataFrame`, `pai.chat`, or `Agent`. Keep
legacy wrappers only when maintaining existing v2-style code.

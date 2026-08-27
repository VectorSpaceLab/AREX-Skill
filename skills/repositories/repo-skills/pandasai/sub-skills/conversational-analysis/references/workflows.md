# Conversational Analysis Workflows

## Basic single-dataframe chat

```python
import os
import pandasai as pai
from pandasai_litellm.litellm import LiteLLM

llm = LiteLLM(model="gpt-4.1-mini", api_key=os.environ["OPENAI_API_KEY"])
pai.config.set({"llm": llm, "save_logs": True, "verbose": False, "max_retries": 3})

df = pai.read_csv("sales.csv")
response = df.chat("What is total revenue by region?")
print(response.value)
print(response.type)
print(response.last_code_executed)
```

Use `pai.read_csv` when a file should become a PandasAI `DataFrame`. Use the
semantic-layer sub-skill when the user needs persistent datasets, schemas,
transformations, or views.

## Multiple DataFrames

```python
import pandasai as pai

customers = pai.DataFrame({"customer_id": [1, 2], "name": ["A", "B"]})
orders = pai.DataFrame({"customer_id": [1, 2], "amount": [10, 20]})

response = pai.chat("Which customer has the highest order amount?", customers, orders)
print(response.value)
```

Use `pai.chat` for a fresh global conversation over several dataframes. If the
user needs explicit object ownership or a long-lived app object, instantiate
`Agent` directly.

## Explicit Agent with follow-up memory

```python
from pandasai import Agent, DataFrame

sales = DataFrame({"year": [2024, 2025], "revenue": [10, 15]})
agent = Agent([sales], memory_size=10, description="Sales analysis assistant")
first = agent.chat("What is total revenue?")
second = agent.follow_up("What was the year-over-year change?")
```

`Agent.chat` starts a new conversation by clearing memory. `Agent.follow_up`
continues without clearing memory. `DataFrame.chat` reuses an internal agent on
that DataFrame after the first call.

## Deterministic offline smoke with FakeLLM

Use this when validating code paths without provider credentials:

```python
import pandasai as pai
from pandasai.llm.fake import FakeLLM

code = """
df = execute_sql_query('SELECT COUNT(*) AS total FROM table_a')
result = {'type': 'number', 'value': int(df['total'].iloc[0])}
"""

pai.config.set({"llm": FakeLLM(code)})
df = pai.DataFrame({"a": [1, 2]}, _table_name="table_a")
response = df.chat("count rows")
assert response.type == "number"
assert response.value == 2
```

Or run the bundled helper:

```bash
python sub-skills/conversational-analysis/scripts/offline_chat_smoke.py
```

## Response inspection pattern

```python
response = df.chat("Plot sales by month")

if response.type == "chart":
    response.save("sales_by_month.png")
elif response.type == "dataframe":
    print(response.value.head())
elif response.type == "number":
    print(float(response.value))
elif response.type == "error":
    print(response.error)
else:
    print(str(response.value))

print(response.last_code_executed)
```

Do not judge success by `print(response)` alone. For charts, printing can try to
show an image; for error responses, inspect `error` and `last_code_executed`.

## Migrating old SmartDataframe code

Old style:

```python
from pandasai import SmartDataframe

df = SmartDataframe(raw_df, config={"llm": llm})
df.chat("summarize")
```

Preferred v3 style:

```python
import pandasai as pai

pai.config.set({"llm": llm})
df = pai.DataFrame(raw_df)
response = df.chat("summarize")
```

For `SmartDatalake`, replace wrapper construction with either `pai.chat(query,
*dfs)` for quick sessions or `Agent(dfs)` for explicit multi-turn sessions.

## Sandboxed chat handoff

When data or prompts are untrusted, first select a sandbox using the
sandbox-and-security sub-skill, then pass it into PandasAI chat:

```python
# sandbox = DockerSandbox(); sandbox.start()
response = df.chat("analyze suspicious user input", sandbox=sandbox)
# sandbox.stop()
```

Never imply that sandboxing is automatic. It is only used when a `Sandbox`
instance is passed.

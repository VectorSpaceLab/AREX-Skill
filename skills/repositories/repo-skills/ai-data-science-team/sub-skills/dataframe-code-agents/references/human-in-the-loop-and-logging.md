# Human-in-the-loop and logging

This package has two independent review/debugging mechanisms:

- **Human-in-the-loop review** pauses the graph after generated code executes so a human can accept or request changes.
- **Logging** writes generated functions and generated-execution errors to a caller-selected directory when `log=True`.

Both are optional. Use them deliberately because they change run behavior.

## Human-in-the-loop behavior

Set `human_in_the_loop=True` on any of the four class wrappers:

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from ai_data_science_team.agents import FeatureEngineeringAgent

checkpointer = MemorySaver()
agent = FeatureEngineeringAgent(
    model=llm,
    human_in_the_loop=True,
    checkpointer=checkpointer,
    log=False,
)
```

If `human_in_the_loop=True` and no checkpointer is supplied, the package creates an in-memory `MemorySaver()` and prints a notice. Prefer supplying a checkpointer explicitly when the run must be resumed reliably.

When human review is enabled:

1. The graph recommends steps unless `bypass_recommended_steps` was requested.
2. The graph generates code and runs it in the sandbox.
3. If execution failed and retries remain, the graph repairs code before review.
4. The graph interrupts at `human_review` with the recommended steps plus generated code.
5. A response of `"yes"` accepts the current code.
6. Any other response is appended to user instructions as a modification request and routes back to the recommendation step.

If `bypass_recommended_steps=True` is combined with human review, the package forces recommendations back on because review needs the recommendation step.

## Review/resume pattern

Use a stable `thread_id` in `config`.

```python
config = {"configurable": {"thread_id": "feature-review-1"}}

agent.invoke_agent(
    data_raw=df,
    user_instructions="Prepare generic model features while preserving the target.",
    target_variable="target",
    max_retries=2,
    retry_count=0,
    config=config,
)
```

Inspect the interrupt text:

```python
state = agent.get_state(config=config)
review_text = state.tasks[-1].interrupts[-1].value
print(review_text)
```

Request a change:

```python
agent.invoke(
    Command(resume="Keep boolean columns as booleans; do not convert them to integers."),
    config=config,
)
```

Accept the revised result:

```python
agent.invoke(Command(resume="yes"), config=config)
```

Then retrieve output normally:

```python
feature_df = agent.get_data_engineered()
response = agent.get_response()
```

## Agent-specific review prompts

| Agent | Review prompt intent | `yes` route when `bypass_explain_code=False` | Modification route |
|---|---|---|---|
| `DataCleaningAgent` | Confirm cleaning instructions and generated cleaner code. | `report_agent_outputs` | `recommend_cleaning_steps` |
| `DataWranglingAgent` | Confirm wrangling instructions and generated wrangler code. | `report_agent_outputs` | `recommend_wrangling_steps` |
| `DataVisualizationAgent` | Confirm visualization instructions and generated chart code. | `report_agent_outputs` | `chart_instructor` |
| `FeatureEngineeringAgent` | Confirm feature engineering instructions and generated feature code. | `report_agent_outputs` | `recommend_feature_engineering_steps` |

When `bypass_explain_code=True`, accepting review routes to graph end instead of the report node.

## Writing useful modification requests

Good review edits are concrete and bounded:

- “Preserve the target column exactly named `target`.”
- “Do not drop rows; impute missing values instead.”
- “Join on `customer_id` and keep one output row per customer.”
- “Use a box chart, not a histogram, and put `segment` on the x-axis.”
- “Avoid one-hot encoding columns with more than 100 distinct values; bucket rare categories first.”

Avoid vague edits such as “make it better” or “try again.” They usually lead to repeated model-generation failures.

## Logging behavior

Logging is controlled by constructor parameters:

```python
agent = DataCleaningAgent(
    model=llm,
    log=True,
    log_path="agent-logs",
    file_name="cleaner_candidate.py",
    overwrite=False,
)
```

| Parameter | Effect |
|---|---|
| `log=True` | Enables generated function and generated-execution error files. |
| `log=False` | No generated function/error files are written by the logging helpers. |
| `log_path=None` with `log=True` | The package uses its default `logs/` directory under the current process working directory. |
| `file_name` | Controls the generated function file name. |
| `overwrite=True` | Reuses the same generated function file path. |
| `overwrite=False` | Creates a unique suffix if a generated function file already exists. |

The generated function path is returned in the response only when logging is enabled:

| Agent | Function path key | Error log key |
|---|---|---|
| Cleaning | `data_cleaner_function_path` | `data_cleaner_error_log_path` |
| Wrangling | `data_wrangler_function_path` | `data_wrangler_error_log_path` |
| Visualization | `data_visualization_function_path` | `data_visualization_error_log_path` |
| Feature engineering | `feature_engineer_function_path` | `feature_engineer_error_log_path` |

## Logging-safe retrieval

Do not rely on generated function paths for portability. Prefer the in-memory getter when available:

```python
code_text = agent.get_data_cleaner_function(markdown=False)
```

Use function paths only for local debugging in the current run. If `log=False`, path keys will normally be `None`.

## Combining logging, retry, and review

A conservative interactive debug setup:

```python
from langgraph.checkpoint.memory import MemorySaver

agent = DataWranglingAgent(
    model=llm,
    n_samples=10,
    log=True,
    log_path="agent-logs",
    overwrite=False,
    human_in_the_loop=True,
    checkpointer=MemorySaver(),
)

config = {"configurable": {"thread_id": "wrangling-review-1"}}

agent.invoke_agent(
    data_raw=[left_df, right_df],
    user_instructions="Join on id and return one row per id with total amount.",
    max_retries=2,
    retry_count=0,
    config=config,
)
```

If the generated function fails, inspect the relevant `*_error` field and any error log path. If it reaches review, inspect the interrupt and resume with either `"yes"` or a specific modification.

## When not to use human review

Avoid `human_in_the_loop=True` for unattended scripts, batch jobs, or app paths that cannot handle LangGraph interrupts. Use a lower `max_retries`, inspect the response dict, and rerun with clearer instructions instead.

# Logging, token counting, and debugging

## Purpose

Read this when a LaVague WebAgent run produces surprising output, stalls, spends unexpected tokens, or needs inspection of retrieved HTML nodes/action code.

## Bound the run first

During debugging, reduce cost and side effects:

```python
agent = WebAgent(world_model, action_engine, n_steps=3)
result = agent.run("...", display=False, log_to_db=False)
```

Use `n_steps` to cap planning/action loops. Use `step_by_step=True` only in an interactive terminal because it waits for `input()` between steps.

## Inspect the result

```python
result = agent.run("Extract the support email")
print(result.success)
print(result.output)
print(result.instruction)
print(result.code)
print(result.total_estimated_tokens)
print(result.total_estimated_cost)
```

- `success=True` with `output='[NONE]'` can be normal for action-only objectives.
- `result.code` is useful for reviewing generated browser action code, but do not execute it blindly on a different page state.
- Token and cost fields require a `TokenCounter` and callback metadata from the selected model stack.

## Use a logger

```python
from lavague.core.logger import AgentLogger, LocalLogger, LocalDBLogger
from lavague.core.token_counter import TokenCounter

logger = AgentLogger()
token_counter = TokenCounter(log=True)
agent = WebAgent(world_model, action_engine, logger=logger, token_counter=token_counter)
result = agent.run("Find the page title")
logs = logger.return_pandas()
```

Logger choices:

| Logger | Use | Caution |
| --- | --- | --- |
| `AgentLogger()` | In-memory debugging in notebooks or scripts. | Logs may contain objectives, generated code, page text, and screenshots/observations. |
| `LocalLogger(path)` | Persist JSON-like logs for a single run/session. | Choose a safe path and avoid sensitive data. |
| `LocalDBLogger(db_name='lavague_logs.db')` | SQLite logs, often via `agent.run(..., log_to_db=True)`. | Creates a local database; do not enable where persistent files are prohibited. |

## Display retrieved nodes

After a run with navigation engine logs:

```python
agent.display_previous_nodes(steps=1)
agent.display_all_nodes()
```

These methods display retrieved HTML snippets and visual nodes in notebook-style environments. If they print "No previous nodes available", either the run did not reach the navigation engine, the logs were cleared, or the selected logger did not capture `engine_log`.

## Profile summary

```python
plot, table = agent.get_summary()
```

This returns a waterfall-style plot and summary table from profiling state, then clears the profiling data. Use it after a bounded run when users ask where time was spent.

## Debug loop patterns

### The objective completes too early

- Inspect `world_model_output` in logs if available.
- Make the objective more explicit about returned information versus performed action.
- Provide `user_data` with constraints or expected answer format.
- If screenshots show the needed data but no text extraction occurs, ask for a Python Engine extraction step in the objective.

### Navigation repeatedly fails

- Route browser/session/iframe/tab issues to `../browser-drivers/SKILL.md`.
- Display previous nodes to see whether the target element was retrieved.
- Try a more specific instruction/objective phrase naming visible labels.
- Consider a custom retriever pipeline in `../contexts-and-retrievers/SKILL.md` if retrieved nodes are consistently irrelevant.

### The run spends too many tokens

- Lower `n_steps` while debugging.
- Use `TokenCounter(log=True)` and inspect `result.total_estimated_cost`.
- Avoid broad objectives such as "analyze the whole site" without a stop condition.
- Prefer a direct Python Engine extraction if data is already visible in current state.

### Logs contain sensitive data

- Stop the run and confirm whether telemetry/logging is allowed.
- Set `LAVAGUE_TELEMETRY=NONE` before importing/running LaVague when telemetry must be disabled.
- Do not enable `log_to_db=True` for sensitive sessions unless the user explicitly wants persistent logs.

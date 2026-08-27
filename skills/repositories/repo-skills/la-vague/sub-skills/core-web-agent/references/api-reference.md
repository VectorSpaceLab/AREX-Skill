# Core WebAgent API reference

## Purpose

Read this when you need verified constructor names, method names, arguments, and return fields for LaVague core workflows. These facts were confirmed from installed package inspection and source evidence.

## Primary package imports

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.core.python_engine import PythonEngine
from lavague.core.navigation import NavigationEngine, NavigationControl
from lavague.core.token_counter import TokenCounter
from lavague.core.logger import AgentLogger, LocalLogger, LocalDBLogger
```

The installed bundle package is `lavague`; core APIs come from the `lavague-core` distribution and import under `lavague.core`.

## Main constructors

### `WorldModel`

```python
WorldModel(mm_llm=None, prompt_template=<default world-model prompt>, examples=<default examples>, logger=None)
```

- Converts a global objective plus current browser/page state into the next engine and instruction.
- Uses a multimodal LLM by default. Pass `mm_llm` directly or use `WorldModel.from_context(context)` when using a provider context.
- `add_knowledge(...)` can add long-form supporting information for task planning; route context and retrieval details to `../contexts-and-retrievers/SKILL.md`.

### `ActionEngine`

```python
ActionEngine(
    driver,
    navigation_engine=None,
    python_engine=None,
    navigation_control=None,
    llm=None,
    embedding=None,
    retriever=None,
    prompt_template=<default action prompt>,
    extractor=<DynamicExtractor>,
    time_between_actions=1.5,
    n_attempts=5,
    logger=None,
    extraction_llm=None,
)
```

- Owns the per-step execution engines.
- `driver` is required and must implement LaVague's `BaseDriver` interface.
- `navigation_engine` performs RAG over current HTML and generates browser action code.
- `python_engine` is for computation/extraction that does not navigate.
- `navigation_control` handles lighter controls such as wait/back/scan/scroll/switch-tab/maximize.
- Use `ActionEngine.from_context(context, driver)` to populate `llm`, `embedding`, and default provider-bound pieces from a context.

### `WebAgent`

```python
WebAgent(world_model, action_engine, token_counter=None, n_steps=10, clean_screenshot_folder=True, logger=None)
```

- Coordinates `WorldModel`, `ActionEngine`, short-term memory, logging, screenshots, and token counting.
- `n_steps` is the maximum planning/execution loop count.
- `clean_screenshot_folder=True` deletes a local `screenshots/` folder if it exists; turn it off if that folder must be preserved.
- `token_counter` enables cost/token updates on the returned result and log rows.
- `logger` defaults to in-memory `AgentLogger`.

## WebAgent methods

| Method | Use | Notes |
| --- | --- | --- |
| `agent.get(url)` | Navigate to the starting URL before a run. | Calls the driver and appends setup/navigation code to the accumulated result. |
| `agent.run(objective, user_data=None, display=False, log_to_db=False, step_by_step=False)` | Run the full objective loop. | Returns an `ActionResult`. Use `step_by_step=True` only in interactive sessions. |
| `agent.run_step(objective)` | Execute one world-model/action-engine step. | Useful for debugging and manual loops. Returns when complete/success. |
| `agent.prepare_run(display=False, user_data=None)` | Initialize state/logs before custom loops. | Called internally by `run`. |
| `agent.demo(objective='', user_data=None, screenshot_ratio=1)` | Launch Gradio demo. | Requires `lavague-gradio`; route UI issues to `../server-extension-gradio/SKILL.md`. |
| `agent.display_previous_nodes(steps)` / `agent.display_all_nodes()` | Inspect retrieved HTML nodes after a run. | Requires logs with `engine_log`; intended for notebook/display contexts. |
| `agent.get_summary()` | Return profiling waterfall plot and summary table. | Clears profiling data after returning. |
| `agent.set_origin(origin)` | Set telemetry origin label. | Does not disable telemetry. |

## Action results

`agent.run(...)` returns an `ActionResult` with fields such as:

- `instruction`: current/last instruction.
- `code`: generated browser/action code accumulated during the run.
- `success`: boolean success flag for the latest/overall outcome.
- `output`: extracted final output or `[NONE]`-style completion output.
- `total_estimated_tokens` and `total_estimated_cost`: populated when a `TokenCounter` is supplied and model usage metadata is available.

Check both `success` and `output`; a run may finish with no output when the objective is to perform an action rather than return data.

## Engines and routing terms

The world model emits one of these engine routes:

- `Navigation Engine`: heavy HTML retrieval plus action-code generation for interacting with page elements.
- `Navigation Controls`: simple commands such as `WAIT`, `BACK`, `SCAN`, `MAXIMIZE_WINDOW`, `SCROLL_DOWN`, `SCROLL_UP`, and `SWITCH_TAB <n>`.
- `Python Engine`: local computation/extraction over current state; does not navigate.
- `COMPLETE` or `SUCCESS`: objective reached; the instruction becomes the output.

If a workflow repeatedly chooses the wrong engine, add clearer objective/user data, inspect retrieved nodes, and consider a custom context, retriever, or prompt template.

## Logging and token APIs

```python
logger = AgentLogger()
file_logger = LocalLogger("agent_logs.json")
db_logger = LocalDBLogger("lavague_logs.db")
token_counter = TokenCounter(log=True)
agent = WebAgent(world_model, action_engine, token_counter=token_counter, logger=logger)
```

- `AgentLogger.return_pandas()` returns logs as a DataFrame-like table when pandas is available.
- `LocalLogger` serializes logs to a local file.
- `LocalDBLogger` writes logs to SQLite.
- `TokenCounter.process_token_usage(world_model, action_engine, result_to_update=result)` updates token/cost summaries when model callbacks expose usage metadata.

## Optional direct engines

Construct direct engines only when a task asks for lower-level debugging or customization:

```python
NavigationEngine(driver, llm=None, retriever=None, embedding=None, raise_on_error=False)
NavigationControl(driver, time_between_actions=1.5, navigation_engine=None)
PythonEngine(driver, llm=None, embedding=None, display=False, batch_size=5)
```

Most users should instantiate `ActionEngine(driver)` or `ActionEngine.from_context(context, driver)` instead.

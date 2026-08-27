# Agent API Reference

This reference covers Python agent-loop APIs owned by `agent-programming`. Browser/session options, custom tools, model credentials, CLI usage, and production integrations are routed to sibling sub-skills.

## Import Paths

Legacy Python agent:

```python
from browser_use import Agent, ChatBrowserUse
```

Beta Rust-backed agent:

```python
from browser_use.beta import Agent, BrowserProfile, BrowserSession, ChatBrowserUse
```

The beta package lazily exposes browser and LLM classes, including `Browser`, `BrowserProfile`, `BrowserSession`, `ChatBrowserUse`, `ChatOpenAI`, `ChatGoogle`, and `ChatAnthropic`.

## Legacy `Agent(...)` Constructor Surface

Important parameters verified from the current package:

| Parameter | Use | Notes |
| --- | --- | --- |
| `task: str` | Required browser automation objective | Include exact URL, desired result, and fallback behavior. |
| `llm` | Primary chat model | Defaults to configured model or `ChatBrowserUse()`. Browser Use provider models enable flash mode. |
| `browser_profile`, `browser_session`, `browser` | Browser wiring | Route detailed setup to `../../browser-control/SKILL.md`. `browser` and `browser_session` cannot both be set. |
| `tools`, `controller` | Tool registry | Route implementation details to `../../tools-and-actions/SKILL.md`; `controller` is backward-compatible alias. |
| `skill_ids`, `skills`, `skill_service` | Browser Use skills integration | Route production/skills service details to `../../production-integrations/SKILL.md`; `skills` and `skill_ids` cannot both be set. |
| `sensitive_data` | Secret placeholders | Route guardrails to `../../tools-and-actions/SKILL.md`. |
| `initial_actions` | Pre-model deterministic setup | List of `{action_name: params}` dictionaries converted through the current action model. |
| `output_model_schema`, `extraction_schema` | Structured result schema | Route schema design to `../../llm-and-output/SKILL.md`. |
| `use_vision`, `vision_detail_level` | Screenshot/vision behavior | `use_vision != "auto"` excludes the screenshot action from tools. |
| `save_conversation_path`, `save_conversation_path_encoding` | Save LLM conversation | Useful for debugging prompt/model-output problems. |
| `max_failures` | Stop after consecutive failures | Default currently `5` in the verified signature. |
| `final_response_after_failure` | Recovery call after failures | If true, allows one final response attempt after max failures. |
| `override_system_message`, `extend_system_message` | Prompt customization | Prefer `extend_system_message`; override only for expert control. |
| `generate_gif` | Visual artifact from history | Pass `True` or a path-like string. |
| `available_file_paths` | Files the agent may access | Route file-tool security to `../../tools-and-actions/SKILL.md`. |
| `include_attributes` | HTML attributes kept in DOM prompt | Use sparingly to reduce prompt size. |
| `max_actions_per_step` | Multi-action output limit | Default currently `5`. Lower when debugging; raise for form-filling speed. |
| `use_thinking` | Include thinking field | Full mode only; flash mode removes thinking. |
| `flash_mode` | Fast schema | Strips thinking/evaluation/next-goal style fields and disables planning. |
| `max_history_items` | Limit remembered history | Helps long tasks; pairs with message compaction. |
| `page_extraction_llm` | Separate extraction model | Route model selection to `../../llm-and-output/SKILL.md`. |
| `fallback_llm` | Backup model | Route to `../../llm-and-output/SKILL.md`. |
| `use_judge`, `ground_truth`, `judge_llm` | Trace judgement | Useful for validation; `judge_llm` defaults to primary LLM. |
| `calculate_cost`, `pricing_url` | Usage/cost tracking | Route details to `../../llm-and-output/SKILL.md`. |
| `llm_timeout` | Per-LLM-call timeout | If omitted, selected from model name/provider heuristics. |
| `step_timeout` | Per-step timeout | Default currently `180` seconds; also bounds initial actions in legacy run setup. |
| `directly_open_url` | Auto pre-navigation | If true and task contains a URL, Browser Use may create a `navigate` initial action. |
| `include_recent_events` | Browser event context | Useful for event-heavy pages; may increase context. |
| `enable_planning` | Plan field handling | Disabled automatically by flash mode. |
| `planning_replan_on_stall` | Failure threshold for replan nudge | Default currently `3`; soft message only. |
| `planning_exploration_limit` | Exploration nudge limit | Default currently `5`; soft message only. |
| `loop_detection_window`, `loop_detection_enabled` | Repetition/stagnation nudges | Soft context messages, not hard stops. |
| `message_compaction` | Summarize older memory | `True` becomes `MessageCompactionSettings(enabled=True)`. |
| `enable_signal_handler` | Ctrl-C pause/resume handling | Disable in host apps that manage signals. |

## `run(...)`

Legacy:

```python
history = await agent.run(
    max_steps=50,
    on_step_start=on_step_start,
    on_step_end=on_step_end,
)
```

- Default `max_steps` is currently `500` for the legacy agent.
- `on_step_start` and `on_step_end` receive the `Agent` instance and may be async.
- The run loop starts the browser session, registers skills as actions, executes initial actions, then loops until done, stopped, or failure/step limits are reached.
- Ctrl-C support can pause/resume or force-exit when signal handling is enabled.

Beta:

```python
history = await agent.run(max_steps=100)
```

- Default `max_steps` is currently `100` for the beta agent.
- Python setup runs first, then the Rust SDK server performs the main terminal run.
- Initial actions execute before SDK delegation with `allow_terminal_run=False`.
- Exceptions are finalized with telemetry/update cleanup, then re-raised except keyboard interrupt returns current history.

## `step(...)` and One-Step Debugging

Legacy exposes `await agent.step(step_info=None)` for a single Python-loop step. Use it only for advanced debugging because a normal `run()` manages browser startup, initial actions, failure counting, and callbacks.

Beta exposes `take_step(AgentStepInfo(...))` behavior that runs initial actions on the first step, then calls `run(max_steps=1)`. This is useful for interactive wrappers but still depends on beta terminal runtime availability.

## Callbacks and Hooks

Constructor callbacks:

```python
async def new_step(state, model_output, step_number):
    print(step_number, state.url, [a.model_dump() for a in model_output.action])

async def done(history):
    print(history.final_result())

agent = Agent(
    task="...",
    llm=llm,
    register_new_step_callback=new_step,
    register_done_callback=done,
)
```

Run hooks:

```python
async def on_step_start(agent):
    print("starting", agent.state.n_steps)

async def on_step_end(agent):
    print("ending", agent.state.n_steps)

await agent.run(max_steps=20, on_step_start=on_step_start, on_step_end=on_step_end)
```

External stop callbacks:

```python
async def should_stop() -> bool:
    return cancel_flag.is_set()

agent = Agent(task="...", llm=llm, register_should_stop_callback=should_stop)
```

Keep callbacks lightweight. If a callback raises, the run can be interrupted or fail; log enough context to reproduce without printing secrets.

## Initial Action Schema

`initial_actions` is a list of one-action dictionaries:

```python
[
    {"navigate": {"url": "https://example.com", "new_tab": False}},
    {"click": {"index": 3}},
]
```

Behavior:

- Actions are validated through the current tool registry when possible.
- Unknown or invalid action dictionaries may remain raw until execution and then fail.
- Beta preserves `initial_action_payloads` for task-context explanation, including original order.
- Beta normalizes some older names such as `click_element_by_index` to `click`.
- Initial actions are not rerun on beta follow-up tasks.

## Planning Fields

`AgentOutput` full mode can include:

- `thinking`
- `evaluation_previous_goal`
- `memory`
- `next_goal`
- `current_plan_item`
- `plan_update`
- `action`

Planning behavior:

- `enable_planning=False` makes plan rendering return `None` and plan updates no-op.
- `flash_mode=True` uses a flash output schema where `thinking`, `current_plan_item`, and `plan_update` are absent.
- Flash mode forces `enable_planning=False`.
- Replan nudges trigger when consecutive failures reach `planning_replan_on_stall` and a plan exists.
- Exploration nudges can trigger when no plan appears after the configured exploration limit.

## History API

`AgentHistoryList` fields and helpers:

| Helper | Meaning |
| --- | --- |
| `final_result()` | Extracted content from the last result, or `None`. |
| `is_done()` | True if last result has `is_done=True`. |
| `is_successful()` | `success` from final done result, or `None` if not done. |
| `has_errors()` / `errors()` | Error summary per step. |
| `judgement()`, `is_judged()`, `is_validated()` | Judge result helpers when judgement is enabled. |
| `urls()` | URL per history item. |
| `screenshot_paths()`, `screenshots()` | Screenshot artifact paths or base64 screenshots. |
| `action_names()` | Flattened executed action names. |
| `model_actions()` | Flattened action dictionaries with interacted element metadata. |
| `action_history()` | Step-grouped action/result memory summary. |
| `model_outputs()` | Raw model output objects. |
| `model_thoughts()` | Backward-compatible brain/current-state summaries. |
| `action_results()` | Flattened `ActionResult` objects. |
| `extracted_content()` | All extracted content strings. |
| `number_of_steps()` | Count of history items. |
| `total_duration_seconds()` | Sum of step metadata durations. |
| `save_to_file(path, sensitive_data=...)` | JSON save with optional sensitive-data filtering. |
| `structured_output` | Parse final result using retained output schema. |
| `get_structured_output(MyModel)` | Parse final result with an explicit Pydantic model. |

Pattern:

```python
history = await agent.run(max_steps=30)
if history.has_errors():
    print(history.errors())
if history.is_done():
    print("success:", history.is_successful())
print("result:", history.final_result())
```

## Beta Agent API Notes

Beta `Agent(...)` mirrors most legacy constructor parameters, but wraps terminal/core behavior:

- `use_vision` is forced true in current beta initialization.
- `run(max_steps=100)` delegates to a Rust SDK server after Python setup.
- `follow_up(task, max_steps=None, step_timeout=None, enqueue_timeout=None)` requires `run()` first.
- `find_browser_use_terminal_binary()` checks `BROWSER_USE_TERMINAL_BINARY`, packaged `browser_use_core`, default Browser Use Terminal install locations, and PATH.
- Missing terminal support raises `BetaAgentError` mentioning Browser Use Terminal/core install or `BROWSER_USE_TERMINAL_BINARY`.
- Beta reconstructs `AgentHistoryList` from terminal events and supports structured output, including fenced JSON extraction.

## Minimal Smoke Checks

Import smoke:

```bash
python - <<'PY'
from browser_use import Agent, ChatBrowserUse
from browser_use.agent.views import AgentHistoryList
from browser_use.beta import Agent as BetaAgent, find_browser_use_terminal_binary
print("legacy", Agent)
print("history", AgentHistoryList)
print("beta", BetaAgent)
PY
```

Beta terminal availability:

```bash
python - <<'PY'
from browser_use.beta import find_browser_use_terminal_binary, BetaAgentError
try:
    print(find_browser_use_terminal_binary())
except BetaAgentError as exc:
    print(type(exc).__name__, exc)
PY
```

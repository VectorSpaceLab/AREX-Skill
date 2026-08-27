# Agent Workflow Recipes

These recipes are self-contained patterns distilled from Browser Use source, examples, and tests. They avoid depending on original repository examples at runtime.

## Minimal Legacy Agent

```python
import asyncio
from browser_use import Agent, ChatBrowserUse

async def main():
    agent = Agent(
        task="Open https://example.com and report the page title.",
        llm=ChatBrowserUse(),
    )
    history = await agent.run(max_steps=20)
    print(history.final_result() or "No final result")

asyncio.run(main())
```

Validation checklist:

- Import succeeds.
- A provider key or configured default model is available.
- `max_steps` is small while debugging.
- `history.is_done()` and `history.errors()` are inspected before assuming success.

## Minimal Beta Agent

```python
import asyncio
from browser_use.beta import Agent, ChatBrowserUse

async def main():
    agent = Agent(
        task="Open https://example.com and report the page title.",
        llm=ChatBrowserUse(),
    )
    history = await agent.run(max_steps=20)
    print(history.final_result() or "No final result")

asyncio.run(main())
```

Validation checklist:

- `browser-use[core]` or Browser Use Terminal is installed for the current platform.
- `find_browser_use_terminal_binary()` succeeds or `BROWSER_USE_TERMINAL_BINARY` points to a compatible terminal binary.
- Use beta only when the user explicitly imports `browser_use.beta` or requests the Rust-backed/core path.

## Task Prompt Template

Use this task shape for reliable automation:

```text
1. Go to https://target.example/path.
2. If the page fails to load, wait once, refresh once, then use search fallback.
3. Extract exactly: title, price, availability, and canonical URL.
4. If a required field is missing, say which field is missing and why.
5. Finish with done and a compact JSON object.
```

Good prompt traits:

- Names exact fields and final format.
- Gives bounded recovery steps.
- Avoids vague goals like “browse until you find something useful.”
- Tells the agent when to stop.

## Deterministic Setup With `initial_actions`

Use `initial_actions` for setup that should not consume a model step:

```python
initial_actions = [
    {"navigate": {"url": "https://example.com/start", "new_tab": False}},
]
agent = Agent(
    task="After the page opens, extract the visible heading and status message.",
    llm=llm,
    initial_actions=initial_actions,
    step_timeout=30,
)
history = await agent.run(max_steps=10)
```

Debug notes:

- If history is empty or the first error is a timeout, the initial action may have failed before model execution.
- Set `directly_open_url=False` if automatic URL extraction from the task is causing unwanted pre-navigation.
- For beta, initial actions run before SDK delegation and are included in task context in order.

## Fast Agent Mode

Use fast mode when speed matters more than plan introspection:

```python
agent = Agent(
    task="Find the first three product names and prices on the search page.",
    llm=llm,
    flash_mode=True,
    max_actions_per_step=5,
    extend_system_message="Be concise and use multi-action sequences when safe.",
)
```

Trade-offs:

- `flash_mode=True` disables planning and removes thinking/plan fields from output.
- Browser Use provider models currently force flash mode automatically.
- Debug with full mode when you need plan updates or richer reasoning traces.

## Planning-Aware Debug Mode

Use planning mode when a task stalls or loops:

```python
agent = Agent(
    task="Compare the current dashboard total with yesterday's total and report the delta.",
    llm=llm,
    enable_planning=True,
    planning_replan_on_stall=2,
    planning_exploration_limit=3,
    loop_detection_enabled=True,
    max_failures=3,
)
```

Checks:

- If `agent.settings.enable_planning` is false, planning fields will not render.
- If `agent.settings.flash_mode` is true, planning is disabled even if requested.
- Loop detection and replan messages are nudges; they do not prevent actions.

## Step Callbacks for Observability

```python
async def new_step(state, model_output, step_number):
    names = []
    for action in model_output.action:
        names.extend(action.model_dump(exclude_none=True).keys())
    print(step_number, state.url, names)

async def done(history):
    print("done", history.is_done(), history.is_successful())

agent = Agent(
    task="Open https://example.com and report what changed after clicking Learn more.",
    llm=llm,
    register_new_step_callback=new_step,
    register_done_callback=done,
)
await agent.run(max_steps=15)
```

Rules:

- Keep callbacks fast and side-effect safe.
- Never print secrets from `sensitive_data`, form fields, or cookies.
- If a callback must stop execution, use `register_should_stop_callback` rather than raising from ordinary logging code.

## Run Hooks Around Each Step

```python
async def on_step_start(agent):
    print("start", agent.state.n_steps)

async def on_step_end(agent):
    print("end", agent.state.n_steps)

history = await agent.run(
    max_steps=20,
    on_step_start=on_step_start,
    on_step_end=on_step_end,
)
```

Use run hooks for local instrumentation. Use constructor callbacks when integrating with a host service that needs state/model-output snapshots.

## External Stop Switch

```python
class StopFlag:
    value = False

stop_flag = StopFlag()

async def should_stop() -> bool:
    return stop_flag.value

agent = Agent(task="...", llm=llm, register_should_stop_callback=should_stop)
```

This is safer than cancelling the asyncio task when the user has a UI cancel button or job queue timeout.

## Save Conversation and History

```python
agent = Agent(
    task="...",
    llm=llm,
    save_conversation_path="logs/browser-use-conversation.json",
    max_history_items=20,
)
history = await agent.run(max_steps=25)
history.save_to_file("logs/browser-use-history.json")
```

Use saved conversation logs for model-output/schema problems. Use saved history for browser state, actions, errors, and final result.

## History Triage Snippet

```python
history = await agent.run(max_steps=30)
print("done:", history.is_done(), "success:", history.is_successful())
print("result:", history.final_result())
print("urls:", history.urls())
print("actions:", history.action_names())
print("errors:", [e for e in history.errors() if e])
```

Use this before changing browser settings or tools; many issues are obvious from the first non-empty error.

## Structured Output Handoff

Agent-programming owns where `output_model_schema` plugs in, but schema design belongs to `../../llm-and-output/SKILL.md`.

```python
from pydantic import BaseModel

class PageSummary(BaseModel):
    title: str
    facts: list[str]

agent = Agent(task="Extract a page summary as JSON", llm=llm, output_model_schema=PageSummary)
history = await agent.run(max_steps=20)
summary = history.structured_output or history.get_structured_output(PageSummary)
```

If parsing fails, check whether the final result is valid JSON and whether the history retained `_output_model_schema`.

## Beta Follow-Up Task

```python
agent = Agent(task="Open https://example.com and summarize the page", llm=llm)
history = await agent.run(max_steps=20)
if history.is_done():
    followup_history = await agent.follow_up("Now find the contact link on the same site", max_steps=10)
```

Rules:

- Call `follow_up` only after `run()` has created an active beta terminal session.
- If it raises `BetaAgentError: No active Rust session`, re-run the initial task or use a legacy agent workflow.

## Multi-Agent Parallel Pattern

Use separate agents and separate browser sessions unless shared state is intentional:

```python
async def run_task(task: str):
    agent = Agent(task=task, llm=llm)
    return await agent.run(max_steps=15)

histories = await asyncio.gather(
    run_task("Find the headline on https://example.com"),
    run_task("Find the status text on https://example.org"),
)
```

Do not share a single mutable browser session across concurrent agents unless the workflow intentionally coordinates tabs and the browser-control guidance has been followed.

## Failure-Recovery Workflow

When a user reports “the agent keeps clicking the same thing”:

1. Re-run with `max_steps=8`, `save_conversation_path`, and history triage printing.
2. Check repeated names in `history.action_names()` and URL/page stagnation in `history.urls()`.
3. Make the prompt more explicit: name the target text, alternative keyboard fallback, and stop condition.
4. Enable planning/full mode if flash mode hid plan context.
5. If element indices are unstable, route to browser-control or tools-and-actions for deterministic selectors or a custom action.

## Maintainer Validation Notes

When explicitly maintaining Browser Use itself, validate planning/flash behavior, beta initial actions, beta history reconstruction, and beta structured output behavior with the project’s native test suite. For ordinary user projects, do not depend on a source checkout; use portable import checks and small capped agent runs instead.

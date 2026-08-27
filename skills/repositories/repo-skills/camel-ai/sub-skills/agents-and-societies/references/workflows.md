# Agent And Society Workflows

Use these recipes to design CAMEL-AI agent workflows without relying on repository examples at runtime. Real `.step()` and `.process_task()` calls usually require a configured model backend and credentials; validate imports and object construction first with `../scripts/inspect_agent_basics.py`.

## Recipe: Credential-Free Planning Pass

Before running a user workflow in CI or a restricted environment:

1. Identify the workflow type: single `ChatAgent`, `RolePlaying`, or `Workforce`.
2. Build `BaseMessage` and `Task` objects locally.
3. Inspect constructors and planned arguments.
4. Check whether `.step()`, `RolePlaying(... with_task_specify=True)`, or `Workforce.process_task(...)` would call a model.
5. Route model setup to `../../models-and-configuration/`, tool schemas to `../../tools-runtimes-and-services/`, and memory internals to `../../memory-rag-and-data/`.

Minimal dry-run object construction:

```python
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.tasks import Task

system_message = BaseMessage.make_system_message(
    "You are a careful planner. Do not call tools unless asked.",
    role_name="Planner System",
)
agent = ChatAgent(
    system_message=system_message,
    max_iteration=1,
    message_window_size=6,
    token_limit=4096,
)
task = Task(content="Plan a release checklist", id="release-checklist")

print(agent.system_message.content)
print(task.to_string())
```

Do not call `agent.step(...)` in a credential-free check unless the model backend has been explicitly configured to a safe local or mocked backend.

## Recipe: Single `ChatAgent`

Use this when the user wants one assistant with an explicit role, memory window, optional tools, and bounded runtime.

```python
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.terminators import ResponseWordsTerminator
from camel.types import TerminationMode

system_message = BaseMessage.make_system_message(
    "You are a migration planner. End with DONE when the checklist is complete.",
    role_name="Migration Planner",
)
terminator = ResponseWordsTerminator(
    {"DONE": 1},
    case_sensitive=True,
    mode=TerminationMode.ANY,
)
agent = ChatAgent(
    system_message=system_message,
    model=model,  # prepared via the models sub-skill
    response_terminators=[terminator],
    max_iteration=4,
    message_window_size=10,
    summarize_threshold=70,
    token_limit=8192,
    step_timeout=60,
)
response = agent.step("Create a database migration checklist.")
if response.terminated:
    print(response.info.get("termination_reasons"))
print(response.msgs[0].content)
```

Design checklist:

- Keep the system message specific enough to prevent role drift.
- Pair every response terminator with an explicit instruction in the system prompt.
- Use `max_iteration=1` for simple single-turn calls; raise it only when tools or terminators need multiple model calls.
- Use `message_window_size`, `token_limit`, and `summarize_threshold` for long conversations.
- Use `retry_attempts`, `retry_delay`, and `step_timeout` for backend reliability.

## Recipe: Tool-Enabled Agent At Routing Level

This sub-skill only owns the agent wiring; use `../../tools-runtimes-and-services/` for `FunctionTool`, MCP, schema synthesis, sandbox, and external service details.

```python
from camel.agents import ChatAgent

agent = ChatAgent(
    system_message="Use the calculator only for arithmetic, then explain briefly.",
    model=model,
    tools=[calculator_function],
    tool_execution_timeout=10,
    mask_tool_output=True,
    max_iteration=3,
)
```

Routing decisions:

- Use `tools=[callable_or_FunctionTool]` when CAMEL should execute the tool inside the agent loop.
- Use `external_tools=[schema_or_tool]` when the caller should receive tool call requests and execute externally.
- Use `mask_tool_output=True` when raw tool output may be sensitive or verbose.
- Use `prune_tool_calls_from_memory` only after checking whether downstream reasoning needs tool traces.

## Recipe: Role-Playing Society

Use `RolePlaying` when two roles should alternate: the AI user gives instructions/challenges, the AI assistant solves them, and an optional critic reduces/evaluates responses.

```python
from camel.societies import RolePlaying

session = RolePlaying(
    assistant_role_name="Python Developer",
    user_role_name="Product Manager",
    task_prompt="Design a minimal issue triage bot.",
    with_task_specify=False,
    with_task_planner=False,
    assistant_agent_kwargs={"model": model, "max_iteration": 2},
    user_agent_kwargs={"model": model, "max_iteration": 2},
)
message = session.init_chat()
for _ in range(8):
    assistant_response, user_response = session.step(message)
    if assistant_response.terminated or user_response.terminated:
        break
    if "CAMEL_TASK_DONE" in user_response.msg.content:
        break
    message = assistant_response.msg
```

Use `with_task_specify=False` and `with_task_planner=False` for dry-run object construction or when no model credentials are available during initialization. Enable them when the user wants CAMEL to refine or plan the prompt automatically.

Use pre-built agents when you need custom memory, terminators, tools, or model managers:

```python
assistant_agent = ChatAgent(
    system_message="You are the implementation lead.",
    model=model,
    max_iteration=2,
)
user_agent = ChatAgent(
    system_message="You are the reviewer who asks for the next concrete step.",
    model=model,
    max_iteration=2,
)
session = RolePlaying(
    assistant_role_name="Implementation Lead",
    user_role_name="Reviewer",
    task_prompt="Refine a deployment plan.",
    with_task_specify=False,
    assistant_agent=assistant_agent,
    user_agent=user_agent,
)
```

Pre-built `assistant_agent` and `user_agent` must have non-`None` system messages.

## Recipe: Workforce Team

Use `Workforce` for a team of agents, automatic decomposition, assignment, retries, and worker creation.

```python
from camel.agents import ChatAgent
from camel.societies.workforce import Workforce
from camel.tasks import Task

coordinator = ChatAgent(
    system_message="Coordinate workers and assign tasks precisely.",
    model=model,
    max_iteration=2,
)
planner = ChatAgent(
    system_message="Decompose tasks into independently verifiable subtasks.",
    model=model,
    max_iteration=2,
)
researcher = ChatAgent(
    system_message="Research facts and cite assumptions.",
    model=model,
    max_iteration=2,
)
writer = ChatAgent(
    system_message="Write concise final reports.",
    model=model,
    max_iteration=2,
)

workforce = Workforce(
    description="Research report team",
    coordinator_agent=coordinator,
    task_agent=planner,
    task_timeout_seconds=180,
    share_memory=False,
    failure_handling_config={
        "max_retries": 2,
        "enabled_strategies": ["retry", "replan"],
        "halt_on_max_retries": False,
    },
)
workforce.add_single_agent_worker("Finds source facts", researcher)
workforce.add_single_agent_worker("Writes final report", writer)

result = workforce.process_task(Task(content="Prepare a market summary", id="market-summary"))
print(result.result)
```

Design checklist:

- Provide custom `coordinator_agent` and `task_agent` when default backend credentials are not acceptable.
- Bound execution with `task_timeout_seconds` and a small `failure_handling_config.max_retries` during early testing.
- Keep worker descriptions distinct; the coordinator uses descriptions to assign work.
- Enable `share_memory=True` only when cross-worker context continuity is more important than trace isolation.
- Add a `stream_callback` or `WorkforceCallback` for observability, not for slow blocking side effects.

## Recipe: Workforce Pipeline Mode

Use pipeline mode when the user already knows the dependency graph and does not want auto-decomposition to invent steps.

```python
from camel.societies.workforce import Workforce, WorkforceMode
from camel.tasks import Task

workforce = Workforce("Release note pipeline", mode=WorkforceMode.PIPELINE)
workforce.pipeline_add("Collect merged PRs", task_id="collect") \
    .pipeline_fork([
        "Summarize user-facing changes",
        "Summarize breaking changes",
    ]) \
    .pipeline_join("Write release notes", task_id="release-notes") \
    .pipeline_build()

result = workforce.process_task(Task(content="Create release notes", id="root"))
```

Pipeline mode is the right answer when debugging nondeterminism from auto-decomposition. It also lets failed upstream context flow into downstream join tasks, which can be useful for robust reporting.

## Recipe: Tasks And Dependencies

Use `Task` to represent structured work, hierarchy, and dependencies.

```python
from camel.tasks import Task, TaskManager

root = Task(content="Prepare launch", id="launch")
docs = Task(content="Draft docs", id="docs")
tests = Task(content="Run smoke tests", id="tests")
root.add_subtask(docs)
root.add_subtask(tests)
print(root.to_string(state=True))

TaskManager.set_tasks_dependence(root, [docs, tests], type="parallel")
```

For model-assisted decomposition, `task.decompose(agent=planner_agent)` calls a model and parses `<task>...</task>` blocks. Use a dry-run prompt review first when credentials are unavailable.

## Reference-Only Native Example Decisions

The original CAMEL examples that inspired these recipes include single-agent, role-playing, and workforce demos. They are not linked as runtime dependencies because they may require model credentials, external APIs, or source checkout paths. This sub-skill instead bundles distilled recipes and the safe inspection script.

## Difficult Usability Cases

Case 1: Role-playing society, custom backend, memory, and termination guard without API keys in CI.

- Route backend creation to `../../models-and-configuration/`.
- Build `BaseMessage` system prompts and `ChatAgent` instances with memory/window/terminator settings.
- Set `with_task_specify=False` and avoid `.step()` in CI.
- Run `../scripts/inspect_agent_basics.py --json` to prove imports, signatures, and dry-run objects.
- Document the exact command that should run only when credentials are available.

Case 2: Workforce never finishes.

- Inspect whether the workflow is `AUTO_DECOMPOSE` or `PIPELINE`.
- Bound `task_timeout_seconds`, `failure_handling_config.max_retries`, and worker `max_iteration`.
- Add a `stream_callback` or `WorkforceCallback` to identify the stuck worker/task.
- Check whether `share_memory` is causing confusing stale context; reset agents and tasks.
- Consider rewriting the workflow into `WorkforceMode.PIPELINE` with explicit dependencies.

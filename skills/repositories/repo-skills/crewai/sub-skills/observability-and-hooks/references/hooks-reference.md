# Hooks and Event Listeners

CrewAI exposes several hook layers. Choose the smallest hook surface that matches the problem: kickoff hooks for crew input/output boundaries, LLM/tool hooks for execution interception, event listeners for passive monitoring/integration, and core callbacks for task/step behavior.

## Hook Surface Map

| Surface | Use for | Return behavior | Scope |
| --- | --- | --- | --- |
| `@before_kickoff` / `before_kickoff_callbacks` | Preprocess kickoff inputs | Return the modified inputs mapping | Specific Crew instance |
| `@after_kickoff` / `after_kickoff_callbacks` | Postprocess `CrewOutput` | Return the modified result | Specific Crew instance |
| `@before_llm_call` | Inspect/mutate LLM messages or block an LLM call | Return `False` to block; `True`/`None` to continue | Global registry; can be crew-scoped by defining as `@CrewBase` method |
| `@after_llm_call` | Sanitize/transform LLM response or update message history | Return replacement string or `None` to keep original | Global registry; can be crew-scoped by defining as `@CrewBase` method |
| `@before_tool_call` | Inspect/mutate tool input or block a tool call | Return `False` to block; `True`/`None` to continue | Global registry; supports tool and agent filters |
| `@after_tool_call` | Sanitize/transform tool result | Return replacement string or `None` to keep original | Global registry; supports tool and agent filters |
| `BaseEventListener` | Passive monitoring, custom audit logs, integrations | Handlers receive `(source, event)` | Event-bus singleton |

Use [core-runtime](../../core-runtime/SKILL.md) for task callbacks, step callbacks, guardrails, and `CrewOutput`/`TaskOutput` semantics outside observability.

## Before and After Kickoff Hooks

Kickoff hooks run around `crew.kickoff(...)` and are best for boundary transformations that do not need access to every LLM or tool call.

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, before_kickoff, after_kickoff, crew, task

@CrewBase
class ReportCrew:
    @before_kickoff
    def normalize_inputs(self, inputs):
        inputs = dict(inputs or {})
        inputs["topic"] = inputs.get("topic", "CrewAI")
        return inputs

    @after_kickoff
    def add_audit_marker(self, result):
        result.raw = f"{result.raw}\n\n[observed]"
        return result

    @agent
    def reporter(self):
        return Agent(role="Reporter", goal="Write a brief report", backstory="Concise writer")

    @task
    def report_task(self):
        return Task(description="Report on {topic}", expected_output="Short report", agent=self.reporter())

    @crew
    def crew(self):
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential)
```

Important details:

- `@CrewBase` wires decorated kickoff hooks onto the `Crew` returned by the `@crew` method.
- `before_kickoff` receives a normalized copy of the inputs. If kickoff receives `None`, hooks receive `{}`.
- Multiple before hooks run in declaration/registration order; each receives the previous hook's returned inputs.
- Multiple after hooks run in order after task execution and before the result is returned.
- Direct `Crew(before_kickoff_callbacks=[...], after_kickoff_callbacks=[...])` is also supported; those callbacks are distinct from decorators but use the same input/output pattern.

## LLM Call Hooks

Import global LLM hook helpers from `crewai.hooks`:

```python
from crewai.hooks import before_llm_call, after_llm_call

@before_llm_call(agents=["Researcher"])
def add_safety_context(context):
    context.messages.append({"role": "system", "content": "Do not reveal secrets."})
    return None

@after_llm_call
def redact_response(context):
    if context.response and "SECRET" in context.response:
        return context.response.replace("SECRET", "[REDACTED]")
    return None
```

`LLMCallHookContext` includes:

- `executor`: Crew agent executor, LiteAgent, or `None` for direct LLM calls.
- `messages`: mutable list sent to the LLM. Modify in place with `append`, `extend`, or item edits; do not replace the list object.
- `agent`, `task`, `crew`: current runtime objects when available.
- `llm`: LLM instance or model reference.
- `iterations`: current agent iteration, `0` for direct calls.
- `response`: set for after-hooks.

Behavior notes:

- Before hooks run in registration order.
- A before hook returning `False` blocks the LLM call and raises a hook-blocking error in the LLM path.
- After hooks can chain response transformations: each replacement becomes the next hook's `context.response`.
- Hook errors are caught and logged in several executor paths; still treat hooks as production code and keep them small.
- `context.request_human_input(...)` can pause live console output for approval, but it blocks execution and should not be used in unattended jobs.

## Tool Call Hooks

Tool hooks intercept tool execution and can filter by sanitized tool name and/or agent role.

```python
from crewai.hooks import before_tool_call, after_tool_call

@before_tool_call(tools=["Delete File", "execute_code"], agents=["Developer"])
def require_safe_paths(context):
    path = str(context.tool_input.get("path", ""))
    if path.startswith("/") or ".." in path:
        return False
    return None

@after_tool_call(tools=["web_search"])
def redact_tool_result(context):
    if context.tool_result:
        return context.tool_result.replace("api_key", "[redacted-key]")
    return None
```

`ToolCallHookContext` includes:

- `tool_name`: sanitized name used by the executor.
- `tool_input`: mutable dict passed to the tool. Modify in place; do not replace the dict object.
- `tool`: `CrewStructuredTool` instance.
- `agent`, `task`, `crew`: current runtime objects when available.
- `tool_result`: agent-facing string result for after-hooks.
- `raw_tool_result`: original Python result for after-hooks.

Filter details:

- `@before_tool_call(tools=[...])` and `@after_tool_call(tools=[...])` sanitize human-readable tool names, so `"Delete File"` can match executor name `delete_file`.
- `agents=[...]` matches agent role strings exactly.
- Combined tool+agent filters run only when both match.

## Hook Registration and Cleanup

The global hook registry provides explicit registration, introspection, unregister, and clear helpers:

```python
from crewai.hooks import (
    register_before_llm_call_hook,
    unregister_before_llm_call_hook,
    clear_all_global_hooks,
    get_before_tool_call_hooks,
)
```

Useful cleanup APIs:

- `unregister_before_llm_call_hook(hook)` / `unregister_after_llm_call_hook(hook)`.
- `unregister_before_tool_call_hook(hook)` / `unregister_after_tool_call_hook(hook)`.
- `clear_all_llm_call_hooks()` and `clear_all_tool_call_hooks()`.
- `clear_all_global_hooks()` returns counts for LLM, tool, and total hooks cleared.

In notebooks, tests, daemons, or repeated imports, clean up global hooks after a run. Without cleanup, decorators can register additional global hooks each time a module is imported or a new `@CrewBase` instance is created.

## Crew-Scoped Execution Hooks

Execution hook decorators are global when used on module-level functions. When used as methods inside an `@CrewBase` class, CrewAI detects the hook methods, binds `self`, and registers filtered wrappers when an instance is created.

```python
from crewai.project import CrewBase, crew
from crewai.hooks import before_llm_call, before_tool_call

@CrewBase
class AuditedCrew:
    audit_count = 0

    @before_llm_call(agents=["Researcher"])
    def count_researcher_calls(self, context):
        self.audit_count += 1
        return None

    @before_tool_call(tools=["web_search"])
    def normalize_search(self, context):
        if "query" in context.tool_input:
            context.tool_input["query"] = context.tool_input["query"].strip()
        return None
```

Caveats:

- Each `@CrewBase` instance registers its bound hook functions. Creating multiple instances can intentionally create multiple registered hooks.
- Crew-scoped execution hooks still use the global hook registry under the hood. Clear/unregister in tests if needed.
- Agent filters compare `context.agent.role`, not method names or config keys.

## Event Listeners

Use event listeners for passive observability and integrations that need event-bus data rather than mutation/blocking.

```python
from crewai.events import BaseEventListener, CrewKickoffStartedEvent, CrewKickoffCompletedEvent

class AuditListener(BaseEventListener):
    def setup_listeners(self, crewai_event_bus):
        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_started(source, event):
            print(f"Crew started: {event.crew_name}")

        @crewai_event_bus.on(CrewKickoffCompletedEvent)
        def on_completed(source, event):
            print(f"Crew completed: {event.crew_name}")

listener = AuditListener()
```

Event listener rules:

- Instantiate the listener before the Crew or Flow runs, and keep the instance reachable so its handlers stay registered.
- Handlers receive `(source, event)`; some advanced handlers may receive runtime state when registered for that signature.
- Event bus supports synchronous and asynchronous handlers. Async handlers run in a background event loop, so account for eventual completion in tests.
- Registering the same listener class repeatedly can duplicate side effects if the event bus still holds previous handlers.

Common event classes include crew kickoff events, task events, agent execution events, tool usage events, LLM call events, memory/knowledge events, flow events, reasoning events, MCP events, guardrail events, and system signal events.

## Hook Selection Guidance

- Use kickoff hooks to enrich inputs, normalize metadata, or postprocess final outputs.
- Use LLM hooks for prompt/message inspection, response sanitization, iteration limits, cost counters, and LLM approval gates.
- Use tool hooks for tool input validation, destructive-action blocking, result redaction, cache/rate-limit counters, and tool analytics.
- Use event listeners for audit trails, metrics, dashboards, and side-channel observability that should not change execution behavior.
- Use output logs or latest task-output storage when the user needs a local after-the-fact execution record rather than live interception.

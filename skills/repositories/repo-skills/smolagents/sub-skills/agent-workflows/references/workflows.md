# Agent Workflow Recipes

These recipes are self-contained patterns for creating and running smolagents agent workflows. They assume a working model object is already available; model/provider setup belongs to `model-providers`, and tool authoring belongs to `tools-and-integrations`.

## Choose `CodeAgent` vs `ToolCallingAgent`

Choose `CodeAgent` when:

- The model can reliably emit code blocks.
- The task benefits from Python control flow, intermediate variables, calculations, or data transformations.
- You want the generated action represented as `ActionStep.code_action` and available through `agent.memory.return_full_code()`.

Choose `ToolCallingAgent` when:

- The model/provider has strong native function/tool calling.
- You want direct tool-call messages instead of generated Python.
- You want multiple non-final tool calls in one action to execute concurrently.

Minimal construction looks like:

```python
from smolagents import CodeAgent, ToolCallingAgent

code_agent = CodeAgent(tools=[], model=model, max_steps=6)
tool_agent = ToolCallingAgent(tools=[], model=model, max_steps=6)
```

## Run and Inspect a Single Agent

```python
agent = CodeAgent(tools=[], model=model, max_steps=4, return_full_result=True)
run_result = agent.run("Return the square root of 144.")

print(run_result.output)
print(run_result.state)
print(run_result.token_usage)
print(run_result.timing.duration)
print(agent.memory.get_succinct_steps())
```

If the caller only needs the final answer, omit `return_full_result=True` and `run()` returns the output directly.

## Stream a Run

```python
for event in agent.run("Solve this in steps", stream=True):
    print(type(event).__name__)
```

Streaming only executes while the generator is consumed. With `stream_outputs=True`, the model must implement `generate_stream(...)`; otherwise agent initialization raises a `ValueError`. A streaming run may yield stream deltas, tool calls, tool outputs, memory steps, and the final-answer step.

A robust streamer should branch by attributes rather than exact concrete classes:

```python
for event in agent.run("Debug the workflow", stream=True):
    if hasattr(event, "step_number"):
        print("step", event.step_number, getattr(event, "error", None))
    elif hasattr(event, "content"):
        print(event.content or "", end="")
    elif hasattr(event, "output"):
        print("output", event.output)
```

## Add Managed Agents

Managed agents are specialized agents exposed to a manager as callable tools. Each managed agent needs a unique valid `name` and a `description`; duplicate names across tools, managed agents, or the manager's own name are rejected.

```python
search_agent = ToolCallingAgent(
    tools=[search_tool],
    model=model,
    name="search_agent",
    description="Searches and summarizes web pages for the manager.",
)

manager = CodeAgent(
    tools=[],
    model=model,
    managed_agents=[search_agent],
    max_steps=8,
)

answer = manager.run("Ask the search agent for evidence, then synthesize an answer.")
```

When called by a manager, a managed agent receives a templated task from `prompt_templates["managed_agent"]["task"]`. Its return is wrapped by `prompt_templates["managed_agent"]["report"]`. If `provide_run_summary=True`, the report includes a compact summary of the managed agent's memory.

Managed agents are useful for separation of memory and specialization. For example, a web-search agent can accumulate page content while the manager keeps only a report.

## Use Final-Answer Checks

Final-answer checks validate candidate final answers before the run accepts them.

```python
def must_be_integer(final_answer, memory, agent):
    try:
        int(final_answer)
    except (TypeError, ValueError):
        return False
    return True

agent = CodeAgent(
    tools=[],
    model=model,
    final_answer_checks=[must_be_integer],
    max_steps=5,
)
```

Check functions are called as `check(final_answer, memory, agent=agent)`. If a check fails or raises, the error is stored on the action step and the model gets a retry opportunity. If no valid final answer appears before `max_steps`, the agent asks the model to provide a final answer from the logs.

Do not rely on `to_dict()`/`save()` to preserve final-answer checks; recreate them after loading.

## Preserve or Reset Conversation State

Every `run()` appends a `TaskStep`. By default it clears previous steps first.

```python
first = agent.run("Remember that the project codename is Aurora.")
second = agent.run("Use the previous codename in a sentence.", reset=False)
```

Use `reset=False` when you intentionally want continuation. Use the default `reset=True` when each task should be isolated. `additional_args` also updates `agent.state`, which can be referenced by generated code or tool-call arguments.

## Save and Reload an Agent

```python
agent.save("agent_bundle")
loaded = CodeAgent.from_folder("agent_bundle", max_steps=10)
```

The saved bundle includes prompts, tools, requirements, managed agents, and app scaffolding. Recreate non-serialized runtime callbacks and final-answer checks explicitly:

```python
loaded = CodeAgent.from_folder("agent_bundle")
loaded.final_answer_checks = [must_be_integer]
loaded.step_callbacks.register(PlanningStep, my_planning_callback)
```

When loading from a Hub Space, set `trust_remote_code=True` only after reviewing the source:

```python
agent = CodeAgent.from_hub("org/agent-space", trust_remote_code=True)
```

## Inspect a Managed-Agent Run

```python
manager = CodeAgent(
    tools=[],
    model=model,
    managed_agents=[worker],
    return_full_result=True,
)
result = manager.run("Delegate part of this task, then finish.")

print(result.output)
print(result.token_usage)
print(result.timing)
print(manager.memory.get_succinct_steps())
print(worker.memory.get_succinct_steps())
```

The manager and each managed agent keep separate memory. Inspect both when debugging delegation.

For a no-network demonstration, use `scripts/inspect_agent_run.py` from this sub-skill.

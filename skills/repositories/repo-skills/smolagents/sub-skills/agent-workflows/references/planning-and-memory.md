# Planning, Prompt Templates, and Memory

Use this reference when a workflow needs explicit planning, prompt customization, callbacks, memory inspection, replay, or resume behavior.

## Enable Periodic Planning

`planning_interval` activates planning. A plan is generated at step 1 and then every interval.

```python
agent = CodeAgent(
    tools=[],
    model=model,
    planning_interval=3,
    max_steps=10,
)
```

Planning creates `PlanningStep` entries in `agent.memory.steps`. Initial planning uses `prompt_templates["planning"]["initial_plan"]`; later planning uses `update_plan_pre_messages` and `update_plan_post_messages` together with a summary-mode view of memory.

## Intercept or Edit Plans with Callbacks

Callbacks can be a list for action steps or a mapping keyed by memory step classes.

```python
from smolagents import CodeAgent, PlanningStep


def review_plan(memory_step, agent):
    if "unsafe shortcut" in memory_step.plan.lower():
        memory_step.plan += "\nAvoid unsafe shortcuts; use verified evidence only."

agent = CodeAgent(
    tools=[],
    model=model,
    planning_interval=2,
    step_callbacks={PlanningStep: review_plan},
)
```

A callback can inspect or mutate the memory step. It can call `agent.interrupt()` to stop execution; resume later with `agent.run(task, reset=False)` when preserving memory is desired.

Callback signature rules:

- A one-parameter callback receives only `memory_step`.
- A multi-parameter callback receives `memory_step` and keyword arguments such as `agent=agent`.
- The monitor callback is always registered for `ActionStep` to update metrics.

`to_dict()` does not serialize callbacks; re-register them after loading.

## Inspect Memory

```python
print(agent.memory.system_prompt.system_prompt)
for step in agent.memory.steps:
    print(type(step).__name__, getattr(step, "step_number", None), getattr(step, "error", None))

succinct = agent.memory.get_succinct_steps()
full = agent.memory.get_full_steps()
```

Use `get_succinct_steps()` for compact debugging; it excludes `model_input_messages`. Use `get_full_steps()` when you need exact model inputs and serializable raw fields. For `CodeAgent`, use `agent.memory.return_full_code()` to collect all code actions into one script.

Common step classes:

- `TaskStep`: the user task and optional images.
- `PlanningStep`: plan text, planning input messages, timing, and token usage.
- `ActionStep`: model output, parsed code or tool calls, observations, action output, errors, timing, token usage, and final-answer flag.
- `FinalAnswerStep`: the final output yielded at the end of streaming.

## Replay a Run

```python
agent.replay(detailed=False)
agent.replay(detailed=True)  # verbose; includes model input messages
```

`detailed=True` can be large because it prints memory at each step. Prefer succinct steps in automated logs and detailed replay only while debugging locally.

## Preserve Memory Across Runs

By default, `run(reset=True)` clears prior steps. Use `reset=False` to continue from existing memory.

```python
agent.run("First task")
agent.run("Continue from the previous task", reset=False)
```

If a workflow manually injects memory before running, use `reset=False`; otherwise injected steps are cleared.

```python
from smolagents import TaskStep

agent.memory.steps.append(TaskStep(task="Previous user request"))
agent.run("Continue the previous work", reset=False)
```

## Customize Prompt Templates Safely

Agents store prompts in `agent.prompt_templates`. `agent.system_prompt` is a read-only property regenerated from templates. To customize, mutate or pass `prompt_templates`, not `agent.system_prompt`.

```python
agent.prompt_templates["system_prompt"] += "\nAlways cite exact assumptions before acting."
```

If you pass a full `prompt_templates` dictionary, it must contain all required top-level and nested keys. Missing keys raise an assertion during initialization.

Required structure includes:

```python
{
    "system_prompt": "...",
    "planning": {
        "initial_plan": "...",
        "update_plan_pre_messages": "...",
        "update_plan_post_messages": "...",
    },
    "managed_agent": {
        "task": "...",
        "report": "...",
    },
    "final_answer": {
        "pre_messages": "...",
        "post_messages": "...",
    },
}
```

Prompt templates may use placeholders populated by smolagents, including:

- `tools`
- `managed_agents`
- `authorized_imports` for `CodeAgent`
- `custom_instructions`
- `task`
- `remaining_steps`
- `name`
- `final_answer`
- `code_block_opening_tag` and `code_block_closing_tag` for `CodeAgent`

When adding managed agents, preserve the managed-agent placeholders in the system prompt so the manager knows the delegated agents exist.

## Planning Customization Pattern

A safe pattern for human-in-the-loop planning is:

1. Set `planning_interval` to create a `PlanningStep` early.
2. Register a `PlanningStep` callback.
3. In the callback, display or validate `memory_step.plan`.
4. Mutate `memory_step.plan` if needed.
5. Call `agent.interrupt()` only when the workflow should pause.
6. Resume with `run(..., reset=False)` if continuing from existing memory.

For non-interactive agents, replace human input with deterministic validation logic so runs do not block.

## Memory and Managed Agents

Manager and managed agents have separate memory. Debug delegation by inspecting both:

```python
manager_steps = manager.memory.get_succinct_steps()
worker_steps = manager.managed_agents["worker"].memory.get_succinct_steps()
```

If `provide_run_summary=True` on a managed agent, its report to the manager includes a compact summary generated from `write_memory_to_messages(summary_mode=True)`.

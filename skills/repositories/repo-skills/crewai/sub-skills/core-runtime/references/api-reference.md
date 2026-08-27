# Core Runtime API Reference

This reference covers CrewAI core runtime APIs verified for package version `1.14.8a2`. It is distilled from the current public docs, installed signatures, and core runtime tests.

## Public Imports and Process Values

```python
from crewai import Agent, Crew, Task, Process
from crewai import CrewOutput, TaskOutput
```

`Process` is a string enum with these values:

- `Process.sequential` / `"sequential"`: tasks execute in list order.
- `Process.hierarchical` / `"hierarchical"`: a manager coordinates delegation and validation; `manager_llm` or `manager_agent` is required.

## `Agent` Essentials

Required fields:

- `role: str`
- `goal: str`
- `backstory: str`

Common core fields:

- `llm`: model string or `BaseLLM`; route provider setup to `../llm-and-providers/SKILL.md`.
- `tools`: list of CrewAI tools; route tool implementation and MCP details to `../tools-and-mcp/SKILL.md`.
- `verbose: bool = False`
- `allow_delegation: bool = False`
- `max_iter: int = 25` in the installed signature; docs examples may show older default values.
- `max_rpm`, `max_execution_time`, `max_retry_limit`
- `step_callback`: called after each agent step; agent-level callback overrides crew-level step callback.
- `callbacks`: serializable callable list.
- `allow_code_execution: bool | None = False`
- `code_execution_mode: "safe" | "unsafe" = "safe"`; prefer `safe` and never enable code execution for untrusted projects.
- `respect_context_window: bool = True`
- `planning: bool = False`, `planning_config`
- `reasoning: bool = False`, `max_reasoning_attempts`
- `checkpoint: bool | CheckpointConfig | None`
- `security_config`: controls runtime fingerprinting/identity defaults.

Minimal direct-code shape:

```python
researcher = Agent(
    role="Research Analyst",
    goal="Find accurate facts about {topic}",
    backstory="Careful researcher who writes concise notes.",
    verbose=True,
)
```

## `Task` Essentials

Required fields:

- `description: str`
- `expected_output: str`

Common core fields:

- `name`: useful for JSONC context references and debugging.
- `agent`: direct `Agent` instance, omitted when a hierarchical manager should assign work.
- `context`: list of previous `Task` objects in code, or previous task names in JSONC.
- `async_execution: bool = False`
- `human_input: bool = False`
- `markdown: bool = False`
- `output_file: str | None`, `create_directory: bool = True`
- `callback`: called with task output after completion.
- `guardrail`: one function or one LLM guardrail string.
- `guardrails`: sequence of functions/strings; if present, it takes precedence over `guardrail`.
- `guardrail_max_retries: int = 3`; `max_retries` is deprecated and maps to `guardrail_max_retries`.
- `output_json`, `output_pydantic`, `response_model`: structured output model fields.
- `input_files`: file inputs; route file constraints to `../files-and-multimodal/SKILL.md` if present.

Important validation behavior:

- `expected_output` must be provided directly or through config.
- Only one of `output_json` and `output_pydantic` can be set.
- String guardrails require an assigned agent whose `llm` is a `BaseLLM` instance.
- Function guardrails must accept one output argument and return `(bool, value)`.
- If guardrails fail, CrewAI retries up to `guardrail_max_retries`; the runtime raises after retries are exhausted.

## `Crew` Essentials

Common fields:

- `agents: list[Agent]`
- `tasks: list[Task]`
- `process: Process = Process.sequential`
- `manager_llm` or `manager_agent`: required for `Process.hierarchical`.
- `verbose`, `memory`, `cache`, `max_rpm`
- `function_calling_llm`: crew-level function/tool calling model, overridden by agent-level values.
- `planning: bool = False`, `planning_llm`
- `step_callback`: applied to agents that do not already have an agent-level `step_callback`.
- `task_callback`: applied to tasks that do not already have a task-level callback.
- `before_kickoff_callbacks`: callables that receive and may modify the inputs dict before kickoff.
- `after_kickoff_callbacks`: callables that receive and may modify the `CrewOutput` after kickoff.
- `output_log_file`: `True`, `.txt`, or `.json` path for run logs.
- `stream: bool = False`
- `tracing: bool | None`; route tracing setup to `../observability-and-hooks/SKILL.md`.
- `checkpoint: bool | CheckpointConfig | None`
- `security_config`: default security/fingerprint config.

Hierarchical manager rules:

- `Process.hierarchical` requires `manager_llm` or `manager_agent`.
- A custom `manager_agent` must not also appear in the crew `agents` list.
- CrewAI sets a custom manager agent's `allow_delegation` to `True` during manager creation.
- Tasks may still name agents in hierarchical mode, but manager-driven assignment is the defining behavior.

Minimal sequential crew:

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, report_task],
    process=Process.sequential,
    verbose=True,
)
result = crew.kickoff(inputs={"topic": "AI agents"})
```

Minimal hierarchical crew:

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, report_task],
    process=Process.hierarchical,
    manager_llm="openai/gpt-4o",
)
```

## Kickoff Modes

Synchronous:

- `kickoff(inputs=None, input_files=None, from_checkpoint=None)`: run one crew execution.
- `kickoff_for_each(inputs=[...], input_files=None)`: run one execution per input mapping.

Async/thread-backed:

- `kickoff_async(...)`: thread-backed wrapper around sync kickoff.
- `kickoff_for_each_async(...)`: thread-backed per-input wrapper.

Native async:

- `akickoff(...)`: native async execution path.
- `akickoff_for_each(...)`: native async per-input path.

Use native async methods for high-concurrency workloads because they keep async task, memory, and knowledge operations on the async path. Use thread-backed methods when integrating existing synchronous crews into an async application.

Streaming:

```python
crew = Crew(agents=[researcher], tasks=[task], stream=True)
streaming = crew.kickoff(inputs={"topic": "AI"})
for chunk in streaming:
    print(chunk.content, end="")
final_result = streaming.result
```

## Outputs

`TaskOutput` fields include:

- `raw: str`
- `pydantic: BaseModel | None`
- `json_dict: dict | None`
- `description`, `summary`, `expected_output`, `agent`
- `output_format`: raw, JSON, or Pydantic
- `messages`: messages from the final task execution

`TaskOutput.json` returns JSON only when the output format is JSON. `to_dict()` prioritizes `json_dict`, then Pydantic data, then raw fields. `str(task_output)` prioritizes Pydantic, then JSON dict, then raw.

`CrewOutput` fields include:

- `raw`, `pydantic`, `json_dict`
- `tasks_output: list[TaskOutput]`
- `token_usage`

`CrewOutput.to_dict()` merges structured outputs when present. `CrewOutput` can be indexed by JSON keys when `json_dict` exists.

## Guardrails

A function guardrail:

```python
def validate_short(output: TaskOutput) -> tuple[bool, str]:
    if len(output.raw.split()) > 200:
        return False, "Output must stay under 200 words."
    return True, output.raw.strip()

Task(
    description="Write a concise summary.",
    expected_output="A summary under 200 words.",
    agent=writer,
    guardrail=validate_short,
    guardrail_max_retries=2,
)
```

Multiple guardrails run sequentially; each receives the output from the previous guardrail. When `guardrails` is supplied, the single `guardrail` field is ignored.

String guardrails create LLM-based validators. They are convenient for subjective checks but require a live agent LLM and can incur an LLM call.

## Planning and Reasoning

Crew-level planning:

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, report_task],
    process=Process.sequential,
    planning=True,
    planning_llm="openai/gpt-4o-mini",
)
```

When planning is enabled, CrewAI uses an `AgentPlanner` before each crew iteration and injects the plan into task descriptions. If `planning_llm` is omitted, the default planner model may require OpenAI credentials.

Agent-level reasoning:

```python
analyst = Agent(
    role="Data Analyst",
    goal="Analyze complex datasets",
    backstory="Experienced analyst.",
    reasoning=True,
    max_reasoning_attempts=3,
)
```

Reasoning lets an agent reflect, plan, and decide readiness before executing a task. If reasoning fails, execution continues without the reasoning plan.

## Checkpoint Basics

Enable default checkpointing:

```python
crew = Crew(agents=[researcher, writer], tasks=[research_task, report_task], checkpoint=True)
```

Use full control:

```python
from crewai import CheckpointConfig

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, report_task],
    checkpoint=CheckpointConfig(
        location="./.checkpoints",
        on_events=["task_completed"],
        max_checkpoints=5,
    ),
)
```

Resume:

```python
from crewai import CheckpointConfig

crew = Crew.from_checkpoint(CheckpointConfig(restore_from="./.checkpoints/latest.json"))
crew.kickoff()
```

`Crew`, `Flow`, and `Agent` can accept checkpoint configs. Children inherit from parents unless they override or pass `False`. For Flow checkpoint routing, see `../flows-and-events/SKILL.md`.

# Core Runtime Workflows

Use these recipes when building or reviewing CrewAI runtime code. They avoid LLM execution unless the caller explicitly runs the crew.

## Choose JSONC or Direct Code

Prefer JSONC when:

- The crew is a normal project created with the JSON-first layout.
- Non-Python users need to edit roles, goals, task descriptions, inputs, or output files.
- The team wants declarative agent/task definitions and runtime prompting for missing placeholders.

Prefer direct code when:

- You need dynamic Python construction, inline Pydantic models, complex callback wiring, or nontrivial task generation.
- The crew is embedded in a larger Python service or test harness.
- You need type checking and ordinary Python refactoring around runtime objects.

Classic YAML/decorator projects are still supported, but new projects generally use JSONC. CLI creation and template migration details belong in `../cli-and-projects/SKILL.md`.

## Build a Sequential Crew in Direct Code

```python
from crewai import Agent, Crew, Process, Task

researcher = Agent(
    role="Market Researcher",
    goal="Find reliable facts about {topic}",
    backstory="Careful researcher who separates evidence from speculation.",
    verbose=True,
)

writer = Agent(
    role="Report Writer",
    goal="Turn research into a concise markdown report",
    backstory="Editor who writes practical executive summaries.",
)

research = Task(
    description="Research {topic} and collect five key findings.",
    expected_output="Five concise bullets with source-quality notes.",
    agent=researcher,
)

report = Task(
    description="Write a report from the research notes.",
    expected_output="A markdown report with findings and recommendations.",
    agent=writer,
    context=[research],
    markdown=True,
    output_file="output/report.md",
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research, report],
    process=Process.sequential,
    verbose=True,
)
```

Before calling `kickoff()`, check:

- Every agent has `role`, `goal`, and `backstory`.
- Every task has `description` and `expected_output`.
- Context tasks point to earlier task objects.
- Placeholders in descriptions/expected outputs have matching keys in `inputs`.
- `output_file` paths are intentional and safe for the current working directory.

## Build a Hierarchical Crew

```python
crew = Crew(
    agents=[researcher, writer, reviewer],
    tasks=[research, report, review],
    process=Process.hierarchical,
    manager_llm="openai/gpt-4o",
)
```

Rules:

- Provide `manager_llm` or `manager_agent`.
- Do not include a custom `manager_agent` in `agents`.
- Do not give a custom manager agent its own tools unless you have checked current CrewAI behavior; tests cover manager-agent constraints and delegation tooling separately.
- In hierarchical mode, tasks can omit explicit agents so the manager delegates based on roles and goals.
- If tasks still name agents, ensure those agents are present in the crew and the manager can delegate to them.

When debugging hierarchy, first instantiate the `Crew` object without calling `kickoff()`. Constructor validation catches missing manager fields and manager-in-agent-list errors before any LLM run.

## Run and Inspect Outputs

```python
result = crew.kickoff(inputs={"topic": "AI agents"})
print(result.raw)

for task_output in result.tasks_output:
    print(task_output.description)
    print(task_output.raw)
```

For structured outputs:

```python
from pydantic import BaseModel

class ScoreOutput(BaseModel):
    score: int
    rationale: str

score_task = Task(
    description="Score the title quality.",
    expected_output="A score and a short rationale.",
    agent=analyst,
    output_pydantic=ScoreOutput,
)
```

Use exactly one structured output selector per task:

- `output_pydantic=Model`: task output exposes `pydantic` and string conversion prioritizes the model.
- `output_json=Model`: task output exposes `json_dict` and `.json` is available when the output format is JSON.
- `response_model=Model`: use when the selected executor path supports the response-model field; avoid setting it alongside `output_json`/`output_pydantic` unless current code explicitly requires that combination.

## Use Guardrails Safely

Function guardrails are deterministic and best for exact validation:

```python
def require_bullets(output):
    lines = [line for line in output.raw.splitlines() if line.strip()]
    if not all(line.lstrip().startswith("-") for line in lines[:3]):
        return False, "Start the first three non-empty lines with '-' bullets."
    return True, output.raw

Task(
    description="List implementation risks.",
    expected_output="A bullet list of risks.",
    agent=analyst,
    guardrail=require_bullets,
    guardrail_max_retries=2,
)
```

String guardrails are useful for tone, style, or subjective criteria:

```python
Task(
    description="Write a stakeholder update.",
    expected_output="A professional update with no confidential details.",
    agent=writer,
    guardrails=[
        "The update must be professional and concise.",
        "The update must not reveal secrets, API keys, or private customer data.",
    ],
)
```

Guardrail review checklist:

- Function returns `(True, value)` or `(False, actionable_feedback)`.
- Failure feedback tells the agent exactly what to fix.
- `guardrail_max_retries` is low enough to avoid runaway correction loops.
- `guardrails` is not accidentally masking a `guardrail` value.
- String guardrails are only used when an agent with a concrete `BaseLLM` instance is available.

## Place Callbacks Deliberately

Callback levels:

- `Agent.step_callback`: most specific; called after that agent's steps.
- `Crew.step_callback`: applied only to agents that do not already define `step_callback`.
- `Task.callback`: called for that task's output.
- `Crew.task_callback`: applied to tasks that do not already define a distinct task callback.
- `Crew.before_kickoff_callbacks`: receive and may change inputs before kickoff.
- `Crew.after_kickoff_callbacks`: receive and may change `CrewOutput` after kickoff.

Safe callback guidance:

- Keep callbacks idempotent; retries and replay can call logic more than once.
- Avoid network calls and credential access inside validation-only code.
- In JSONC, `{"python": "module.attribute"}` callback references execute local Python at project load time; treat them as trusted-code boundaries.
- For tracing or event-bus listeners, route to `../observability-and-hooks/SKILL.md`.

## Add Planning or Reasoning

Use crew planning when the whole crew benefits from pre-task planning:

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research, report],
    process=Process.sequential,
    planning=True,
    planning_llm="openai/gpt-4o-mini",
)
```

Use agent reasoning when a specific agent should reflect before each task:

```python
analyst = Agent(
    role="Risk Analyst",
    goal="Identify high-impact risks before execution",
    backstory="Systematic reviewer.",
    reasoning=True,
    max_reasoning_attempts=3,
)
```

Operational notes:

- Planning and reasoning can add LLM calls before task execution.
- Specify `planning_llm` instead of relying on a default if the runtime environment does not use OpenAI.
- Reasoning failures are logged and task execution proceeds without a reasoning plan.

## Use Checkpoints Without Confusing Training or Replay

Default crew checkpointing:

```python
crew = Crew(agents=[researcher, writer], tasks=[research, report], checkpoint=True)
```

Custom checkpointing:

```python
from crewai import CheckpointConfig

crew = Crew(
    agents=[researcher, writer],
    tasks=[research, report],
    checkpoint=CheckpointConfig(
        location="./.checkpoints",
        on_events=["task_completed"],
        max_checkpoints=5,
    ),
)
```

Resume from a checkpoint file:

```python
from crewai import CheckpointConfig, Crew

crew = Crew.from_checkpoint(CheckpointConfig(restore_from="./.checkpoints/latest.json"))
crew.kickoff()
```

Do not confuse these features:

- Checkpointing saves execution state and supports resume/fork.
- CLI replay starts from saved task output history; route command syntax to `../cli-and-projects/SKILL.md`.
- Training files tune agent behavior over repeated runs; route training command details to `../cli-and-projects/SKILL.md`.

## Convert Direct Code to JSONC

1. Move each agent's `role`, `goal`, `backstory`, simple `llm`, and runtime options into `agents/<name>.jsonc`.
2. Move ordered tasks into `crew.jsonc` with stable `name` values.
3. Replace `context=[task_obj]` with `context: ["previous_task_name"]`.
4. Put simple booleans and strings directly in JSONC; put callback references as `{"python": "module.attribute"}` only for trusted project code.
5. Preserve structured output intent by naming the model reference consistently with the project loader conventions; if the model is complex or inline-only, keep direct code.
6. Run `scripts/validate_crew_definition.py <project-dir>` before any LLM-backed `crewai run`.

## Convert JSONC to Direct Code

1. Create one `Agent(...)` per `agents/<name>.jsonc` file.
2. Create `Task(...)` objects in the order listed in `crew.jsonc`.
3. Convert `context` task names to earlier task variables.
4. Convert string process values to `Process.sequential` or `Process.hierarchical`.
5. Replace `{"python": "module.attribute"}` with actual imported callables only after reviewing the target code.
6. Keep tools/MCP/provider configuration routed to the relevant sibling sub-skills when the conversion requires deeper setup.

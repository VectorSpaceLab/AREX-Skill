# Project Templates and Layouts

CrewAI projects are created by `crewai create`. The CLI currently supports JSON-first crew projects, classic Python/YAML crew projects, and Python flow projects.

## Which Scaffold to Choose

Choose JSON-first crew when:

- The app is primarily a crew with agents and tasks.
- The user wants editable `agents/*.jsonc` and `crew.jsonc` files.
- The project can treat Python references and custom tools as explicit trusted-code extension points.
- The user is migrating from hand-written crews and wants less Python ceremony.

Choose classic crew with `--classic` when:

- The project already relies on `@CrewBase`, `@agent`, `@task`, `@crew`, YAML config files, or custom Python setup in `crew.py`.
- The user needs direct Python control over crew construction, training/replay/test entrypoints, callbacks, or custom classes.

Choose flow when:

- The app needs deterministic orchestration, state, branching, plotting, trigger payloads, or multiple crews in a workflow.
- The user is building a production app where flow state and execution order should be explicit. Route flow design details to [flows and events](../../flows-and-events/SKILL.md).

## JSON-First Crew Layout

A default crew scaffold creates a flat JSONC-centered project:

```text
my_crew/
├── .gitignore
├── agents/
│   └── researcher.jsonc
├── crew.jsonc
├── knowledge/
├── pyproject.toml
├── README.md
├── skills/
└── tools/
```

Important facts:

- `agents/<name>.jsonc` filenames are referenced by `crew.jsonc` under `agents` and by each task's `agent` field.
- `crew.jsonc` owns task order, process, crew-level memory, runtime input defaults, and optional advanced crew fields.
- `tools/` contains local custom tool code referenced as `custom:<name>` from agent tool lists.
- `knowledge/` and `skills/` are included in the wheel target so they can be packaged with the project.
- The JSON crew `pyproject.toml` uses `[tool.crewai] type = "crew"` and a Hatch wheel target that includes `agents`, `crew.jsonc`, `tools`, `knowledge`, and `skills`.
- The generated README warns that `custom:<name>` loads `tools/<name>.py` as local Python code when the crew loads.

Minimal `crew.jsonc` shape:

```jsonc
{
  "name": "Research Crew",
  "agents": ["researcher"],
  "tasks": [
    {
      "name": "research_task",
      "description": "Research {topic} and summarize key findings.",
      "expected_output": "A concise markdown report.",
      "agent": "researcher",
      "output_file": "output/report.md",
      "markdown": true
    }
  ],
  "process": "sequential",
  "verbose": true,
  "memory": false,
  "inputs": {
    "topic": "AI Agents"
  }
}
```

Minimal `agents/researcher.jsonc` shape:

```jsonc
{
  "role": "Senior {topic} Researcher",
  "goal": "Find accurate, useful information about {topic}.",
  "backstory": "You organize complex information into clear findings.",
  "llm": "openai/gpt-4o",
  "tools": [],
  "settings": {
    "verbose": false,
    "allow_delegation": false
  }
}
```

JSON crew advanced fields are intentionally close to runtime object options but remain data-first:

- Agent fields can include `llm` as provider/model string or object form, `function_calling_llm`, `tools`, guardrails, `step_callback`, `reasoning`, `planning_config`, `multimodal`, code-execution controls, knowledge fields, and security settings.
- Task fields can include `context`, `output_file`, `markdown`, `input_files`, guardrails, `type`, `condition`, `output_json`, `output_pydantic`, `response_model`, `converter_cls`, `tools`, human input, async execution, and security settings.
- Crew fields can include `process`, `memory`, `planning`, `planning_llm`, `manager_llm`, `manager_agent`, kickoff callbacks, `function_calling_llm`, `output_log_file`, `stream`, `tracing`, `security_config`, and `chat_llm`.

Route exact field semantics and object API decisions to [core runtime](../../core-runtime/SKILL.md).

## Placeholder Inputs

Use `{placeholder}` in agent text, task text, and task output file paths. `crewai run` prompts for placeholders missing from `inputs`; `CREWAI_DMN=true` exits with a missing-input error instead.

Good pattern:

```jsonc
{
  "tasks": [
    {
      "name": "write_report",
      "description": "Write a report about {topic} for {target-audience}.",
      "expected_output": "A markdown report.",
      "agent": "researcher"
    }
  ],
  "inputs": {
    "topic": "AI Agents",
    "target-audience": "engineering leaders"
  }
}
```

Placeholder names may include hyphens after the first character, such as `{target-audience}`.

## Trust Boundaries in JSONC Projects

JSONC data can still route into executable code:

- `custom:<name>` loads and executes Python from `tools/<name>.py`.
- `{"python": "module.attribute"}` references load module-level functions/classes for custom agents, conditions, converters, callbacks, output models, and related extension points.
- Built-in tool class names such as `SerperDevTool` may require credentials or network access at runtime.

Before running an unfamiliar project, inspect `tools/`, JSONC Python references, callback fields, and any provider/tool credentials. Route custom tool implementation review to [tools and MCP](../../tools-and-mcp/SKILL.md).

## Classic Crew Layout

`crewai create crew <name> --classic` creates a source-layout Python package:

```text
my_crew/
├── .gitignore
├── AGENTS.md
├── knowledge/
│   └── user_preference.txt
├── pyproject.toml
├── README.md
├── src/
│   └── my_crew/
│       ├── __init__.py
│       ├── config/
│       │   ├── agents.yaml
│       │   └── tasks.yaml
│       ├── crew.py
│       ├── main.py
│       └── tools/
│           ├── __init__.py
│           └── custom_tool.py
└── tests/
```

The classic `pyproject.toml` includes script entry points:

```toml
[project.scripts]
my_crew = "my_crew.main:run"
run_crew = "my_crew.main:run"
train = "my_crew.main:train"
replay = "my_crew.main:replay"
test = "my_crew.main:test"
run_with_trigger = "my_crew.main:run_with_trigger"

[tool.crewai]
type = "crew"
```

`crewai run`, `crewai train`, `crewai replay`, and `crewai test` depend on these script names. If they are missing or renamed, CLI commands fail even when `crew.py` imports correctly.

Classic `crew.py` uses `@CrewBase` and decorated methods:

```python
@CrewBase
class MyCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent: ...

    @task
    def research_task(self) -> Task: ...

    @crew
    def crew(self) -> Crew: ...
```

`main.py` supplies default `inputs`, calls `MyCrew().crew().kickoff(...)`, and implements `train`, `replay`, `test`, and `run_with_trigger` script functions.

## Flow Layout

`crewai create flow <name>` creates:

```text
my_flow/
├── .env
├── .gitignore
├── AGENTS.md
├── pyproject.toml
├── README.md
├── src/
│   └── my_flow/
│       ├── __init__.py
│       ├── main.py
│       ├── crews/
│       │   └── content_crew/
│       │       ├── config/
│       │       │   ├── agents.yaml
│       │       │   └── tasks.yaml
│       │       └── content_crew.py
│       └── tools/
│           ├── __init__.py
│           └── custom_tool.py
└── tests/
```

The flow `pyproject.toml` includes:

```toml
[project.scripts]
kickoff = "my_flow.main:kickoff"
run_crew = "my_flow.main:kickoff"
plot = "my_flow.main:plot"
run_with_trigger = "my_flow.main:run_with_trigger"

[tool.crewai]
type = "flow"
```

The generated `main.py` defines a Pydantic state model, a `Flow[...]` subclass, `@start()` and `@listen(...)` methods, `kickoff()`, `plot()`, and `run_with_trigger()`. `crewai run` detects `[tool.crewai].type = "flow"` and runs the `kickoff` script; `crewai flow plot` runs the `plot` script.

## Migration Notes

From classic crew to JSON-first:

1. Identify YAML agents and tasks from `config/agents.yaml` and `config/tasks.yaml`.
2. Convert each agent into `agents/<name>.jsonc`.
3. Convert task order and context into `crew.jsonc` `tasks` entries.
4. Move default runtime inputs from `main.py` into `crew.jsonc` `inputs` when possible.
5. Keep Python-only behavior as explicit `{"python": "module.attribute"}` references or leave the project classic if it relies heavily on dynamic construction.
6. Preserve custom tools under `tools/` and reference them as `custom:<name>` only after reviewing safety.

From JSON-first to classic:

1. Use `crewai create crew <new_name> --classic` to generate script names and package layout.
2. Translate JSON agent/task fields into YAML config and decorated methods.
3. Move default inputs into `main.py`.
4. Keep `[tool.crewai] type = "crew"` and required script entry points.

## Template Import Notes

The source templates are evidence, not runtime dependencies. This skill distills their layouts and critical entry points instead of copying entire generated skeletons because future agents can create fresh projects through `crewai create`, and template details may change with the installed CLI. Use `inspect_crewai_cli.py --commands` plus `crewai create --help` to confirm exact behavior in a target environment.

## Common Layout Checks

Use the bundled inspector before running user code:

```bash
python scripts/inspect_crewai_cli.py --project . --json
```

Check for:

- `pyproject.toml` present and parseable.
- `[tool.crewai].type` set to `crew` or `flow` when possible.
- JSON crew marker `crew.jsonc` or `crew.json` plus `agents/` for JSON projects.
- `src/<normalized_project_name>/crew.py` and config YAML files for classic crew projects.
- `src/<normalized_project_name>/main.py` with flow entry points for flow projects.
- Required script names in `[project.scripts]` for classic crew or flow projects.
- `uv.lock` or `poetry.lock` before deployment.

Run `crewai deploy validate` for a fuller validation pass once it is safe to import the project code.

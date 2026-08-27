# JSONC Crew Runtime Reference

CrewAI JSON-first projects use `crew.jsonc` or `crew.json` plus one file per agent under `agents/`. JSONC supports comments and trailing commas. If both `.jsonc` and `.json` exist for the same agent, the JSONC file takes precedence.

## Runtime Layout

Typical layout:

```text
project/
  crew.jsonc
  agents/
    researcher.jsonc
    writer.jsonc
  tools/
    custom_tool.py
```

`crew.jsonc` controls crew-level settings, ordered tasks, and default inputs. Agent files define one `Agent` each.

## Agent File Shape

```jsonc
{
  "role": "{topic} Senior Researcher",
  "goal": "Find accurate and current information about {topic}.",
  "backstory": "You are a careful researcher who cites clear evidence.",
  "llm": "openai/gpt-4o",
  "tools": ["SerperDevTool"],
  "settings": {
    "verbose": true,
    "allow_delegation": false,
    "max_iter": 20
  }
}
```

Required fields:

- `role`
- `goal`
- `backstory`

Agent files support public `Agent` fields. Common fields include `llm`, `tools`, `function_calling_llm`, `guardrail`, `step_callback`, `verbose`, `allow_delegation`, `max_iter`, `max_rpm`, `memory`, `cache`, `planning`, `planning_config`, `reasoning`, `max_reasoning_attempts`, `checkpoint`, and `use_system_prompt`.

Fields may be placed at the top level or under `settings`; when the same option appears in both places, `settings` values take precedence.

## Crew File Shape

```jsonc
{
  "name": "Market Research Crew",
  "agents": ["researcher", "writer"],
  "tasks": [
    {
      "name": "research",
      "description": "Research {topic} and collect the most relevant facts.",
      "expected_output": "Structured research notes about {topic}.",
      "agent": "researcher"
    },
    {
      "name": "report",
      "description": "Analyze the research and write a concise report.",
      "expected_output": "A markdown report with findings and recommendations.",
      "agent": "writer",
      "context": ["research"],
      "markdown": true,
      "output_file": "output/report.md"
    }
  ],
  "process": "sequential",
  "verbose": true,
  "inputs": {
    "topic": "AI Agents"
  }
}
```

Crew-level fields commonly used by the runtime:

- `name`
- `agents`: names resolving to `agents/<name>.jsonc` first, then `agents/<name>.json`.
- `tasks`: ordered task entries.
- `process`: `"sequential"` or `"hierarchical"`.
- `verbose`, `memory`, `cache`, `max_rpm`
- `planning`, `planning_llm`
- `manager_llm`, `manager_agent`
- `function_calling_llm`
- `output_log_file`
- `stream`, `tracing`
- `before_kickoff_callbacks`, `after_kickoff_callbacks`
- `inputs`: defaults for `{placeholder}` substitution.

For hierarchical crews, set `"process": "hierarchical"` and provide either `manager_llm` or `manager_agent`. A `manager_agent` can reference an agent file that is not included in the top-level `agents` list. Do not include a custom manager in `agents`.

## Task Entries

Required fields:

- `description`
- `expected_output`

Common optional fields:

- `name`: use stable lowercase names for context references.
- `agent`: agent name from `agents`; can be omitted when a hierarchical manager should assign the task.
- `context`: list of prior task names.
- `output_file`, `create_directory`
- `tools`
- `human_input`, `async_execution`, `markdown`
- `guardrail`, `guardrails`, `guardrail_max_retries`
- `input_files`
- `output_json`, `output_pydantic`, `response_model`, `converter_cls`
- `callback`
- `type: "ConditionalTask"` plus `condition` for conditional tasks.

Context rule: task context must point to tasks already listed earlier in `tasks`. Forward references are rejected because sequential dependencies must be explicit.

## Placeholders and Inputs

Use `{placeholder}` values in agent `role`, `goal`, `backstory`, task `description`, task `expected_output`, and task `output_file`. Put defaults in `crew.jsonc` under `inputs`.

At runtime, `crewai run` prompts for missing placeholder values. In validation or code generation, collect placeholders and check whether `inputs` has safe defaults for expected noninteractive runs.

## Callback and Custom Tool Trust Boundary

JSONC can reference Python callables:

```jsonc
{
  "before_kickoff_callbacks": [{"python": "my_project.callbacks.normalize_inputs"}],
  "after_kickoff_callbacks": [{"python": "my_project.callbacks.store_output"}]
}
```

Custom tools use `custom:<name>` and load `tools/<name>.py` at runtime.

Security rule: only run JSONC projects from trusted sources. `custom:<name>` and `{"python": "module.attribute"}` references execute local Python when the crew loads. For static review, use the bundled validator script because it does not import project tools or callbacks.

## Guardrails in JSONC

Use string guardrails for natural-language checks:

```jsonc
{
  "name": "report",
  "description": "Write a report from the research.",
  "expected_output": "A concise markdown report.",
  "agent": "writer",
  "guardrails": [
    "The report must be written in professional tone.",
    "The report must not include private credentials or secrets."
  ],
  "guardrail_max_retries": 2
}
```

For deterministic function guardrails, reference trusted Python code. Keep retry counts low and make failure messages actionable.

## Structured Outputs in JSONC

Avoid setting both `output_json` and `output_pydantic` on the same task. CrewAI validates that only one structured output type is active.

Use:

- `output_json` when downstream code expects a JSON dictionary and `.json` output.
- `output_pydantic` when downstream code expects a Pydantic model object.
- `response_model` only when the project's executor path and model loading convention support it.

When migrating from direct code, inline Python model classes may not map cleanly to JSONC. Keep direct code if the output model is complex, generated dynamically, or not importable by a simple trusted module reference.

## Static Validation Before Running

Run the bundled validator from this sub-skill before any LLM-backed execution:

```bash
python scripts/validate_crew_definition.py path/to/project
```

The validator checks:

- `crew.jsonc` or `crew.json` exists and parses.
- `agents` is a list of names.
- Each listed agent file exists and has `role`, `goal`, and `backstory`.
- Each task has `description` and `expected_output`.
- Task `context` references are known prior tasks.
- Task `agent` references are declared agents, unless omitted for hierarchical routing.
- Hierarchical process has `manager_llm` or `manager_agent`.
- Custom Python callbacks and custom tools are reported as trust warnings, not executed.
- `output_json` and `output_pydantic` are not both set.

The script is intentionally conservative. Passing it does not guarantee a crew will run; it only catches common shape and trust-boundary errors without importing project code or calling LLMs.

## Migration Checklist

Direct code to JSONC:

- Give every task a stable `name` before replacing object references with strings.
- Move agent public fields into `agents/<name>.jsonc`.
- Move crew-level process, callbacks, planning, checkpointing, logging, and inputs into `crew.jsonc`.
- Convert function references to trusted `{"python": "module.attribute"}` references only when they are importable and reviewed.
- Keep direct code for dynamic task generation, inline output models, or complex callback wiring.

JSONC to direct code:

- Preserve task order exactly.
- Create task variables before tasks that use them as context.
- Convert process strings to `Process.sequential` or `Process.hierarchical`.
- Import callback functions explicitly after reviewing them.
- Instantiate tools or MCP config through `../tools-and-mcp/SKILL.md` guidance.

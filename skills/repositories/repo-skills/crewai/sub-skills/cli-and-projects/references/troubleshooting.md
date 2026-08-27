# CLI and Project Troubleshooting

Start with read-only checks before running project code:

```bash
crewai version
crewai create --help
python scripts/inspect_crewai_cli.py --project . --json
crewai deploy validate
```

Do not run `crewai run`, `train`, `test`, `replay`, `chat`, deployment create/push, or checkpoint resume until you trust the project code and the user approves any LLM/network/destructive behavior.

## Missing Project Root or `pyproject.toml`

Symptoms:

- `crewai uv ...` says a valid `pyproject.toml` is required.
- `crewai run` cannot read project metadata.
- `crewai deploy validate` reports `missing_pyproject`.

Checks:

1. Confirm the current working directory is the project root, not `src/<package>/` or a parent workspace.
2. Look for `pyproject.toml`, `crew.jsonc`, `agents/`, `src/`, `uv.lock`, and `poetry.lock`.
3. Run `python scripts/inspect_crewai_cli.py --project . --json`.

Fixes:

- Move to the directory containing the project's `pyproject.toml`.
- If the project is not scaffolded, create one with `crewai create crew <name>`, `crewai create crew <name> --classic`, or `crewai create flow <name>`.
- If only `crew.jsonc` exists, JSON crew loading can work in limited cases, but deploy validation expects a complete project root.

## JSONC vs Classic Confusion

Symptoms:

- A user edits `agents/*.jsonc` but the CLI runs `src/<package>/crew.py`.
- A flow project with `crew.jsonc` is treated unexpectedly.
- `crewai run` cannot find `run_crew`, `kickoff`, or expected scripts.

Rules:

- JSON crew projects have `crew.jsonc` or `crew.json` and are not declared as flow in `[tool.crewai]`.
- Flow projects are declared with `[tool.crewai] type = "flow"`; that declaration wins even if a `crew.jsonc` file exists.
- Classic crew projects use `[tool.crewai] type = "crew"`, `src/<package>/crew.py`, config YAML files, and `[project.scripts] run_crew`, `train`, `replay`, and `test`.

Fixes:

- For JSON-first crews, ensure `crew.jsonc`, `agents/`, and `[tool.crewai] type = "crew"` are consistent.
- For classic crews, restore `src/<package>/crew.py`, `src/<package>/config/agents.yaml`, `src/<package>/config/tasks.yaml`, and script entry points.
- For flows, keep `[tool.crewai] type = "flow"`, `main.py`, `kickoff`, and `plot` entry points.

## Missing Placeholder Inputs

Symptoms:

- Interactive `crewai run` prompts for values unexpectedly.
- `CREWAI_DMN=true crewai run` fails with `Missing runtime inputs`.
- Output file paths or agent/task text still contain `{topic}`-style markers.

Checks:

- Search `crew.jsonc` and `agents/*.jsonc` for `{placeholder}` values.
- Remember placeholders can appear in agent `role`, `goal`, `backstory`, task `description`, task `expected_output`, and task `output_file`.
- Hyphenated placeholders such as `{target-audience}` are valid.

Fix:

```jsonc
{
  "inputs": {
    "topic": "AI Agents",
    "target-audience": "engineering leaders"
  }
}
```

In interactive mode, leaving defaults out can be intentional because the CLI prompts the user. In non-interactive mode, add all defaults before running.

## Untrusted Custom Tools and Python References

Symptoms:

- JSONC includes `custom:<name>` tool references.
- JSONC includes `{"python": "module.attribute"}` for custom agents, callbacks, conditions, converters, output models, or guardrails.
- CLI validation/import runs execute unexpected local code.

Risk:

- These references import and run Python from the project. They may read files, contact networks, call LLMs, or mutate state.

Safe approach:

1. Inspect `tools/` and referenced modules before running.
2. Review callback and guardrail references.
3. Confirm built-in tools' credentials and network behavior.
4. Route tool implementation concerns to [tools and MCP](../../tools-and-mcp/SKILL.md).
5. Run only read-only inspector checks until the user approves execution.

## `chat_llm` Missing for `crewai chat`

Symptoms:

- `crewai chat` starts but cannot orchestrate a session.
- The crew definition lacks a chat-specific LLM.

Fix for JSON-first crews:

```jsonc
{
  "chat_llm": "openai/gpt-4o"
}
```

Object form is also accepted for provider-specific setup:

```jsonc
{
  "chat_llm": {"model": "llama3", "provider": "ollama", "base_url": "http://localhost:11434"}
}
```

Fix for classic crews:

```python
return Crew(
    agents=self.agents,
    tasks=self.tasks,
    process=Process.sequential,
    chat_llm="openai/gpt-4o",
)
```

Route model/provider setup to [LLM and providers](../../llm-and-providers/SKILL.md) if that sibling exists in the generated skill tree.

## `uv` Wrapper and Dependency Issues

Symptoms:

- `crewai uv ...` fails outside a project root.
- `crewai run` installs dependencies unexpectedly.
- JSON crew run fails during `uv run --no-sync` or `uv sync`.
- Project has `poetry.lock` but no `uv.lock`.

Rules:

- `crewai uv` first reads `pyproject.toml` and builds an environment with tool credentials.
- JSON crew execution uses the project environment when `pyproject.toml` exists.
- If a JSON project has a `uv.lock` but no `.venv`, the CLI syncs dependencies from the lockfile.
- If there is no lockfile, the CLI may install dependencies before running.
- If only `poetry.lock` exists, JSON crew run uses `poetry run python -c ...` and skips `uv` sync.

Fixes:

- Run from the project root.
- Prefer `uv lock` and `crewai install` after dependency edits.
- Do not run dependency-changing commands in user repositories without approval.
- For old Poetry projects, `crewai update` can migrate project metadata toward `uv`; ask before running it.

## Deploy Credentials and Private Package Registries

Symptoms:

- `crewai deploy validate` passes locally but create/push fails.
- Validation warns `env_vars_not_in_dotenv` or `llm_init_missing_key`.
- Hosted deployment cannot install private dependencies.
- Project imports a provider at module import time and fails before runtime.

Fixes:

- Add required variable names to `.env` locally and to CrewAI AMP deployment environment; never paste secret values into logs.
- Move LLM/provider construction out of import-time globals and into agent or crew methods where possible.
- Add provider extras with targeted dependencies, for example `uv add "crewai[azure-ai-inference]"` when validation recommends it.
- Ensure private package registry credentials are configured in the deployment environment, not hardcoded in `pyproject.toml`.
- Run `crewai deploy validate` again before create/push.

## Checkpoints and Memory State Surprises

Symptoms:

- `crewai checkpoint` opens a TUI unexpectedly.
- `checkpoint resume` restarts from a state the user did not expect.
- `reset-memories --all` deletes more state than intended.

Safe approach:

- Use `crewai checkpoint list` and `crewai checkpoint info` before `resume`, `diff`, or `prune`.
- Use `crewai checkpoint prune --dry-run` before pruning.
- Prefer targeted memory reset flags over `--all` when preserving knowledge or latest kickoff output matters.
- Route memory store behavior to [memory, knowledge, and RAG](../../memory-knowledge-and-rag/SKILL.md).

## Flow Project Runs as Crew or Crew Project Runs as Flow

Symptoms:

- `crewai run` says `Running the Flow` for a crew project.
- A flow's nested starter crew causes JSON crew detection confusion.

Checks and fixes:

- Inspect `[tool.crewai].type` in `pyproject.toml`.
- For flow projects, keep `type = "flow"` and ensure `src/<package>/main.py` defines a `Flow` subclass.
- For JSON crew projects, keep `type = "crew"` or omit flow declaration, and keep `crew.jsonc` at project root.
- For classic crew projects, ensure script `run_crew` points to `main:run`.

## Difficult Usability Cases This Sub-Skill Supports

- Diagnose a JSON-first crew where `crewai run` fails in non-interactive mode because `{topic}` and `{target-audience}` placeholders are missing from `inputs`, while `custom:browser_tool` and Python callback references make the project unsafe to execute before review.
- Choose JSON-first versus classic scaffolding for a migration where existing YAML `@CrewBase` code uses callbacks and custom classes, but the user wants future agents to edit agent/task definitions safely.

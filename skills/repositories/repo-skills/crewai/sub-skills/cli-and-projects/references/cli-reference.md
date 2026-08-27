# CrewAI CLI Reference

This reference summarizes the installed CrewAI CLI surface and behavior needed by coding agents. Use it with `../scripts/inspect_crewai_cli.py` when exact installed command help matters.

## Installation and Version Checks

CrewAI requires Python `>=3.10,<3.14`. The CLI is normally installed as a `uv` tool or as part of a project dependency set:

```bash
uv tool install crewai
crewai version
crewai version --tools
crewai create --help
```

`crewai version --tools` prints the `crewai-tools` package version when installed. In the inspected package set, `crewai`, `crewai-cli`, `crewai-tools`, `crewai-files`, `crewai-core`, and `crewai-devtools` were all version `1.14.8a2`; future agents should verify the installed version instead of assuming this pin.

## Top-Level Command Groups

The installed command tree includes these top-level commands:

- Project execution and lifecycle: `create`, `install`, `run`, `train`, `test`, `replay`, `chat`, `update`, `uv`, `version`.
- Runtime data: `log-tasks-outputs`, `reset-memories`, `memory`, `checkpoint`.
- Flow support: `flow kickoff`, `flow plot`, `flow add-crew`.
- Deployment and hosted operations: `login`, `logout`, `deploy`, `org`, `enterprise`, `template`, `triggers`, `traces`, `config`, `env`.
- Tool and experimental repositories: `tool`, `experimental skill`.

Some hosted and repository commands require authentication, remote APIs, or hosted CrewAI AMP access. Treat them as credential-bound unless the user explicitly asks to use them.

## Project Creation

```bash
crewai create crew <name>
crewai create crew <name> --classic
crewai create flow <name>
```

`crewai create crew <name>` creates a JSON-first crew project by default. Use `--classic` only when the user needs the older Python/YAML scaffold with `src/<package>/crew.py`, `src/<package>/config/agents.yaml`, and `src/<package>/config/tasks.yaml`.

`crewai create flow <name>` creates a Python flow project under `src/<package>/` with a starter crew under `src/<package>/crews/content_crew/`.

Useful creation flags and modes:

- `--provider <name>` preselects a provider for crew scaffolding.
- `--skip_provider` skips provider validation/prompting.
- `--classic` selects the classic Python/YAML crew template.
- `CREWAI_DMN=true` makes `create` non-interactive: `TYPE` and `NAME` are required, provider prompts are skipped, and JSON crew defaults are deterministic.

Project names are normalized to lowercase Python package/module names by replacing spaces and hyphens with underscores and removing unsupported characters. Names that become invalid identifiers, start with a digit, become a Python keyword, or collide with reserved script names are rejected.

## Install and Run

```bash
crewai install
crewai run
crewai run -f trained_agents_data.pkl
crewai run --definition flow.yaml --inputs '{"topic":"AI"}'
```

`crewai install` delegates to the project package manager through the CLI's install helper. It accepts extra unknown options and passes them through to the underlying install command.

`crewai run` routes by project type:

- JSON crew project: finds `crew.jsonc` or `crew.json`, unless `[tool.crewai].type = "flow"` declares the project as a flow. It may install/sync dependencies first, then runs through the project environment with `uv run --no-sync python -c ...` or `poetry run python -c ...` for Poetry-only lockfiles.
- Classic crew project: reads `pyproject.toml`, treats `[tool.crewai].type != "flow"` as a standard crew, and runs `uv run run_crew`.
- Flow project: reads `[tool.crewai].type = "flow"` and runs `uv run kickoff`.
- Experimental flow definition: `crewai run --definition <path-or-inline-yaml-json> --inputs <json-object>` bypasses normal project detection; `--inputs` requires `--definition`.

`-f/--filename` on `run`, `test`, and `replay` forwards a trained-agents pickle path through `CREWAI_TRAINED_AGENTS_FILE`; JSON crews receive it in-process and classic commands receive it in the subprocess environment.

## JSON Crew Runtime Inputs

JSON crew projects can use `{placeholder}` values in agent roles/goals/backstories and task descriptions/expected outputs/output file paths. `crewai run` prompts for missing values interactively. In `CREWAI_DMN` mode, missing values are an error; add defaults to `crew.jsonc` under `inputs`:

```jsonc
{
  "inputs": {
    "topic": "Artificial Intelligence in Healthcare",
    "target-audience": "executives"
  }
}
```

Placeholder names may include hyphens after the first character, such as `{target-audience}`.

## Train, Test, Replay, and Logs

```bash
crewai train -n 10 -f trained_agents_data.pkl
crewai test -n 5 -m gpt-4o
crewai replay -t <task_id>
crewai replay -t <task_id> -f trained_agents_data.pkl
crewai log-tasks-outputs
```

- `train` prints the iteration count and delegates to `uv run train <n_iterations> <filename>`.
- `test` prints the iteration/model pair and delegates to `uv run test <n_iterations> <model>`. The default installed CLI model was `gpt-5.4-mini`; confirm with `crewai test --help` for the active installation.
- `replay` delegates to `uv run replay <task_id>` and may load a trained-agents file.
- `log-tasks-outputs` prints latest kickoff task output metadata, or reports that no task outputs are available.

These commands can execute the user's project code and LLM/tool calls. Do not run them on untrusted projects without approval.

## Chat

```bash
crewai chat
```

`crewai chat` starts an interactive crew conversation. It requires a chat LLM in the crew definition:

```jsonc
{
  "chat_llm": "openai/gpt-4o"
}
```

For classic projects, pass `chat_llm="gpt-4o"` or a provider/model string when constructing `Crew(...)`. Without `chat_llm`, the chat command cannot orchestrate the interactive session.

## Memory and Checkpoint Commands

```bash
crewai reset-memories --memory
crewai reset-memories --knowledge
crewai reset-memories --agent-knowledge
crewai reset-memories --kickoff-outputs
crewai reset-memories --all
crewai memory --storage-path ./.crewai/memory
crewai checkpoint --location ./.checkpoints
crewai checkpoint list ./.checkpoints
crewai checkpoint info ./.checkpoints
crewai checkpoint resume <checkpoint_id>
crewai checkpoint diff <id1> <id2>
crewai checkpoint prune --dry-run --keep 5
```

`reset-memories` deletes selected persisted data. Legacy `--long`, `--short`, and `--entities` flags are hidden/deprecated and map to unified memory. `memory` launches a Textual TUI and may need optional UI dependencies. `checkpoint` without a subcommand launches a TUI; `checkpoint prune` supports `--dry-run`, while `checkpoint resume` and non-dry-run prune can alter execution state or stored checkpoint data.

## Flow Commands

```bash
crewai flow kickoff
crewai flow plot
crewai flow add-crew <crew_name>
```

`crewai run` is the recommended execution command for both crews and flows because it auto-detects `[tool.crewai].type`. Use `flow kickoff`, `flow plot`, and `flow add-crew` when working in older projects or when explicitly managing flow-specific entry points. Route flow graph design to `../flows-and-events/SKILL.md`.

## Hosted, Template, Tool, and Config Commands

- `login`, `logout`, `org`, `enterprise`, `deploy`, `template`, `triggers`, and hosted `tool` commands may contact CrewAI services or require authentication.
- `tool create/install/publish` and `experimental skill create/install/publish/list` are repository/hosted-tooling commands; route implementation details to `../tools-and-mcp/SKILL.md`.
- `traces enable/disable/status` manages trace consent and can interact with user-level settings. `CREWAI_TRACING_ENABLED=true` overrides opt-out behavior for tracing.
- `env view` reports tracing-related environment variables and whether a `.env` file exists. Avoid copying secret values into logs.
- `uv <args...>` wraps `uv` commands after reading the project's `pyproject.toml` and building an environment with tool credentials. It fails when no valid `pyproject.toml` exists.

## Safe CLI Introspection

Use the bundled script for read-only inspection:

```bash
python scripts/inspect_crewai_cli.py --commands
python scripts/inspect_crewai_cli.py --project .
python scripts/inspect_crewai_cli.py --json --project .
```

The script imports `crewai_cli.cli`, reads Click metadata, and checks for project marker files. It does not run crews, deploy, log in, contact hosted services, or execute project custom tools.

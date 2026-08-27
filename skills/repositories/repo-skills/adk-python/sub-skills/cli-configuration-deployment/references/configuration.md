# ADK Configuration and App Discovery

Read this when an ADK app does not load in `adk run`, `adk web`, or `adk api_server`, or when a user wants to choose between Python agent definitions and YAML configuration.

## Loader Contract

ADK CLI commands load an app from a filesystem path. The path should resolve to an app directory that exposes one of these entry points:

- Python app layout: an importable package directory containing `__init__.py` and `agent.py`.
- `__init__.py` imports the `agent` module so package import triggers agent discovery.
- `agent.py` defines `root_agent = Agent(...)`, `root_agent = Workflow(...)`, or `app = App(...)`.
- YAML config layout: `root_agent.yaml` describes an agent tree with `agent_class`, `name`, model/instruction fields, tools, callbacks, and `sub_agents` references.

Use Python definitions when the app needs arbitrary Python logic, custom tools, dynamic construction, or complex imports. Use YAML when the app should be declarative, schema-checkable, and easy to diff.

## Minimal Python App

```text
my_agent/
  __init__.py
  agent.py
```

```python
# my_agent/__init__.py
from . import agent
```

```python
# my_agent/agent.py
from google.adk import Agent

root_agent = Agent(
    name="greeter",
    model="gemini-2.5-flash",
    instruction="Greet the user and answer briefly.",
)
```

Validation steps:

```bash
adk run path/to/my_agent --help
adk web path/to/agents_dir --help
```

`adk web` can point at a parent directory containing multiple app directories, or at a single-agent folder. If the UI does not list an app, validate the package layout before debugging model credentials.

## Minimal YAML App

```yaml
agent_class: LlmAgent
name: greeter
model: gemini-2.5-flash
instruction: Greet the user and answer briefly.
```

YAML config files are backed by Pydantic config models and an installed `AgentConfig.json` schema. Prefer schema validation from the installed package over copying schema files from a source checkout.

Common config fields:

- `agent_class`: usually `LlmAgent`, `SequentialAgent`, `ParallelAgent`, `LoopAgent`, or `BaseAgent` for custom references.
- `name` and `description`: stable identifiers shown by CLI/server tooling.
- `model`, `instruction`, `global_instruction`, `static_instruction`: LLM behavior fields for LLM agents.
- `tools`: function, built-in, MCP, OpenAPI, Google API, or configured tool entries depending on installed extras.
- `sub_agents`: nested agent references or inline agent configs.
- `before_agent_callbacks`, `after_agent_callbacks`, `before_model_callbacks`, `after_model_callbacks`, `before_tool_callbacks`, `after_tool_callbacks`, `on_tool_error_callbacks`: callback references using code config patterns.
- `input_schema`, `output_schema`, `state_schema`: structured schemas; route agent behavior details to `agent-construction`.

## Schema Inspection Workflow

Use the bundled script to inspect command availability and schema metadata without opening the source repository:

```bash
python sub-skills/cli-configuration-deployment/scripts/inspect_adk_cli.py --json
python sub-skills/cli-configuration-deployment/scripts/inspect_adk_cli.py --commands run web eval deploy
```

Expected schema signals:

- The package exposes `google.adk.agents.config_schemas/AgentConfig.json` or equivalent package resource metadata.
- The JSON schema names agent config fields and nested definitions.
- Missing schema resources mean the installed package may be incomplete or not the expected `google-adk` distribution.

## Service Configuration

Server and CLI commands can construct runtime services from URIs:

- Session: `memory://`, `sqlite:///...`, Agent Engine, or SQL database URLs when DB dependencies are installed.
- Artifact: `memory://`, `file:///...`, or `gs://...` when GCS dependencies and credentials are available.
- Memory: `memory://`, Vertex AI RAG, or Agent Engine when cloud dependencies and credentials are available.

App-local service registration can be declarative or Python-based:

- `services.yaml` or `services.yml` registers factories by scheme, type, and class.
- `services.py` can register custom factories programmatically.
- YAML registration loads before Python registration, so Python code can override duplicate schemes.

Route service design and persistence trade-offs to `runtime-services`.

## Graph Visualization and App Objects

The web/API server graph view serializes the loaded root object. Missing or unexpected nodes usually mean one of these issues:

- The loaded module defined a variable other than `root_agent` or `app`.
- `root_agent` is a plain helper object instead of an ADK `Agent`, `Workflow`, or compatible node.
- The app points to a parent directory and another child app shadows the expected name.
- A YAML config references a sub-agent, callback, or tool entry that cannot be imported.
- Optional dependencies for a configured toolset are not installed.

## Safe Configuration Checklist

- Use relative app paths in examples and scripts; avoid absolute machine paths.
- Keep secrets in environment variables or secret services, not YAML committed with the app.
- Use `--help` and schema/resource inspection before running servers or deploy commands.
- For local testing, prefer `--in_memory` storage unless persistence is required.
- For deployment, confirm project, region, target service, credentials, optional extras, and generated-source output directory before running side-effecting commands.

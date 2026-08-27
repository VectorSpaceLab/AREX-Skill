# Magentic-One CLI

The `magentic-one-cli` package installs the `m1` command for running Magentic-One tasks from the terminal. It is a convenience CLI around AgentChat, AutoGen Core model component loading, Docker code execution, and `autogen_ext.teams.magentic_one.MagenticOne`.

## Package Boundary

Repository metadata for `magentic-one-cli` version `0.2.4` requires:

- Python `>=3.10`.
- `autogen-agentchat>=0.4.4,<0.5`.
- `autogen-ext[docker,openai,magentic-one,rich]>=0.4.4,<0.5`.
- `pyyaml>=5.1`.

This conflicts with environments that already use AutoGen 0.7.x libraries such as `autogen-agentchat==0.7.5`, `autogen-core==0.7.5`, or `autogen-ext==0.7.5`. Prefer a separate environment for `m1` rather than downgrading a working 0.7.x application environment.

## Safe Checks

Safe static/help checks:

```bash
python -m pip show magentic-one-cli
python -c "import importlib.metadata as m; print(m.version('magentic-one-cli'))"
m1 --help
m1 --sample-config
```

`m1 --sample-config` prints a default YAML model-client component configuration. It should not start a model call.

## Execution Caution

Do not run task commands such as the following without explicit user approval:

```bash
m1 "research this task"
m1 --no-hil --config config.yaml "modify files"
```

A real `m1` task can:

- Load a model client component from YAML.
- Use provider credentials and network calls.
- Start a Docker code executor in the current working directory.
- Browse, write files, execute generated code, and prompt for human input unless `--no-hil` is set.
- Produce side effects through tools and code execution.

## Config Shape

The default sample config is a YAML object with a `client` component:

```yaml
client:
  provider: autogen_ext.models.openai.OpenAIChatCompletionClient
  config:
    model: gpt-4o
```

Before execution, verify the provider class exists in the installed `autogen_ext`, credentials are supplied out-of-band, Docker is available if code execution is expected, and the working directory is safe for generated files.

## Routing

- For Magentic-One library/team API details, route to `agentchat-workflows`.
- For Docker executor, OpenAI/Azure clients, browser dependencies, and optional extras, route to `extensions-integrations`.
- For dependency resolution and why `m1` conflicts with 0.7.x packages, use `references/compatibility.md`.

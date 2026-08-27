# Classic Workflows

## Status and scope

Classic is an unsupported legacy project. Use it for educational, historical, Forge, or direct benchmark work only. For new production agent workflow work, route to the current Platform sub-skills.

The `classic/` directory is a single Poetry project with three installed packages:

- `autogpt` from `original_autogpt/`.
- `forge` from `forge/`.
- `direct_benchmark` from `direct_benchmark/`.

It requires Python 3.12+ and dependencies are not maintained for long-term security.

## Install and configure

```bash
cd classic
poetry install
cp .env.example .env
```

Configuration is layered:

1. Environment variables from shell or `.env`.
2. Workspace settings in `.autogpt/autogpt.yaml`.
3. Agent-specific settings in `.autogpt/agents/{id}/permissions.yaml`.

Keep API keys local. Do not commit `.env`, workspace state, agent state, benchmark reports containing provider output, or answer files.

## Run Forge or original AutoGPT

```bash
cd classic
poetry run python -m forge
poetry run autogpt --help
poetry run autogpt run --help
poetry run serve --help
```

Forge and server mode default to port 8000 unless configured otherwise. Original AutoGPT/Forge workspaces create `.autogpt/` state under the chosen workspace.

## Workspace and permissions

Classic uses layered allow/deny rules with first-match behavior:

1. Agent deny.
2. Workspace deny.
3. Agent allow.
4. Workspace allow.
5. Interactive approval.

Permission patterns look like `read_file({workspace}/**)`, `write_to_file({workspace}/**)`, `execute_shell(sudo:*)`, or `web_search(*)`. Deny sensitive files and destructive shell commands by default. Inspect `.autogpt/autogpt.yaml` and the relevant agent `permissions.yaml` before allowing shell, file, or web actions.

A typical workspace contains:

```text
.autogpt/
  autogpt.yaml
  ap_server.db
  agents/AutoGPT-<id>/
    state.json
    permissions.yaml
    workspace/
```

## Direct benchmark workflow

Start with list commands, then choose a bounded run:

```bash
cd classic
poetry run direct-benchmark list-challenges
poetry run direct-benchmark list-models
poetry run direct-benchmark list-strategies
poetry run direct-benchmark run --strategies one_shot --tests <challenge> --models openai --attempts 1 --parallel 1 --timeout 300
```

Before any run, decide: challenge subset, model preset, strategy list, attempts, parallelism, timeout, workspace, reports directory, whether to keep answers, and whether saved state should be reset or resumed.

Reports are written under `reports/<timestamp>_<strategy>_<model>/report.json` plus comparison summaries. Use `--json` for CI-style output, `--quiet` for minimal output, and `--keep-answers` only when debugging answer artifacts is intended.

## Safe tests

```bash
cd classic
poetry run pytest forge/tests/test_permissions.py -q
poetry run pytest original_autogpt/tests/unit/test_config.py -q
```

Broader Classic tests may need network/provider mocks or old assumptions. Treat failures in unsupported Classic dependencies separately from Platform health.

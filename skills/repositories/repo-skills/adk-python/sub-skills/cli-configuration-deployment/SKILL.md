---
name: cli-configuration-deployment
description: "Use ADK CLI commands, agent/app discovery, YAML configuration,
  local run/web/API server flows, eval/test commands, deployment commands, and
  safe CLI/config inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ADK CLI, Configuration, and Deployment

Use this sub-skill when a user asks how to run or expose an ADK app with the `adk` console script, why an agent is not discovered by `adk web`, how to structure a Python or YAML agent app, how to validate generated YAML config, or how to reason about `adk deploy` targets and credentials. ADK 2.3.0 provides the `google.adk` import root and the `adk` console command on Python 3.10+.

## Route Common Requests

- **Run locally:** Use [CLI reference](references/cli-reference.md) for `adk run`, `adk web`, `adk api_server`, `adk test`, `adk eval`, `adk eval_set`, and safe `--help` checks.
- **Fix app discovery:** Use [configuration](references/configuration.md) for loader conventions, `root_agent`/`app`, `agent.py`, `__init__.py`, `root_agent.yaml`, `.env`, and service registration.
- **Generate or validate YAML:** Use [configuration](references/configuration.md) for `AgentConfig.json`, `agent_class`, `sub_agents`, `tools`, callbacks, `CodeConfig`, and schema-validation workflow.
- **Deploy safely:** Use [CLI reference](references/cli-reference.md) for `adk deploy cloud_run`, `adk deploy agent_engine`, and `adk deploy gke`; use [troubleshooting](references/troubleshooting.md) for credentials, project/region, optional extras, and generated source caveats.
- **Diagnose failures:** Use [troubleshooting](references/troubleshooting.md) for missing agents in web UI, server/log/CORS issues, YAML schema errors, deployment failures, missing optional dependencies, and model credential problems.
- **Inspect an installation:** Run [inspect_adk_cli.py](scripts/inspect_adk_cli.py) to list available CLI commands and locate installed config schema metadata without starting servers, deployments, network calls, or credential flows.

## Boundaries

- **Included here:** `adk` console commands; agent loader and app discovery; `root_agent`/`app`; YAML config and schema metadata; local `run`, `web`, `api_server`, `test`, `eval`, and `eval_set`; deploy command families; service registry; graph visualization; safe CLI help diagnostics.
- **Route elsewhere:** Eval assertion design and detailed metrics go to `evaluation-debugging`; Python `Agent`/`LlmAgent` object design goes to `agent-construction`; repository maintainer commands, schema regeneration PR workflow, and source test policy go to `repo-development`.

## Safe Defaults

- Prefer `adk --help` and subcommand `--help` for non-mutating CLI checks.
- Do not launch `adk web` or `adk api_server` unless the user explicitly wants a local server.
- Do not run `adk deploy ...` without confirmed project/region/credentials and a clear deployment target.
- Treat base installs as intentionally minimal: optional DB, extensions, MCP, eval, GCP/cloud, and A2A integrations can be absent and should be diagnosed rather than assumed.

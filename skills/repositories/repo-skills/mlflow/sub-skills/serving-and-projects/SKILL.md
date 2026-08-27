---
name: serving-and-projects
description: "Use when working with MLflow CLI commands, tracking servers,
  auth/security, database migrations, MLproject execution, local model
  serving/prediction, deployments, MCP or agent setup, and local development
  server workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serving And Projects

Use this sub-skill when the task is about operating MLflow from the command line or hosting/serving MLflow services. It covers command discovery, `mlflow server`, `mlflow run`, `mlflow deployments`, `mlflow models serve/predict`, auth app setup, database migrations, MCP/agent CLI setup, and development-server caveats.

## Route First

- Use `references/cli-reference.md` to choose CLI groups, inspect help safely, and distinguish read-only probes from side-effectful commands.
- Use `references/server-and-auth.md` for tracking server storage, artifact serving, allowed-host/CORS security, auth app setup, and auth DB migration guidance.
- Use `references/projects-and-deployments.md` for `MLproject` execution, deployment target commands, local model serving/prediction, Docker/SageMaker/cloud cautions, MCP, agent setup, and repo development server workflows.
- Use `references/troubleshooting.md` when diagnosing backend/artifact store mismatches, auth DB problems, host/origin blocks, deployment credentials, env-manager failures, CLI input-file formats, or long-running process behavior.

## Safety Defaults

- Prefer help/version probes before running operational commands: `python scripts/cli_probe.py --commands mlflow "mlflow server" "mlflow models serve"`; use `--python-module /path/to/python` when the `mlflow` console script is not on `PATH`.
- Do not start `mlflow server`, `mlflow models serve`, `mlflow mcp run`, `mlflow gateway start`, or the repo dev server unless the user explicitly asks for a long-running process and provides ports/log handling.
- Do not run deployment create/update/delete, SageMaker, Docker build/run, Kubernetes, Databricks, or cloud commands unless credentials, target, network, and cost/side effects are explicitly approved.
- Do not run auth DB migrations or tracking DB migrations against shared databases without a backup and the exact database URI from the user.
- For model flavor internals, serialization, signatures, and environment inference, route to `models-and-flavors`; for experiment/run semantics and registry objects, route to `tracking-and-registry`; for GenAI tracing/evaluation semantics, route to `genai-observability`.

## Safe Probe Script

`scripts/cli_probe.py` runs only `--help` and `--version` style probes with timeouts. It is suitable for checking an installed MLflow CLI surface before choosing commands, and it intentionally refuses arbitrary command execution.

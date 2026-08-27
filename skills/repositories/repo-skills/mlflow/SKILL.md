---
name: mlflow
description: "Use this skill for MLflow repository work: experiment tracking,
  model registry, MLflow Models and flavors, evaluation, GenAI
  tracing/prompts/datasets/scorers, local serving, deployments, projects,
  CLI/server/auth, and troubleshooting MLflow workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MLflow

MLflow is an open-source platform for the machine learning and GenAI lifecycle. Use this skill when a task asks you to implement, debug, document, or operate MLflow APIs, CLIs, model packaging, tracking stores, observability, evaluation, or serving workflows.

## Start Here

1. Confirm MLflow is importable before relying on API examples:
   `python -c "import mlflow; print(mlflow.__version__)"`.
2. Use `mlflow doctor` and `mlflow --help` for environment and CLI discovery.
3. Pick the nearest sub-skill by user intent; do not load every sub-skill by default.
4. Prefer temporary local SQLite tracking URIs for smoke tests unless the user explicitly provides a remote tracking URI, Databricks workspace, cloud artifact store, or credentials.
5. Treat cloud providers, Databricks-only features, Docker, SageMaker, long-running servers, and external model/provider calls as gated workflows that require explicit user intent and credentials.

## Route by Task

- Use `sub-skills/tracking-and-registry/SKILL.md` for experiments, runs, params, metrics, tags, artifacts, datasets, `MlflowClient`, search filters, tracking/registry URIs, and model registry lifecycle.
- Use `sub-skills/models-and-flavors/SKILL.md` for MLflow Models, `MLmodel`, pyfunc, signatures, input examples, model dependencies, flavor logging/loading, local prediction/serving payloads, and `mlflow.evaluate`.
- Use `sub-skills/genai-observability/SKILL.md` for traces, spans, OpenTelemetry, GenAI evaluation, prompts, datasets, scorers/judges, review queues, assessments, feedback, and provider autologging.
- Use `sub-skills/serving-and-projects/SKILL.md` for `mlflow` CLI groups, `mlflow server`, auth/security, database migrations, `MLproject`, `mlflow run`, deployments, MCP/agent setup, and development-server workflows.

## Common Cross-Routes

- Tracking a model and registering it spans `tracking-and-registry` for runs/registry and `models-and-flavors` for model logging/signatures.
- Serving a logged model spans `models-and-flavors` for model URI/payload/schema and `serving-and-projects` for CLI/server process handling.
- GenAI evaluation spans `genai-observability` for traces/prompts/scorers and `models-and-flavors` when the evaluated object is an MLflow Model or pyfunc.
- A local tracking server spans `serving-and-projects` for server/auth/storage commands and `tracking-and-registry` for client-side URI and experiment/run behavior.

## Repo-Level References

- Read `references/repo-provenance.md` when deciding whether this skill may be stale relative to a checkout.
- Read `references/troubleshooting.md` for cross-cutting install/import, optional dependency, credential, backend, and validation failures.
- Read `references/development-notes.md` for contributor commands, development server caveats, and safe validation strategy.

## Bundled Smoke Scripts

Each sub-skill owns safe helpers for its workflow:

- `sub-skills/tracking-and-registry/scripts/tracking_smoke.py` runs an isolated local tracking smoke test.
- `sub-skills/models-and-flavors/scripts/pyfunc_smoke.py` logs and loads a tiny custom pyfunc model.
- `sub-skills/models-and-flavors/scripts/evaluate_smoke.py` checks tiny callable and precomputed-prediction evaluation.
- `sub-skills/genai-observability/scripts/tracing_smoke.py` records and searches local manual traces.
- `sub-skills/serving-and-projects/scripts/cli_probe.py` runs safe CLI help/version probes only.

Run these scripts with an environment where MLflow is installed. They create temporary local stores by default and should not contact external services unless you modify them.

## Safety Rules

- Do not run long-lived servers, deployment commands, Docker builds, cloud uploads, provider calls, or Databricks operations without explicit user approval and configuration.
- Do not assume optional integrations are installed; check imports and extras before using flavor/provider-specific APIs.
- Keep `MLFLOW_TRACKING_URI`, `MLFLOW_REGISTRY_URI`, provider API keys, Databricks host/token, cloud credentials, and server auth settings explicit in commands or environment setup.
- Use tiny local fixtures for verification before touching user data, model registries, SQL databases, artifact stores, or production endpoints.

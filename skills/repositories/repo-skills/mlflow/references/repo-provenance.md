# Repository Provenance

This file records the source evidence baseline used to generate the `mlflow` skill so future agents can decide whether the skill may be stale.

## Source Snapshot

- Repository project: MLflow
- Package distribution/import: `mlflow`
- Package version inspected: `3.14.1.dev0`
- Current commit: `3f1bdf856aaf45849f42dc9084535a006812f06e`
- Branch: `master`
- Exact tag: none recorded
- Working tree state at generation: dirty because the generated `skills/` artifact tree was untracked
- Remote URL: https://github.com/mlflow/mlflow

## Evidence Paths

Primary source and package metadata:

- `pyproject.toml`
- `pyproject.release.toml`
- `uv.lock`
- `requirements/`
- `mlflow/`

Tracking and registry evidence:

- `mlflow/tracking/`
- `mlflow/client.py`
- `mlflow/store/tracking/`
- `mlflow/store/model_registry/`
- `mlflow/entities/`
- `docs/docs/classic-ml/tracking/`
- `docs/docs/classic-ml/model-registry/`
- `examples/quickstart/mlflow_tracking.py`
- `examples/mlflow-3/register_model.py`
- `tests/tracking/`
- `tests/store/tracking/`

Models, flavors, and evaluation evidence:

- `mlflow/models/`
- `mlflow/pyfunc/`
- `mlflow/sklearn/`
- `mlflow/pytorch/`
- `mlflow/transformers/`
- `mlflow/langchain/`
- `docs/docs/classic-ml/model/`
- `docs/docs/classic-ml/evaluation/`
- `docs/docs/classic-ml/deployment/deploy-model-locally/`
- `examples/pyfunc/`
- `examples/evaluation/`
- `examples/sklearn_logistic_regression/`
- `tests/models/`
- `tests/pyfunc/`

GenAI observability evidence:

- `mlflow/tracing/`
- `mlflow/genai/`
- `mlflow/prompt/`
- Provider integration packages such as `mlflow/openai/`, `mlflow/anthropic/`, `mlflow/bedrock/`, `mlflow/gemini/`, `mlflow/langchain/`, `mlflow/llama_index/`, and `mlflow/dspy/`
- `docs/docs/genai/`
- `docs/docs/prompts/index.mdx`
- `examples/tracing/`
- `tests/tracing/`
- `tests/genai/`
- `tests/prompt/`

Serving, projects, and CLI evidence:

- `mlflow/cli.py`
- `mlflow/server/`
- `mlflow/projects/`
- `mlflow/deployments/`
- `mlflow/gateway/`
- `mlflow/mcp/`
- `mlflow/agent/`
- `mlflow/models/cli.py`
- `docs/docs/self-hosting/`
- `docs/docs/classic-ml/projects/`
- `docs/docs/classic-ml/deployment/`
- `examples/docker/`
- `examples/virtualenv/`
- `examples/deployments/`
- `tests/projects/`
- `tests/server/`
- `tests/deployments/`
- `tests/test_cli.py`
- `dev/run_dev_server.py`

## Refresh Triggers

Refresh this skill when any of these change substantially:

- `mlflow` package version, public function signatures, or CLI command groups.
- Tracking/model-registry store behavior, workspace-aware validations, or URI semantics.
- MLflow Models, pyfunc, signatures, dependency handling, evaluation APIs, or flavor support.
- GenAI tracing, prompts, datasets, scorers, review queues, OpenTelemetry, or provider integrations.
- Server/auth/security defaults, `mlflow run`, `MLproject`, deployment targets, or model serving CLI behavior.
- Documentation/examples/tests that establish public workflows or troubleshooting expectations.

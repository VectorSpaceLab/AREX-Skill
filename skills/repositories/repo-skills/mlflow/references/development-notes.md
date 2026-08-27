# Development Notes

Use this reference for MLflow repository contributor tasks after routing user-facing API, model, GenAI, or serving questions to the nearest sub-skill.

## Environment and Dependency Commands

- `uv sync` installs development dependencies when network and package availability allow it.
- `uv run --frozen pytest ...` is useful when PyPI is unavailable and the existing lock/cache should be reused.
- `uv run pytest <path>` runs focused tests; start with the tests nearest the changed code before broad suites.
- `uv run ruff check . --fix` and `uv run ruff format .` are the standard Python lint/format commands.
- `uv run clint .` runs MLflow's custom lint checks.
- `uv run bash dev/mlflow-typo.sh .` checks spelling/typos.

## Development Server

- For full local backend plus React frontend development, run `uv run dev/run_dev_server.py` and capture logs to a temporary file.
- For a Databricks-backed development server, set `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `MLFLOW_TRACKING_URI=databricks`, and `MLFLOW_REGISTRY_URI=databricks-uc` deliberately before starting the dev server.
- Treat the dev server as a long-running process: pick log handling, ports, cleanup, and backend credentials before launch.

## Testing Strategy

- For tracking store changes, include workspace-aware tests when applicable, especially in `tests/store/tracking/test_sqlalchemy_store_workspace.py` or nearby workspace-specific tests.
- For CLI changes, test `--help` and focused CLI behavior before running broad CLI suites.
- For model/flavor changes, add or run tests near `tests/models/`, `tests/pyfunc/`, or the affected flavor package.
- For GenAI/tracing changes, prefer local/offline trace tests first; run credentialed provider tests only when the user provides the required environment.
- Avoid fixing unrelated failing tests while validating a skill task; record unrelated failures separately.

## Source Areas

- `mlflow/tracking/`, `mlflow/store/`, and `mlflow/entities/` drive tracking and registry behavior.
- `mlflow/models/`, `mlflow/pyfunc/`, and flavor packages drive model packaging, signatures, dependencies, and evaluation.
- `mlflow/tracing/`, `mlflow/genai/`, and provider integration packages drive GenAI observability and evaluation.
- `mlflow/server/`, `mlflow/projects/`, `mlflow/deployments/`, `mlflow/gateway/`, `mlflow/mcp/`, and `mlflow/agent/` drive serving, projects, deployment, and CLI workflows.
- `docs/docs/` and `examples/` are evidence for public workflows; distill or adapt them rather than depending on original paths in generated skills.

## Release and Heavy Workflows

- Release scripts, PyPI publishing helpers, benchmark scripts, Docker/SageMaker/cloud deployment examples, and credentialed provider examples are not safe default verification commands.
- Run heavyweight or side-effectful workflows only when the user explicitly requests them and supplies required credentials, services, hardware, or cleanup instructions.

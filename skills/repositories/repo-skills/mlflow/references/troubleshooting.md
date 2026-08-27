# Cross-Cutting MLflow Troubleshooting

Use this reference before diving into a sub-skill-specific troubleshooting file when the failure could involve installation, optional dependencies, credentials, tracking configuration, or local runtime setup.

## Install and Import Failures

- Verify the active Python environment with `python -c "import mlflow; print(mlflow.__version__)"`.
- If `mlflow` imports but an integration package fails, install the smallest relevant extra or dependency group instead of broad optional dependencies.
- For source checkouts, use the repository's documented development commands and respect dependency cooldown policies; prefer existing lockfiles/caches when offline.
- If `pip check` reports conflicts, fix the environment before debugging MLflow behavior; broken dependencies can surface as misleading runtime errors.

## Tracking and Registry Configuration

- Keep `MLFLOW_TRACKING_URI` and `MLFLOW_REGISTRY_URI` explicit when code crosses local SQLite stores, legacy file stores, SQL-backed stores, HTTP tracking servers, or Databricks.
- Prefer local SQLite URIs for MLflow 3 smoke tests; filesystem tracking backends are in maintenance mode unless `MLFLOW_ALLOW_FILE_STORE=true` is deliberately set, and they are not proof of registry-server behavior.
- For artifact failures, inspect both the run's artifact URI and the server-side `--default-artifact-root` or proxied-artifact settings.
- For Databricks, set host/token/tracking/registry environment variables deliberately and avoid copying credentials into code, logs, or generated files.

## Optional Integrations

- Flavor modules and provider integrations often require packages not installed with the base `mlflow` distribution.
- Cloud artifact stores, Databricks, OpenAI, Anthropic, Bedrock, Gemini, SageMaker, Docker, Kubernetes, and Gateway workflows can require credentials, network access, local daemons, or backend services.
- When optional dependencies are missing, route to the owning sub-skill and add import checks before writing workflow code.
- Prefer provider-free local smoke tests for initial validation; use credentialed examples only after the user opts in.

## CLI and Server Safety

- Run `mlflow --help`, `mlflow <group> --help`, or the bundled CLI probe before operational commands.
- Do not start `mlflow server`, `mlflow models serve`, `mlflow mcp run`, `mlflow gateway start`, Docker builds, database migrations, or deployment mutations without explicit user approval.
- For long-running commands, choose ports, logs, lifecycle cleanup, and timeout/readiness checks before launching.
- For allowed-host or CORS failures, inspect server host/origin configuration rather than disabling security globally.

## Data, Schema, and Payload Validation

- For model prediction or serving failures, compare the input payload to the model signature and input example.
- For evaluation failures, check whether `model`, `data`, `targets`, `predictions`, `model_type`, and evaluator config are mutually consistent.
- For trace/search failures, confirm the trace destination experiment, async flush behavior, and search filter syntax.
- For prompt/dataset/scorer workflows, distinguish local tracking-store capabilities from Databricks-only review apps or scheduled jobs.

## Debugging Order

1. Confirm import/version and `mlflow doctor` output.
2. Confirm active tracking and registry URIs.
3. Reproduce with a tiny local fixture or bundled smoke script.
4. Add optional dependencies or credentials only for the specific failing integration.
5. Move to remote servers, cloud stores, Docker, Databricks, or provider calls after local behavior is understood.

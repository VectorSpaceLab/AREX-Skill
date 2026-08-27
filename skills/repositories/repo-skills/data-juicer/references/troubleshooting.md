# Troubleshooting

## Install and import failures
- Confirm `py-data-juicer` is installed in the environment you are using.
- Add only the extra group required by the workflow instead of installing all extras.
- If import errors mention a missing dependency, route to the matching sub-skill before changing the code.

## Config and dataset failures
- Check whether the task expects `dataset_path` or a structured dataset config.
- Confirm the export path is writable and the export type matches the downstream consumer.
- Simplify the recipe to one dataset and one operator when a config is hard to read.

## CLI and API misuse
- Use the right command for the route: `dj-process`, `dj-analyze`, `dj-install`, or `dj-mcp`.
- For service or MCP calls, confirm the transport, HTTP method, and JSON encoding rules.
- If `skip_return` is set, an empty response body may be intentional.

## Operator and plugin issues
- Use `dj-install` or operator search before assuming an operator is available.
- If a custom operator fails to load, check for name collisions and invalid paths.
- If the operator depends on a heavy optional package, document that dependency next to the workflow.

## Route escalation
- Ray execution, checkpointing, and recovery issues belong in `ray-and-recovery`.
- FastAPI, MCP, and operator-search issues belong in `service-mcp`.
- Dataset syntax, export, and local operator issues belong in `recipes-and-ops`.

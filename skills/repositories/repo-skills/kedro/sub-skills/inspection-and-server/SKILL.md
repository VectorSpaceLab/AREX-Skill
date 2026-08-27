---
name: inspection-and-server
description: "Inspect Kedro projects with read-only snapshots and troubleshoot
  the optional HTTP server API without confusing inspection with execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inspection and Server

Use this sub-skill when a task is about reading Kedro project structure without running the pipeline, using `kedro.inspection.get_project_snapshot`, interpreting snapshot dataclasses, calling the optional HTTP `/snapshot` API, or troubleshooting `kedro server start` dependency/startup failures.

## Route Here

- Produce a read-only summary of project metadata, registered pipelines, nodes, datasets, and parameter keys.
- Use `from kedro.inspection import get_project_snapshot` with `project_path`, `env`, `conf_source`, or precomputed `metadata`.
- Interpret `ProjectSnapshot`, `ProjectMetadataSnapshot`, `PipelineSnapshot`, `NodeSnapshot`, and `DatasetSnapshot` fields.
- Use `GET /health` or `GET /snapshot` from the optional FastAPI server, or diagnose `create_http_server()` and `kedro server start` setup.
- Explain server request/response schemas, strict validation, runner allowlisting, session reuse, and read-only versus run-capable endpoints.

## Route Elsewhere

- Project creation, project detection, global/project CLI command availability, `bootstrap_project()`, `KedroSession.create()`, or telemetry-safe CLI probing: read [project CLI and sessions](../project-cli-and-sessions/SKILL.md).
- Actual pipeline execution through `kedro run`, `KedroSession.run()`, runner choice, slicing, load versions, or only-missing-output behavior: read [runners and execution](../runners-and-execution/SKILL.md).
- Pipeline graph authoring, `node()`, `Pipeline`, namespacing, tags, or pipeline registry design: read [pipelines and nodes](../pipelines-and-nodes/SKILL.md).
- Catalog YAML, credentials, dataset factories, `OmegaConfigLoader`, parameters, or config validation: read [data catalog and config](../data-catalog-and-config/SKILL.md).
- Custom hooks, plugins, custom server routes, middleware, deployment wrappers, or serving customization: read [hooks and extensions](../hooks-and-extensions/SKILL.md).
- Package-wide install/import checks and top-level routing: read the [Kedro root skill](../../SKILL.md).

## Current Facts

- Kedro version target: `1.4.0`; distribution and import name: `kedro`; Python requirement: `>=3.10`.
- Public inspection entry point: `kedro.inspection.get_project_snapshot(project_path=None, env=None, conf_source=None, metadata=None)`.
- Inspection snapshots are read-only: they bootstrap/load project metadata, pipeline definitions, catalog configuration, and parameter keys, but do not load datasets, execute nodes, or write outputs.
- Snapshot dataclasses are `ProjectSnapshot`, `ProjectMetadataSnapshot`, `PipelineSnapshot`, `NodeSnapshot`, and `DatasetSnapshot` from `kedro.inspection.models`.
- Optional server entry point: `from kedro.server import create_http_server`; CLI command: `kedro server start` from inside a Kedro project.
- The `server` optional extra installs `fastapi` and `uvicorn` and depends on Kedro's `pydantic` extra; missing optional packages are expected if only base Kedro is installed.
- Server endpoints include `GET /health`, `GET /snapshot`, and `POST /run`; only `/snapshot` is read-only, while `/run` executes project code.

## Reference Map

- Read [inspection API](references/inspection-api.md) for `get_project_snapshot()` usage, snapshot fields, environment/config-source handling, redaction behavior, and safe read-only summary patterns.
- Read [server API](references/server-api.md) for optional dependency installation, `kedro server start`, `create_http_server()`, endpoint schemas, session reuse, runner allowlisting, and security boundaries.
- Read [troubleshooting](references/troubleshooting.md) when imports fail, optional dependencies are missing, project paths or environments are invalid, snapshots return empty or failed sections, server startup fails, or `/run` is accidentally used for inspection.

## Fast Patterns

- Inspect from Python without running nodes:

  ```python
  from kedro.inspection import get_project_snapshot

  snapshot = get_project_snapshot(project_path=".", env="local")
  print(snapshot.metadata.project_name)
  print([pipeline.name for pipeline in snapshot.pipelines])
  ```

- Reuse project bootstrap metadata for repeated snapshots:

  ```python
  from kedro.framework.startup import bootstrap_project
  from kedro.inspection import get_project_snapshot

  metadata = bootstrap_project(".")
  local_snapshot = get_project_snapshot(metadata=metadata)
  staging_snapshot = get_project_snapshot(metadata=metadata, env="staging")
  ```

- Use a telemetry-safe optional server check only when the server extra is installed and a short-lived local service is acceptable: `KEDRO_DISABLE_TELEMETRY=1 kedro server start --host 127.0.0.1 --port 8000`.
- Prefer `GET /snapshot` for HTTP inspection; avoid `POST /run` unless the user explicitly wants execution and has accepted dataset/code side effects.

## Safety Notes

- Snapshot APIs can import project code and read configuration files, so treat them as read-only introspection rather than a no-import static parser.
- Dataset file paths in `DatasetSnapshot.filepath` may reveal storage layout; URI credentials embedded as `scheme://user:password@host` are redacted, but do not print arbitrary config values or secrets.
- `kedro server start` starts a long-running local service and may execute pipeline code through `/run`; do not expose it publicly without authentication, authorization, request isolation, and network controls.
- Use `KEDRO_DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` for automated CLI probes when telemetry must be disabled.

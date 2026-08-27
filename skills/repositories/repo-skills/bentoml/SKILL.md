---
name: bentoml
description: "Use BentoML to author model-serving Services, build and
  containerize Bentos, run HTTP/gRPC servers and clients, manage models, operate
  the CLI and BentoCloud, and configure observability or production runtime
  behavior. Use when tasks mention BentoML, bentoml service.py, bentofile.yaml,
  Bento build/serve/deploy, BentoCloud, or BentoML model stores."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BentoML

Use this repo skill for BentoML, a Python framework for building, serving, packaging, and deploying AI/model inference APIs. This root skill is a router: read the focused sub-skill that matches the user’s task, then use its bundled references and scripts.

## First Checks

- Install: `pip install -U bentoml`; optional extras include `bentoml[grpc]`, `bentoml[io]`, `bentoml[tracing-otlp]`, `bentoml[monitor-otlp]`, and framework-specific packages needed by the user’s model.
- Import check: `python -c "import bentoml; print(bentoml.__version__)"`.
- CLI check: `bentoml --help` and `bentoml env`.
- Provenance check: read `references/repo-provenance.md` before deciding whether this skill is stale for a current checkout.
- Troubleshooting: read `references/troubleshooting.md` for cross-cutting install/import, CLI, environment, optional dependency, and cloud safety issues.

## Route The Task

| User task | Use this sub-skill | Typical triggers |
| --- | --- | --- |
| Write or debug `service.py`, APIs, tasks, batching, lifecycle hooks, ASGI/Gradio/WebSocket/streaming, IO specs, runtime image hints | `sub-skills/service-authoring/SKILL.md` | `@bentoml.service`, `@bentoml.api`, `@bentoml.task`, `bentoml.importing`, service import target, API schema |
| Build a Bento, author `bentofile.yaml`, include/exclude files, configure build dependencies/images, local Bento store, Docker/containerize | `sub-skills/packaging-and-containerization/SKILL.md` | `bentoml build`, `bentofile.yaml`, `bentoml.build`, `containerize`, `.bentoignore`, build context |
| Run a local server or call endpoints using Python clients, curl/OpenAPI, HTTP/gRPC, streaming, WebSocket, server flags | `sub-skills/serving-and-clients/SKILL.md` | `bentoml serve`, `bentoml.serve`, `SyncHTTPClient`, `AsyncHTTPClient`, port, host, reload, gRPC |
| Save/load/list/import/export models and choose framework helpers or optional dependencies | `sub-skills/model-management/SKILL.md` | `bentoml.models`, model tags, Model Store, sklearn/pytorch/transformers/mlflow/xgboost helpers, missing model |
| Use CLI command families or BentoCloud login/deploy/deployment/secret/api-token/codespace/push/pull workflows | `sub-skills/cli-and-cloud/SKILL.md` | `bentoml deploy`, `bentoml deployment`, `bentoml cloud`, secrets, tokens, context, cluster, BentoCloud |
| Configure logging, metrics, tracing, monitoring, resources, scaling, gateways, testing, config files, production diagnostics | `sub-skills/observability-and-operations/SKILL.md` | metrics missing, tracing, config YAML, GPU resources, workers, autoscaling, gateways, production readiness |

## Common End-To-End Flow

1. Author a Service with `sub-skills/service-authoring/SKILL.md`; validate the import target before serving.
2. Serve locally and call endpoints with `sub-skills/serving-and-clients/SKILL.md`; keep server/client debugging separate from service authoring.
3. Package with `sub-skills/packaging-and-containerization/SKILL.md`; validate `bentofile.yaml` or `bentoml.build(...)` options before expensive builds.
4. Use `sub-skills/model-management/SKILL.md` when the workflow needs saved model tags, framework helpers, or model inclusion in a Bento.
5. Deploy or manage cloud resources with `sub-skills/cli-and-cloud/SKILL.md`; treat credentialed and destructive operations as explicit user-run or user-approved actions.
6. Add telemetry, resources, scaling, config, and production validation with `sub-skills/observability-and-operations/SKILL.md`.

## Safe Bundled Helpers

- `sub-skills/service-authoring/scripts/create_minimal_service.py` generates a starter service file.
- `sub-skills/service-authoring/scripts/validate_service_target.py` imports and inspects a service target without serving it.
- `sub-skills/packaging-and-containerization/scripts/validate_bentofile.py` statically checks a `bentofile.yaml`.
- `sub-skills/serving-and-clients/scripts/serve_command_builder.py` constructs dry-run `bentoml serve` commands.
- `sub-skills/model-management/scripts/check_framework_extra.py` checks optional framework imports.
- `sub-skills/cli-and-cloud/scripts/inspect_bentoml_cli.py` renders safe CLI help without contacting BentoCloud.
- `sub-skills/observability-and-operations/scripts/check_observability_config.py` checks local config shapes without external collectors.

## Side-Effect Boundaries

- Safe by default: import checks, CLI help, static YAML/config validation, command construction, and read-only local store inspection.
- Potentially mutating: `bentoml build`, model save/delete/import/export, local store changes, config writes, and server startup.
- External or credentialed: `bentoml deploy`, `cloud`, `deployment`, `secret`, `api-token`, `push`, `pull`, Docker/container builds, OTLP/exporter endpoints, and cloud scaling changes.
- Expensive or environment-specific: framework model downloads, GPU workloads, large image builds, long-running servers, and integration tests requiring Docker/cloud credentials.

## Version Notes

This skill was generated from BentoML source commit `73c4dbead99be6515fa25fcd91e348ac30f5c22e` on branch `main` and installed package version `0.0.0.post1+g73c4dbead`. If the current checkout, package version, CLI flags, or public SDK signatures differ, run a DisCo refresh before relying on detailed guidance.

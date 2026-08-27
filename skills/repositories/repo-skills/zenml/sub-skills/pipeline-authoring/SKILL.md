---
name: pipeline-authoring
description: "Build, configure, run, schedule, debug, and validate ZenML step
  and pipeline workflows, artifacts, materializers, settings, hooks,
  wait/resume, and local execution patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pipeline Authoring

Use this sub-skill when the task is to write or debug ZenML user code built with `@step`, `@pipeline`, artifacts, materializers, pipeline settings, schedules, caching, retries, hooks, dynamic pipelines, or local execution.

## Natural Triggers

- User asks for a ZenML pipeline, workflow, DAG, step, artifact, materializer, cache, retry, hook, schedule, dynamic pipeline, wait/resume flow, or local run.
- User has Python functions and wants them wrapped in `@step` or composed with `@pipeline`.
- User needs typed multi-output artifacts, custom output materializers, `DockerSettings`, `ResourceSettings`, or YAML/runtime configuration.
- User is debugging cache misses, skipped hooks, invalid materializer output keys, dynamic `.load()`/`.chunk()`/`.map()` behavior, or duplicate child pipeline runs.

## Route First

1. Read [API reference](references/api-reference.md) for decorator signatures, settings keys, output naming, materializer contracts, schedules, hooks, retries, and dynamic APIs.
2. Read [Workflow recipes](references/workflows.md) for concrete static, dynamic, scheduled, materialized, hook-enabled, and isolated-local patterns.
3. Read [Troubleshooting](references/troubleshooting.md) before changing cache/retry/hook behavior, dynamic child pipeline structure, Docker/resource settings, or local ZenML configuration.
4. Run [inspect_pipeline_api.py](scripts/inspect_pipeline_api.py) when the installed ZenML version may differ from this skill, or before relying on a signature.
5. Run [pipeline_smoke.py](scripts/pipeline_smoke.py) with `--check-imports` for a safe import probe, or with `--run` for an opt-in temporary local pipeline smoke.

## Boundary Rules

- Own user-facing pipeline code: decorators, step signatures, dataflow, artifact typing, materializer selection, settings dictionaries, caching, retries, hooks, dynamic execution, wait/resume, schedules, and local smoke checks.
- Route stack component registration, orchestrator implementation, step operator implementation, integration extras, and component flavor code to [stacks-and-integrations](../stacks-and-integrations/SKILL.md).
- Route CLI/client resource listing, schedule lifecycle commands, run audit scripts, and remote-server queries to [cli-and-client](../cli-and-client/SKILL.md).
- Route FastAPI server, store, trigger model, migration, and RBAC internals to [server-and-stores](../server-and-stores/SKILL.md).
- Route deployment services, model/agent deployment examples, production serving, and credential-heavy operational examples to [deployments-and-agents](../deployments-and-agents/SKILL.md).
- Route repository test selection, formatting, linting, docs maintenance, and CI-equivalent checks to [maintenance](../maintenance/SKILL.md).

## Working Pattern

- Start with ordinary typed Python functions, make them importable at module level, then add `@step` and `@pipeline` only where orchestration is needed.
- Prefer `with_options(...)` for per-run or per-invocation changes; reserve `configure(...)` for deliberate in-place global mutation of a step or pipeline object.
- Name multiple outputs with `typing.Annotated` before assigning per-output materializers or downstream references.
- Keep parameters JSON-serializable; pass complex datasets, models, directories, and custom objects as artifacts with explicit type annotations or materializers.
- For dynamic pipelines, use `.load()` only for Python control flow decisions and `.chunk(index=...)`, `.map(...)`, `.product(...)`, `unmapped(...)`, or futures to wire DAG dependencies.
- Treat cache, retry, and hook behavior together: cache hits skip step execution and step hooks, retries fire attempt hooks repeatedly, and hook failures are recorded without aborting the run.

## Safe Validation

- `python scripts/inspect_pipeline_api.py --check-imports` verifies that the expected public APIs import from the active environment.
- `python scripts/inspect_pipeline_api.py --json` prints decorator/settings/materializer signatures for the active ZenML installation.
- `python scripts/pipeline_smoke.py --check-imports` checks importability without creating a ZenML repository or run.
- `python scripts/pipeline_smoke.py --run` creates a temporary isolated ZenML config and local repository, runs a tiny local pipeline, and cleans up by default.

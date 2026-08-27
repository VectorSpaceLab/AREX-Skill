# Evidence Map

## Purpose

This reference records the SkyPilot source areas distilled into the skill and the runtime ownership of each capability. It is for staleness checks and routing; future agents should use the bundled sub-skills instead of reopening original repository files for normal runtime guidance.

## Included Evidence

| Source area | Evidence value | Runtime owner |
| --- | --- | --- |
| `sky/task.py`, `sky/resources.py`, `sky/data/storage.py`, YAML docs, YAML fixtures | Task schema, resources, storage, service/task parsing, parser errors. | `sub-skills/task-yaml/` |
| `sky/client/cli/command.py`, `sky/core.py`, backend code, CLI help, quickstart docs | Cluster launch/exec/status/log/queue/lifecycle behavior and CLI flags. | `sub-skills/cluster-operations/` |
| `sky/jobs/`, managed-job docs/examples/tests, job group examples, jobs SDK signatures | Managed job launch, recovery, logs, cancellation, job groups, and pools. | `sub-skills/managed-jobs/` |
| `sky/serve/`, SkyServe docs/examples/tests, service SDK signatures | Service YAML, readiness probes, replicas, autoscaling, updates, logs, and serving caveats. | `sub-skills/serving/` |
| `sky/clouds/`, `sky/provision/`, `sky/data/`, provider/storage/Kubernetes tests | Credentials, provider selection, Kubernetes/Slurm/SSH, GPU catalog, storage mounts, volumes. | `sub-skills/infrastructure-storage/` |
| `sky/client/sdk.py`, `sky/client/sdk_async.py`, `sky/server/`, API server docs/tests | Python SDK request lifecycle, API server commands, remote compatibility, dashboard/API deployment. | `sub-skills/sdk-api-server/` |
| `AGENTS.md`, `CONTRIBUTING.md`, `format.sh`, `requirements-dev.txt`, `.github/`, `.buildkite/`, `sky/schemas/proto/`, dashboard docs | Source editing, formatting, tests, protobufs, dashboard, API compatibility, CI/PR guidance. | `sub-skills/repo-development/` |
| Existing repo-local guidance under `agent/skills/skypilot/` | Prior agent-facing examples and generated CLI/YAML/SDK references. | Evidence only; distilled into this self-contained skill. |

## Excluded Or Safety-Gated Evidence

- `sky/schemas/generated/` is generated protobuf output; edit `.proto` sources and regenerate instead of hand-editing generated files.
- Smoke tests, cloud launches, SkyServe deployments, managed-job recovery tests, Kubernetes/Slurm/SSH checks, and LLM examples usually require credentials, hardware, network, or paid resources; they are verification candidates only after explicit user approval.
- `examples/` and `llm/` are distilled into recipes and failure-mode guidance; the public skill does not require future agents to run those source files.
- Build/cache/virtualenv/generated output directories are ignored.

## Native Verification Candidate Classes

| Candidate class | Examples | Safety decision |
| --- | --- | --- |
| Help-only CLI | `sky --help`, `sky launch --help`, `sky jobs --help`, `sky serve --help`, `sky api --help`, bundled helper `--help` commands | Safe local checks. |
| Parser-only YAML | Minimal task YAML, service YAML fragments, representative `resources.any_of`/`ordered`/storage snippets | Safe when using bundled validators or import-only parser checks. |
| Unit tests | Selected CLI validation, YAML parser, resources, jobs utils, serve spec/autoscaler, Kubernetes utils, SDK tests | Potentially safe when dependencies are installed; run focused tests only. |
| Cloud/provider checks | `sky check`, provider tests, real `sky launch`, managed jobs, SkyServe, smoke tests | Skip unless user authorizes credentials/cost/resource use. |
| Expensive examples | LLM serving/training, distributed training, benchmarks, load/stress tests | Evidence only by default. |

## Source Script Decisions

- Root `scripts/check_skypilot_env.py` wraps installed-package import and CLI-help checks.
- Root `scripts/inspect_cli_groups.py` wraps safe CLI help inspection.
- Sub-skill scripts are adapted helpers rather than direct copies of cloud-launching repo examples.
- `format.sh`, docs build scripts, and Buildkite helpers are referenced through `repo-development`; the bundled `repo_sanity.py` reports commands and avoids broad mutation by default.

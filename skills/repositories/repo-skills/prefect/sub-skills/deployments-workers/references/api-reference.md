# Deployment Python API Reference

This reference covers public Prefect deployment APIs for Prefect 3.6.24. Use it to choose between long-running served flows, work-pool deployments, and programmatic triggering without importing Prefect internals.

## Choose The Right API

| Goal | Prefer | Requires API? | Requires Worker? |
|---|---|---:|---:|
| Keep one local process polling for scheduled runs | `flow.serve(...)` or `prefect.serve(...)` | Yes for schedules and deployment records | No separate worker; the serve process is the runner |
| Register a deployment that workers execute on dynamic infrastructure | `flow.deploy(...)`, `prefect.deploy(...)`, or `prefect deploy` | Yes | Usually yes for hybrid work pools |
| Build a deployment object without immediately serving | `flow.to_deployment(...)`, `RunnerDeployment.from_flow(...)`, or `RunnerDeployment.from_entrypoint(...)` | Only when applied/served | Depends on how it is served/applied |
| Trigger an existing deployment | `run_deployment(...)` or `prefect deployment run` | Yes | A matching worker or serve process must pick up the run |

Use `flow.serve()` when the current Python process is the infrastructure. Use `flow.deploy()` / `prefect deploy` when a work pool and worker should launch runs elsewhere. Use `run_deployment()` only after the deployment already exists.

## Server And API Prerequisites

- Deployment creation, schedule management, worker polling, and `run_deployment()` all need a reachable Prefect API from the active profile.
- `flow.deploy()` checks that the target work pool exists and warns when no online worker is found for non-push, non-managed pools.
- `flow.serve()` starts a local runner process; schedules need the API, but no separate `prefect worker start` process is used.
- Push and managed work pools may not require a user-run worker; process, Docker, Kubernetes, and most integration-provided worker types do.
- Docker builds, image pushes, and integration workers may require optional packages and external credentials. Keep those operations explicit.

## Live Signature Summary

Verified installed facts for Prefect 3.6.24 include this `RunnerDeployment.from_flow` shape:

```python
RunnerDeployment.from_flow(
    flow, name, interval=None, cron=None, rrule=None, paused=None,
    schedule=None, schedules=None, concurrency_limit=None, parameters=None,
    triggers=None, description=None, tags=None, version=None,
    version_type=None, enforce_parameter_schema=True, work_pool_name=None,
    work_queue_name=None, job_variables=None, entrypoint_type=..., _sla=None,
)
```

Common public API parameters:

| Parameter | Used By | Notes |
|---|---|---|
| `name` | All deployment creation APIs | Deployment name; run targets are usually `<flow-name>/<deployment-name>`. |
| `interval`, `cron`, `rrule` | `serve`, `deploy`, `to_deployment`, `RunnerDeployment` | Quick single schedule inputs. Only one schedule style should be supplied at a time. |
| `schedule`, `schedules` | `serve`, `deploy`, `to_deployment`, `RunnerDeployment` | Use for richer schedule options such as timezone, slug, active state, or per-schedule parameters. |
| `paused` | Deployment creation APIs | Controls whether deployment schedules are active at creation. |
| `parameters` | Deployment creation and run APIs | Defaults at deployment creation; overrides at run time. Values must be JSON-serializable. |
| `tags` | Deployment creation and run APIs | Organizational metadata, not worker routing. |
| `concurrency_limit` / `global_limit` | `deploy` / `serve` | `serve(global_limit=...)` limits all served instances for the deployment; `deploy(concurrency_limit=...)` sets deployment concurrency. |
| `work_pool_name` | `deploy`, `RunnerDeployment` | Required directly or through the default work pool setting for work-pool deployments. |
| `work_queue_name` | `deploy`, `RunnerDeployment`, `run_deployment` | Routes runs within a work pool. It must match the worker's queue filters when used. |
| `job_variables` | `deploy`, `RunnerDeployment`, `run_deployment` | Infrastructure overrides exposed by the work pool base job template. |
| `entrypoint_type` | Deployment creation APIs | Use file paths by default. Module-path entrypoints must be importable in the runtime environment. |
| `_sla` | Deployment creation APIs | Experimental and Cloud-oriented; avoid unless the user explicitly asks for SLA behavior. |

## Safe Python Snippets

### Serve A Flow From A Local Process

```python
from prefect import flow

@flow
def hourly_report(limit: int = 100) -> None:
    print(f"limit={limit}")

if __name__ == "__main__":
    hourly_report.serve(
        name="hourly-report",
        cron="0 * * * *",
        parameters={"limit": 100},
        tags=["reports"],
    )
```

Safety notes:

- `serve()` is long-running. Put it under a supervisor, container, service manager, or terminal multiplexer for production use.
- With `pause_on_shutdown=True`, Prefect pauses schedules when the process exits. If schedules must continue after exit, another serving process must be available before disabling that safeguard.

### Deploy A Flow To A Work Pool

```python
from prefect import flow

@flow
def daily_etl(limit: int = 500) -> None:
    print(f"limit={limit}")

if __name__ == "__main__":
    daily_etl.deploy(
        name="daily-etl-prod",
        work_pool_name="process-pool",
        work_queue_name="default",
        cron="0 6 * * *",
        parameters={"limit": 500},
        job_variables={"env": {"EXECUTION_ENVIRONMENT": "production"}},
    )
```

Safety notes:

- Create the work pool first, then start a compatible worker for non-push work pools.
- Do not assume `tags` route work; routing is controlled by `work_pool_name` and `work_queue_name`.
- Passing an image may build or push Docker artifacts unless `build=False` or `push=False` is explicitly chosen.

### Deploy Remotely Stored Flow Code

```python
from prefect import flow

if __name__ == "__main__":
    flow.from_source(
        source="https://github.com/example/project.git",
        entrypoint="flows.py:daily_etl",
    ).deploy(
        name="daily-etl-prod",
        work_pool_name="process-pool",
        work_queue_name="default",
        job_variables={"env": {"EXECUTION_ENVIRONMENT": "production"}},
    )
```

Use this shape when worker infrastructure cannot see the same local filesystem as the deployment authoring environment.

### Trigger An Existing Deployment

```python
from prefect.deployments import run_deployment

flow_run = run_deployment(
    name="daily-etl/daily-etl-prod",
    parameters={"limit": 50},
    timeout=0,
    tags=["manual"],
)
print(flow_run.id)
```

`timeout=0` creates the flow run and returns immediately. With `timeout=None`, `run_deployment()` waits indefinitely for completion; use that only when a matching worker or serve process is already online.

## Schedule Options

- Quick parameters `interval`, `cron`, and `rrule` create schedules directly. Supply only one style at a time.
- Use `schedules=[...]` for multiple schedules, schedule `timezone`, `active`, `slug`, `replaces`, or schedule-specific `parameters`.
- Cron schedules should use explicit IANA time zones such as `UTC` or `America/New_York` when wall-clock behavior matters.
- Interval schedules can use seconds or schedule objects. Anchor dates make interval alignment deterministic.
- RRule schedules can express complex calendars, but keep them readable and test with a short preview before production use.
- In `prefect.yaml`, prefer `schedules` over the legacy singular `schedule`; see [prefect-yaml.md](prefect-yaml.md).

## Work Pools, Queues, And Job Variables

- `work_pool_name` selects the infrastructure template and worker type.
- `work_queue_name` narrows routing within the work pool. Workers started with queue filters only receive matching queue names.
- `job_variables` override fields exposed by the selected work pool's base job template. Common examples include `image`, `env`, commands, namespaces, and resource limits, depending on worker type.
- Runtime `job_variables` passed to `run_deployment()` override infrastructure for that flow run only.
- Worker-type-specific variables belong to the corresponding integration skill when the question is about Kubernetes, ECS, ACI, Cloud Run, or other providers.

## Command And YAML Helpers

- Use [cli-reference.md](cli-reference.md) for exact CLI flag names.
- Use [prefect-yaml.md](prefect-yaml.md) for deployment manifest structure.
- Use [troubleshooting.md](troubleshooting.md) when a deployment validates but does not execute.
- Use `scripts/deployment_command_builder.py` to print copyable commands without executing them.
- Use `scripts/validate_prefect_yaml.py` to check a deployment manifest without contacting a Prefect API.

---
name: sdk-api-server
description: "Use SkyPilot's Python SDK, async SDK, API server lifecycle
  commands, request IDs, remote login, compatibility checks, and dashboard
  deployment guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SDK API Server

Use this sub-skill when the user wants to drive SkyPilot programmatically or manage the API server: Python SDK equivalents of CLI workflows, async SDK usage, request IDs and `sky.get()`, `sky.stream_and_get()`, `sky api start/stop/status/login/logout/info/logs/cancel`, remote API server compatibility, dashboard access, API versioning, or API server deployment/debugging.

Do not use this sub-skill for detailed task YAML schema authoring, CLI cluster operations, managed jobs semantics, SkyServe service recipes, cloud credential setup, storage/provider troubleshooting, or repository contribution rules. Route those to the sibling sub-skills.

## Read First

- For SDK request patterns, API server commands, async wrappers, and compatibility rules, read [references/sdk-api-reference.md](references/sdk-api-reference.md).
- For request ID, server health, remote login, dashboard, deployment, and version mismatch failures, read [references/troubleshooting.md](references/troubleshooting.md).
- For a safe installed-package probe that does not start an API server, run [scripts/inspect_sdk_surface.py](scripts/inspect_sdk_surface.py).
- For task construction details, route to the `task-yaml` sub-skill.
- For operational CLI workflows after code is converted, route to `cluster-operations`, `managed-jobs`, or `serving`.
- For cloud/Kubernetes credentials, storage, or resource selection failures, route to `infrastructure-storage`.
- For modifying SkyPilot server code, API schemas, protobufs, or dashboard build artifacts, route to `repo-development`.

## Operating Principles

- Treat most synchronous SDK calls as request submitters: they return a `RequestId`, not the final result. Call `sky.get(request_id)` for structured results or `sky.stream_and_get(request_id)` when the user needs live logs and the result.
- Convert CLI task inputs to `sky.Task.from_yaml(...)` or `sky.Task(...)` plus `sky.Resources(...)`; keep YAML schema decisions in `task-yaml` and keep cluster/job/service behavior in the owning operational sub-skill.
- Start a local API server only when the user asks or the SDK call needs one; the inspection helper in this sub-skill intentionally imports and prints signatures only.
- Use `sky.api_login(endpoint=...)` or `sky api login -e ...` before remote operations, and prefer `SKYPILOT_API_SERVER_ENDPOINT` only for temporary endpoint override in one environment.
- Before adding or using newer SDK/API features against a remote server, check `sky.api_info()` and version-gated behavior; old servers may ignore newer fields or raise `APINotSupportedError`.
- For dashboard troubleshooting in a source checkout, rebuild the dashboard before restarting the API server; for Helm/Kubernetes upgrades, preserve deployed values with `--reuse-values` and protect database/credential settings.

## Common SDK Flow

```python
import sky

task = sky.Task.from_yaml('task.yaml')
request_id = sky.launch(task, cluster_name='demo', dryrun=True)
job_id, handle = sky.get(request_id)

status_request_id = sky.status(['demo'])
clusters = sky.get(status_request_id)
```

For async code, import `sky.client.sdk_async`; convenience wrappers such as `status()` and `launch()` await the submitted request and return final results by default:

```python
from sky.client import sdk_async as sky_async

clusters = await sky_async.status(['demo'])
```

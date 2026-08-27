---
name: routers-services
description: "Use ClearML HTTP routers, local FastAPI proxies, endpoint
  telemetry, and long-running service patterns safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ClearML Routers and Services

Use this sub-skill when a user wants to proxy a local HTTP model or web service through ClearML, diagnose `HttpRouter` import/setup failures, design request/response callbacks, register endpoint telemetry, or package a service/monitor/autoscaler pattern.

## Start Here

- For API names, signatures, optional dependency notes, callback contracts, and endpoint-return shapes, read [references/api-reference.md](references/api-reference.md).
- For local proxy plans, telemetry choices, deploy/wait/list/remove sequences, static routes, and service-task patterns, read [references/workflows.md](references/workflows.md).
- For `clearml[router]` failures, FastAPI/uvicorn/httpx import errors, port conflicts, callback bugs, endpoint wait timeouts, and service safety, read [references/troubleshooting.md](references/troubleshooting.md).
- To check whether the optional router dependencies are importable without starting a server, run [scripts/router_extra_check.py](scripts/router_extra_check.py).
- To generate a safe code plan for a local route and callbacks without binding a port or contacting a ClearML server, run [scripts/router_plan.py](scripts/router_plan.py).

## Route Selection

- Use this sub-skill for `Task.get_http_router()`, `HttpRouter.set_local_proxy_parameters()`, `create_local_route()`, `deploy()`, `wait_for_external_endpoint()`, `list_external_endpoints()`, local FastAPI proxy behavior, request/response/error callbacks, and endpoint telemetry.
- Use [../experiment-tracking/SKILL.md](../experiment-tracking/SKILL.md) when the main question is Task creation, logging, parameters, artifacts, models, or credentials outside router/service serving.
- Use [../remote-execution-cli/SKILL.md](../remote-execution-cli/SKILL.md) when the main question is launching a service on a ClearML Agent queue, CLI task creation, queue selection, or `Task.execute_remotely()` behavior.
- Use [../automation-pipelines/SKILL.md](../automation-pipelines/SKILL.md) when the main question is schedulers, automation controllers, pipelines, optimizers, or broader orchestration.

## Safety Defaults

- Treat router deployment as a live operation: `create_local_route()` and `deploy()` can start a uvicorn-backed proxy subprocess, bind a local port, and request an external endpoint from the ClearML server.
- For local dry runs, set `endpoint_telemetry=False`, choose an unused `incoming_port`, and generate a plan with `scripts/router_plan.py` before running live code.
- Do not put API keys, Slack tokens, cloud credentials, or server configuration in generated snippets; use ClearML configuration and secret handling outside the router code.

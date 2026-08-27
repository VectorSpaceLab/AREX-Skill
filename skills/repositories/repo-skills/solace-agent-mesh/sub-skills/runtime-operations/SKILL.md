---
name: runtime-operations
description: "Run SAM applications, inspect docs/tools, submit tasks through Web
  UI or REST gateways, and use the SAM REST client safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# runtime-operations

Use this sub-skill when a user needs to operate an existing Solace Agent Mesh (SAM) project: start configured apps, inspect available runtime docs or built-in tools, submit tasks through the Web UI gateway CLI, diagnose gateway reachability, or integrate through the REST gateway and `sam-rest-client`.

## Route first

- Project creation, `sam init`, `sam add`, GUI scaffolding, generated config layout, model-provider setup, artifact/session defaults: route to `../project-bootstrap/SKILL.md`.
- Workflow YAML schema, node wiring, template resolution, DAG validation, branch/map/loop behavior: route to `../workflow-authoring/SKILL.md`.
- `sam eval`, evaluation configs, suites, local/remote evaluation runs: route to `../evaluation/SKILL.md`.
- Plugin creation, install, catalog, and packaging lifecycle: route to `../plugin-lifecycle/SKILL.md`.

## Safe operating stance

Before running anything, decide whether the user asked for a dry inspection or a live runtime action:

- Dry/help/config checks: CLI `--help`, reading generated project files, `sam tools list --json`, and `scripts/check_gateway.py` are safe by default.
- Live execution: `sam run`, `sam task run`, `sam task send`, `sam-rest-cli`, direct REST `POST /api/v2/tasks`, and browser Web UI use may contact brokers, models, gateways, databases, auth services, and user data. Only do these when the user actually asked to run or submit.
- Gateway inspection must not submit real tasks unless the user explicitly asks for a task invocation. The bundled gateway checker only performs GET probes.

## Reference map

- Running projects and Web UI task CLI: `references/running-and-tasks.md`.
- REST gateway client library and CLI: `references/rest-client.md`.
- Built-in docs and tools command family: `references/tool-and-docs-commands.md`.
- Runtime troubleshooting decision tree: `references/troubleshooting.md`.
- Safe gateway checker: `scripts/check_gateway.py`.

## Quick workflows

1. **Start an existing project**: use `references/running-and-tasks.md#run-an-existing-sam-project`; verify config selection and environment loading before live startup.
2. **Send a task to a running Web UI gateway**: use `references/running-and-tasks.md#send-a-task-to-an-already-running-web-ui-gateway`; check agent discovery and session/file options.
3. **One-shot task run**: use `references/running-and-tasks.md#start-sam-send-one-task-and-stop`; distinguish startup timeout from task timeout.
4. **Inspect a gateway without submitting**: run `python scripts/check_gateway.py --url http://localhost:8000 --expect-agent orchestrator` from any directory.
5. **Use REST programmatic access**: use `references/rest-client.md`; install `sam-rest-client` in a separate environment when dependency pins conflict with the main SAM package.
6. **List built-in tools or serve docs**: use `references/tool-and-docs-commands.md`.

## Provenance note

This sub-skill distills behavior from SAM package docs, CLI command source, task/gateway source, REST client source, and unit/integration tests. It is self-contained for runtime use; future agents should not need the original repository checkout to follow these instructions.

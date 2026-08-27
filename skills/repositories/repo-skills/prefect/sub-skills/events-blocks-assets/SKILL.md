---
name: events-blocks-assets
description: "Use Prefect events, automations, blocks, assets, variables,
  notification blocks, and concurrency limits for operational workflow
  primitives."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Events Blocks Assets

Use this sub-skill when a task is about operational primitives around a Prefect workflow: custom events, event-triggered automations, notification/webhook blocks, saved block documents, custom block classes, assets and materialization metadata, variables, and global or tag-based concurrency limits.

## Start Here

1. Read [references/events-automations.md](references/events-automations.md) for event schemas, `emit_event`, automation JSON/YAML shapes, trigger/action fields, deployment-event matching, and server/Cloud requirements.
2. Read [references/blocks-assets-concurrency.md](references/blocks-assets-concurrency.md) for `Block.save`/`Block.load`, custom blocks, notification blocks, variables, assets, `@materialize`, global concurrency limits, tag limits, and sync/async concurrency contexts.
3. Check exact commands in [references/cli-reference.md](references/cli-reference.md) before composing `prefect events`, `prefect automation`, `prefect block`, `prefect variable`, `prefect global-concurrency-limit`, or `prefect concurrency-limit` commands.
4. Run `python scripts/validate_automation.py --help` to validate automation JSON/YAML locally before `prefect automation create` or `prefect automation update`.
5. Read [references/troubleshooting.md](references/troubleshooting.md) when diagnosing invalid event resources, automation payload validation, block load/save failures, asset materialization surprises, concurrency timeouts, missing optional block dependencies, or Cloud-only features.

## Use For

- `prefect.events.emit_event`, `prefect event emit`, `prefect events stream`, event resources, related resources, payloads, `follows`, event size limits, and event naming grammar.
- Automation payloads using `EventTrigger`, `MetricTrigger`, `CompoundTrigger`, `SequenceTrigger`, and actions such as `run-deployment`, `send-notification`, `call-webhook`, pause/resume, cancel/delete/suspend, and Cloud-only incident actions.
- `Block.save`, `Block.load`, `Block.load_from_ref`, custom `Block` subclasses, block type registration, notification/webhook blocks, secret fields, and block document schema drift.
- `Asset`, `AssetProperties`, `@materialize`, `asset_deps`, `add_asset_metadata`, materialization events, and runtime asset metadata expectations.
- `Variable.set`/`Variable.get`, `prefect variable`, global concurrency limits, tag-based task concurrency limits, and `prefect.concurrency.sync` / `prefect.concurrency.asyncio` contexts.

## Route Elsewhere

- General profile selection, server startup/status, Cloud login, API URL diagnostics, dashboard, and non-events CLI operations: `../cli-server-operations/SKILL.md`.
- Basic `@flow`/`@task` authoring, retries, caching, futures, local tests, and ordinary task-run state handling: `../flow-task-authoring/SKILL.md`.
- Deployment creation, deployment triggers in `prefect.yaml`, work pools, workers, schedules, and deployment run ownership: `../deployments-workers/SKILL.md`.
- Direct `get_client`, `PrefectClient`, settings/profile internals, schema models, and the `prefect-client` package split: `../api-client-settings/SKILL.md`.
- Maintainer-only source changes, repo test selection, generated artifacts, and internal event/block/concurrency implementation changes: `../repo-development/SKILL.md`.

## Safe Validation

- Validate an automation file locally without contacting a Prefect API:

```bash
python scripts/validate_automation.py --file automation.yaml
```

- Print a deployment-event automation template:

```bash
python scripts/validate_automation.py --example deployment-event
```

- Use CLI help checks before running server-mutating commands:

```bash
prefect events emit --help
prefect automation create --help
prefect block type ls --help
prefect global-concurrency-limit create --help
```

## Safety Notes

- `prefect events stream` opens a live event-stream subscription; `--account` is Cloud/account-wide and can include audit logs.
- `prefect events emit`, `prefect automation create`, `prefect block save/create/delete`, `prefect variable set/unset`, and concurrency-limit commands mutate server-side or Cloud workspace state.
- Blocks, variables, automations, event streams, and concurrency limits require a reachable Prefect API or Cloud workspace; route profile/API troubleshooting to `../cli-server-operations/SKILL.md`.
- Webhook, notification, audit log, and incident workflows may require Prefect Cloud features, credentials, and block documents; keep credentials out of examples and logs.

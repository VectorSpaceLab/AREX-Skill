# Events And Automations

Use this reference for custom event emission, event matching, automation payloads, and event-driven operational actions. Prefer validating automation payloads locally with `scripts/validate_automation.py` before calling the Prefect API.

## Custom Events

### Python API

`prefect.events.emit_event` has this shape in Prefect 3.6.24:

```python
emit_event(
    event: str,
    resource: dict[str, str],
    occurred: datetime | None = None,
    related: list[dict[str, str]] | None = None,
    payload: dict[str, Any] | None = None,
    id: UUID | None = None,
    follows: Event | None = None,
    **kwargs,
) -> Event | None
```

Minimal example:

```python
from prefect.events import emit_event

emitted = emit_event(
    event="external.invoice.received",
    resource={
        "prefect.resource.id": "invoice.2026-0001",
        "prefect.resource.name": "Invoice 2026-0001",
    },
    payload={"amount": 125.5, "currency": "USD"},
)
```

Important behavior:

- `resource` must contain non-empty `prefect.resource.id`; add `prefect.resource.name` and domain labels when useful for filtering or UI display.
- `related` entries must contain both `prefect.resource.id` and non-empty `prefect.resource.role`; use roles like `deployment`, `flow-run`, `customer`, `source`, or `tag` to make automation filters precise.
- `payload` must be a JSON-like dictionary; it is for context and templating, not for matching by `match`/`match_related`.
- `occurred` defaults to current UTC time; `id` defaults to a generated UUID.
- `follows` stores a causal relationship only when the followed event occurred close enough in time.
- Very large events raise `EventTooLarge`; shrink payloads or store bulky data elsewhere and send a pointer.
- `emit_event` returns the created `Event` when Prefect’s event worker is active with an emitting client, otherwise it may return `None`.

### CLI Emission

Use `prefect events emit` or alias `prefect event emit`:

```bash
prefect events emit external.invoice.received \
  --resource-id invoice.2026-0001 \
  --resource prefect.resource.name="Invoice 2026-0001" \
  --payload '{"amount": 125.5, "currency": "USD"}'
```

CLI parsing rules:

- `EVENT` is required.
- `--resource-id` is shorthand for `--resource prefect.resource.id=<id>`.
- `--resource` accepts either one `key=value` pair or a JSON object string.
- `--related` accepts a JSON object or JSON array of related-resource objects.
- `--payload` accepts a JSON object string only.
- Emission contacts the configured Prefect API or Cloud workspace.

### Event Stream

`prefect events stream` subscribes to live events:

```bash
prefect events stream --format json
prefect events stream --format text --run-once
prefect events stream --format json --output-file events.ndjson
```

Notes:

- `--format` is `json` or `text`; `json` writes one serialized event per line.
- `--output-file` appends events to a file.
- `--run-once` is intended for one event, but the command still relies on subscriber behavior.
- `--account` streams account-wide events, including audit logs, and is a Prefect Cloud account-level operation.

## Event Resource Patterns

Common resource IDs and event names to match:

| Surface | Event names | Primary resource | Useful related resources |
| --- | --- | --- | --- |
| Flow run state | `prefect.flow-run.Running`, `prefect.flow-run.Completed`, `prefect.flow-run.Failed`, other state names | `prefect.flow-run.<uuid>` | `prefect.deployment.<uuid>` as `deployment`, creator automation/deployment as `creator`, task-run for subflows |
| Task run state | `prefect.task-run.Running`, `prefect.task-run.Completed`, `prefect.task-run.Failed`, other state names | `prefect.task-run.<uuid>` | flow-run and task relationships when available |
| Deployment | `prefect.deployment.created`, `prefect.deployment.updated`, `prefect.deployment.deleted`, `prefect.deployment.ready`, `prefect.deployment.not-ready` | `prefect.deployment.<uuid>` | concurrency-limit when assigned |
| Asset | `prefect.asset.referenced`, `prefect.asset.materialization.succeeded`, `prefect.asset.materialization.failed` | asset key-derived resource | flow-run and task-run when created by a run |
| Concurrency | `prefect.concurrency-limit.created`, `.updated`, `.deleted`, `.acquired`, `.released` | `prefect.concurrency-limit.<uuid>` | sibling limits in a multi-limit acquisition |
| Custom | Any consistent grammar such as `external.invoice.received` | A stable business object id | deployment, flow-run, customer, tenant, source, or file resources |

Use stable IDs rather than display names for resources that automation filters will depend on. Use labels for grouping, for example `team`, `environment`, `tenant`, or `system`.

## Automation Payload Shape

`prefect automation create --from-file` and `--from-json` validate each automation as `AutomationCore` and then submit it to the Prefect API. A file may contain one automation object, a list of objects, or an object with an `automations` list.

Top-level fields:

```yaml
name: invoice-ingest-on-event
description: Run ingestion when an invoice event arrives
enabled: true
tags: [finance, event-driven]
trigger:
  type: event
  posture: Reactive
  expect:
    - external.invoice.received
  match:
    prefect.resource.id: invoice.*
  threshold: 1
  within: 0
actions:
  - type: run-deployment
    source: selected
    deployment_id: 00000000-0000-0000-0000-000000000000
    parameters:
      invoice_id: "{{ event.resource.id }}"
      raw_payload:
        template: "{{ event.payload | tojson }}"
actions_on_trigger: []
actions_on_resolve: []
```

Required fields are `name`, `trigger`, and `actions`. The model ignores unknown extra top-level keys, but avoid relying on that; extra keys can hide typos.

## Event Triggers

`trigger.type: event` supports:

| Field | Meaning | Notes |
| --- | --- | --- |
| `expect` | Event names that count toward the threshold | Empty means any event that passes resource filters; wildcards may end with `*` |
| `after` | Events that must be observed before expected events count | Useful for multi-step reactive flows |
| `match` | Labels on the primary event resource | Example: `prefect.resource.id: prefect.flow-run.*` |
| `match_related` | Labels on related resources | Dict for one condition; list of dicts for multiple required related-resource matches |
| `for_each` | Labels that split evaluation into independent buckets | Use `prefect.resource.id` or `related:<role>:<label>` to avoid cross-run misfires |
| `posture` | `Reactive` or `Proactive` | Reactive responds to presence; proactive responds to absence |
| `threshold` | Count required to fire or expected count for proactive triggers | Use `within` when threshold > 1 |
| `within` | Seconds or duration accepted by Pydantic | Proactive triggers require at least 10 seconds |

Deployment-event matching pattern:

```yaml
trigger:
  type: event
  posture: Reactive
  expect: [prefect.flow-run.Completed]
  match:
    prefect.resource.id: prefect.flow-run.*
  match_related:
    prefect.resource.id: prefect.deployment.00000000-0000-0000-0000-000000000000
    prefect.resource.role: deployment
  for_each:
    - prefect.resource.id
  threshold: 1
  within: 0
actions:
  - type: run-deployment
    source: selected
    deployment_id: 11111111-1111-1111-1111-111111111111
```

Why this shape matters:

- Matching `prefect.flow-run.Completed` with `match.prefect.resource.id: prefect.flow-run.*` catches completed flow-run events.
- Adding `match_related` for `prefect.deployment.<uuid>` limits the trigger to runs from one deployment.
- `for_each: [prefect.resource.id]` prevents events from different flow runs from satisfying one logical evaluation bucket.
- Creating the deployment and wiring trigger ownership lives in `../deployments-workers/SKILL.md`; this sub-skill owns the automation event semantics.

## Metric And Composite Triggers

Metric trigger shape:

```yaml
trigger:
  type: metric
  posture: Metric
  match:
    prefect.resource.id: prefect.flow-run.*
  metric:
    name: duration
    operator: ">"
    threshold: 600
    range: 300
    firing_for: 300
actions:
  - type: send-notification
    block_document_id: 22222222-2222-2222-2222-222222222222
    subject: Long flow run
    body: "A flow run breached the duration threshold."
```

Metric names are `lateness`, `duration`, and `successes`; operators are `<`, `<=`, `>`, and `>=`. `range` and `firing_for` must be at least 300 seconds.

Composite trigger shapes:

```yaml
trigger:
  type: compound
  require: all
  within: 3600
  triggers:
    - type: event
      expect: [external.extract.finished]
      match: {prefect.resource.id: pipeline.customer-a}
    - type: event
      expect: [external.transform.finished]
      match: {prefect.resource.id: pipeline.customer-a}
```

```yaml
trigger:
  type: sequence
  within: 1800
  triggers:
    - type: event
      expect: [external.file.arrived]
    - type: event
      expect: [external.file.validated]
```

`compound.require` may be `any`, `all`, or an integer from 1 through the number of child triggers. `sequence` triggers require child triggers in order.

## Automation Actions

Common action types and required fields:

| Action type | Main fields | Notes |
| --- | --- | --- |
| `do-nothing` | none | Useful for testing trigger definitions |
| `run-deployment` | `source`, `deployment_id` when selected, optional `parameters`, `job_variables`, `schedule_after` | `source: selected` requires `deployment_id`; `source: inferred` forbids it |
| `pause-deployment` / `resume-deployment` | `source`, selected `deployment_id` | Same selected/inferred rule |
| `cancel-flow-run`, `delete-flow-run`, `suspend-flow-run`, `resume-flow-run` | none | Operates on flow run associated with the triggering event |
| `change-flow-run-state` | `state`, optional `name`, `message`, `force` | `state` is a Prefect state type such as `Cancelled`, `Failed`, or `Completed` |
| `pause-work-pool` / `resume-work-pool` | selected/inferred `work_pool_id` rules | Server-side work-pool action |
| `pause-work-queue` / `resume-work-queue` | selected/inferred `work_queue_id` rules | Server-side work-queue action |
| `send-notification` | `block_document_id`, `subject`, `body` | Requires a saved notification block document |
| `call-webhook` | `block_document_id`, optional templated `payload` string | Requires a saved webhook block document |
| `pause-automation` / `resume-automation` | selected/inferred `automation_id` rules | Can manage automations through automations |
| `declare-incident` | none | Prefect Cloud only |

Selected/inferred rule: for deployment, work-pool, work-queue, and automation actions, `source: selected` requires the matching ID field, while `source: inferred` must not include that ID.

## Python Automation API

For code-managed automations:

```python
from prefect.automations import Automation, DoNothing, EventTrigger

automation = Automation(
    name="custom-event-observer",
    trigger=EventTrigger(
        expect={"external.invoice.received"},
        match={"prefect.resource.id": "invoice.*"},
        posture="Reactive",
        threshold=1,
        within=0,
    ),
    actions=[DoNothing()],
)
created = automation.create()
```

`Automation.create()`, `.read()`, `.update()`, and `.delete()` contact the configured Prefect API. Use `AutomationCore.model_validate()` or the bundled validator for offline schema checks only.

## Requirements And Boundaries

- Event emission, event streaming, automation create/update/delete, notification actions, and webhook actions require a configured Prefect API or Cloud workspace.
- Account-wide event streaming, audit logs, and `declare-incident` are Cloud-specific; do not promise them for a local OSS server.
- Deployment trigger shortcuts and `prefect.yaml` trigger wiring belong in `../deployments-workers/SKILL.md`; use this reference for trigger/action semantics and validation.
- Profile, API URL, login, and server startup debugging belongs in `../cli-server-operations/SKILL.md`.

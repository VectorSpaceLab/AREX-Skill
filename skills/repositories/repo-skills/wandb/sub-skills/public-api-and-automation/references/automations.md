# Automations

W&B Automations combine a scope, event, filter, and action. Use them when the user wants server-side alerts or callbacks triggered by run metrics, run state changes, artifact events, or integration-backed notifications.

## Imports

```python
import wandb
from wandb.automations import (
    DoNothing,
    MetricThresholdFilter,
    MetricZScoreFilter,
    OnRunMetric,
    OnRunState,
    RunEvent,
    SendNotification,
    SendWebhook,
)
```

## Scope

Scopes define where an automation watches for events.

```python
api = wandb.Api()
project = api.project("project", entity="entity")
```

- Project scope is the standard scope for run metric and run state automations.
- Artifact collection scopes are used for artifact events such as link, unlink, tag, alias, and create events; detailed artifact semantics belong to the artifact skill area.
- `api.project(name, entity=...)` returns a project handle suitable as `scope=project`.

## Run metric events

```python
project = api.project("project", entity="entity")
event = OnRunMetric(
    scope=project,
    filter=RunEvent.metric("val_loss").mean(5).gt(0.5) & RunEvent.name.contains("prod"),
)
```

Metric filters supported by the public API include:

- Threshold: `RunEvent.metric("loss").gt(1.0)`, `.gte(...)`, `.lt(...)`, `.lte(...)`.
- Aggregation window: `RunEvent.metric("loss").mean(5).gt(1.0)`; related aggregate names include average/mean, min, and max helpers.
- Change: `RunEvent.metric("loss").avg(5).changes_by(frac=0.5)` for relative changes, or construct `MetricChangeFilter` for explicit direction/type/window settings.
- Z-score: `MetricZScoreFilter(name="loss", window=30, threshold=3.0)`.
- Run filters: combine with `RunEvent.name.contains("text")`, equality/range expressions, and bitwise `&`, `|`, `~` operators.

## Run state events

```python
from wandb.automations._filters.run_states import ReportedRunState

event = OnRunState(
    scope=project,
    filter=RunEvent.name.contains("train") & RunEvent.state.eq(ReportedRunState.FAILED),
)
```

Supported state values include `RUNNING`, `FINISHED`, and `FAILED`; `CRASHED` is accepted as an alias for failed when creating/editing automations.

## Actions and integrations

Webhook action:

```python
webhook = next(api.webhook_integrations(entity="entity"))
action = SendWebhook.from_integration(
    webhook,
    payload={"text": "Run metric threshold crossed", "metric": "val_loss"},
)
```

Slack notification action:

```python
slack = next(api.slack_integrations(entity="entity"))
action = SendNotification.from_integration(
    slack,
    title="W&B alert",
    text="A monitored run crossed the configured threshold.",
    level="WARN",
)
```

No-op action:

```python
action = DoNothing()
```

- `SendWebhook` and `SendNotification` require existing integrations; list them with `api.webhook_integrations(entity=...)` and `api.slack_integrations(entity=...)`.
- Do not invent integration IDs. If no integration exists, ask the user to create or choose one.
- Some older servers support only a subset of event/action types. Check `api._supports_automation(event=..., action=...)` before create/update when targeting self-hosted or older deployments.

## Create, fetch, update, delete

```python
new_automation = event >> action
created = api.create_automation(
    new_automation,
    name="val-loss-alert",
    description="Notify when validation loss is high for prod runs.",
    enabled=True,
)
```

Fetch/list:

```python
one = api.automation(name="val-loss-alert", entity="entity")
for automation in api.automations(entity="entity", per_page=50):
    print(automation.name, automation.enabled, automation.id)
```

Update:

```python
automation = api.automation(name="val-loss-alert", entity="entity")
updated = api.update_automation(
    automation,
    enabled=False,
    description="Temporarily disabled during maintenance.",
)
```

Delete only with explicit confirmation:

```python
api.delete_automation(automation)
```

Creation defaults and safeguards:

- `api.create_automation(obj, fetch_existing=False, **kwargs)` raises on name conflicts by default; set `fetch_existing=True` only when reusing the existing automation is acceptable.
- `kwargs` can override `name`, `description`, `enabled`, `scope`, `event`, or `action` from the `NewAutomation` object.
- `api.automation(name=...)` expects exactly one match and raises if zero or multiple automations match.

## Artifact events overview

The automation API exports artifact event classes such as `OnCreateArtifact`, `OnLinkArtifact`, `OnUnlinkArtifact`, `OnAddArtifactAlias`, `OnAddArtifactTag`, `OnRemoveArtifactTag`, `OnAddCollectionTag`, and `OnRemoveCollectionTag`. Use these only after the artifact scope is correctly identified; defer artifact collection/registry semantics to the artifact skill area.

## Correct invalid filter/action combinations

When a user proposes an invalid automation:

- If they use a run metric filter with an artifact event, switch the event to `OnRunMetric` and a project scope, or ask for artifact criteria.
- If they provide a webhook URL instead of an integration object/id, list `api.webhook_integrations(entity=...)` and select or ask for an existing integration.
- If they choose Slack without a Slack integration, ask them to configure/select a Slack integration or use a webhook/no-op action.
- If server support is unknown, check `_supports_automation` and provide a fallback event/action supported by the deployment.

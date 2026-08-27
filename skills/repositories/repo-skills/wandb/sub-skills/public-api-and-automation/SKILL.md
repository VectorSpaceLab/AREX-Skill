---
name: public-api-and-automation
description: "Query, export, and automate W&B resources with wandb.Api,
  including runs, projects, sweeps, reports, files, history exports, and
  automation events/actions/scopes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# W&B Public API and Automation

Use this sub-skill when a task asks an agent to read existing W&B data, export run history or metadata, inspect files/reports/sweeps, or create/update W&B Automations. This is for post-hoc querying and server-side automation, not live experiment logging, artifact lifecycle design, or running sweep agents.

## Route by task

- For `wandb.Api` construction, path shapes, run/project/sweep/report access, filters, and object properties, read [API reference](references/api-reference.md).
- For large or selective run-history exports, sampled vs unsampled history, pagination, file downloads, and the bundled export helper, read [export and pagination](references/export-and-pagination.md).
- For automation scopes, events, filters, integrations, actions, create/update/delete flows, and compatibility checks, read [automations](references/automations.md).
- For auth, host, path, pagination, missing-field, GraphQL/network, and automation mismatch failures, read [troubleshooting](references/troubleshooting.md).

## Core patterns

```python
import wandb

api = wandb.Api(timeout=60)
run = api.run("entity/project/run_id")
print(run.config)
print(dict(run.summary))
for row in run.scan_history(keys=["loss", "accuracy"], page_size=1000):
    ...
```

```python
import wandb
from wandb.automations import OnRunMetric, RunEvent, SendWebhook

api = wandb.Api()
project = api.project("project", entity="entity")
webhook = next(api.webhook_integrations(entity="entity"))
event = OnRunMetric(scope=project, filter=RunEvent.metric("loss").mean(5).gt(1.0))
action = SendWebhook.from_integration(webhook, payload={"metric": "loss"})
automation = api.create_automation(event >> action, name="loss-alert")
```

## Bundled script

Use [scripts/export_run_history.py](scripts/export_run_history.py) for safe CSV or JSONL exports:

```bash
python scripts/export_run_history.py --entity ENTITY --project PROJECT --run RUN_ID --out history.csv --format csv --keys loss accuracy --max-rows 10000
```

Start with `--dry-run` or `--max-rows` before exporting large histories.

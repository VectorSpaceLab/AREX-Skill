---
name: cards-and-observability
description: "Guides Metaflow Cards, current.card customization, card CLI
  workflows, task logs, sidecars, and observability troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cards and Observability

Use this sub-skill when the task involves `@card`, `current.card`, card components, card CLI commands, runtime card refreshes, task stdout/stderr logs, or sidecar/logging behavior.

## Quick Route

- Read [`references/cards.md`](references/cards.md) for card decorators, `current.card`, built-in components, CLI commands, and custom card concepts.
- Read [`references/logging-and-sidecars.md`](references/logging-and-sidecars.md) for logs CLI and sidecar/process behavior.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for invalid card IDs, card type lookup, timeouts, datastore roots, and missing logs.
- Run [`scripts/card_flow.py`](scripts/card_flow.py) to check a safe local flow with a default editable card.

## Minimal Card Pattern

```python
from metaflow import FlowSpec, card, current, step
from metaflow.cards import Markdown

class CardFlow(FlowSpec):
    @card(type="default", id="summary", customize=True)
    @step
    def start(self):
        current.card.append(Markdown("# Run summary"))
        self.next(self.end)

    @step
    def end(self):
        pass
```

After a run, use `python flow.py card list <pathspec>` or `python flow.py logs show <task-pathspec>` depending on the evidence needed.

## Boundaries

- For general Client object traversal, read [`../client-and-data/SKILL.md`](../client-and-data/SKILL.md).
- For flow graph syntax, read [`../flow-authoring/SKILL.md`](../flow-authoring/SKILL.md).
- For cloud/service deployment logs, read [`../deployment-orchestration/SKILL.md`](../deployment-orchestration/SKILL.md).

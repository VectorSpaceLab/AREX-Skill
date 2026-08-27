---
name: client-and-data
description: "Guides Metaflow Client API queries, run/artifact pathspecs,
  namespaces, metadata providers, datastores, logs, tags, S3 datatools, and
  IncludeFile data access."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Client and Data

Use this sub-skill when a task is about inspecting completed Metaflow runs, reading artifacts, switching namespaces or metadata providers, querying tags/logs, using datastores, or accessing S3-style data with Metaflow utilities.

## Quick Route

- Read [`references/client-api.md`](references/client-api.md) for `Flow`, `Run`, `Step`, `Task`, `DataArtifact`, pathspecs, namespaces, and metadata control.
- Read [`references/data-and-datastores.md`](references/data-and-datastores.md) for local/S3/Azure/GS/spin datastores, `S3`, and `IncludeFile` data behavior.
- Read [`references/configuration.md`](references/configuration.md) for public, non-secret `METAFLOW_*` configuration surfaces.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for `MetaflowNotFound`, namespace mismatch, S3 access, logs, and local datastore confusion.
- Run [`scripts/client_query_smoke.py`](scripts/client_query_smoke.py) to create a tiny local run and query an artifact through the Client API.

## Minimal Query Pattern

```python
from metaflow import Run, namespace

namespace(None)  # disable namespace filtering when intentionally inspecting all local runs
run = Run("MyFlow/123")
print(run["end"].task.data.my_artifact)
```

Use `metadata(...)` only when you intentionally switch between local, service, or spin metadata sources.

## Boundaries

- Flow syntax and local run commands belong in [`../flow-authoring/SKILL.md`](../flow-authoring/SKILL.md).
- Cards belong in [`../cards-and-observability/SKILL.md`](../cards-and-observability/SKILL.md).
- Cloud deployment prerequisites belong in [`../deployment-orchestration/SKILL.md`](../deployment-orchestration/SKILL.md).

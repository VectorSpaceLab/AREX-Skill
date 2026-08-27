---
name: graph-workflows
description: "Use R2R graph extraction, graph CRUD, community workflows, and
  graph lifecycle troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Graph Workflows

Use this sub-skill when the user wants to extract entities and relationships, build or reset a graph, manage communities, or inspect graph results.

## What it owns

- document and collection extraction flows
- graph build, pull, reset, and retrieval
- entity, relationship, and community CRUD
- graph lifecycle troubleshooting

## Start here

```python
from r2r import R2RClient

client = R2RClient(base_url="http://localhost:7272")
print(client.graphs.list().results)
```

## Route out when the work becomes another topic

- Preparing or ingesting source documents: `../ingestion-documents/SKILL.md`
- Search or RAG over graph-backed content: `../retrieval-rag/SKILL.md`
- Server/provider setup for orchestration or full mode: `../server-configuration/SKILL.md`

## Bundled assets

- `references/graph-workflows.md`
- `references/api-reference.md`
- `references/troubleshooting.md`
- `scripts/graph_workflow_planner.py`

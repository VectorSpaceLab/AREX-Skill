# Graph Troubleshooting

## Common issues

- **No graph output after extraction**: verify that the source documents were ingested and that the collection you pass to graph operations is the correct one.
- **Empty communities**: check the extraction settings, the graph build step, and whether the collection has enough source material.
- **Pending or delayed build**: if orchestration is enabled, the graph may take time to materialize.
- **Missing provider settings**: graph extraction may need the same provider configuration as retrieval workflows.
- **Graph search confusion**: if the user wants search over graph content, route to retrieval instead of staying in graph CRUD.

## Recovery steps

1. Validate the sequence with `scripts/graph_workflow_planner.py`.
2. Confirm ingestion and collection membership.
3. If the problem is really server orchestration or provider setup, switch to `server-configuration`.

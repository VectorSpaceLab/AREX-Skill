# Migration, Export, and Visualization

Read this when the task is to move memory in/out of Cognee or inspect the graph after it is built.

## Migration sources

Cognee exposes migration sources through `cognee.migration` and routes them through `remember(...)`:

```python
from cognee.migration import Mem0Source, ZepSource, LettaSource, COGXArchiveSource

await cognee.remember(Mem0Source("mem0_export.json"))
await cognee.remember(ZepSource("graphiti_dump.json", mode="hybrid"))
await cognee.remember(COGXArchiveSource("backup_cogx"))
```

Supported public symbols include `GraphSnapshot`, `ExportResult`, `GraphEdge`, `COGX*` record types, `IMPORT_MODES`, and `EXPORT_FORMATS`.

## Export

Public signature:

```python
await cognee.export(
    dataset="main_dataset",
    format="pydantic",
    destination=None,
    link_relations=False,
    include_permissions=False,
)
```

Use cases:
- `format="pydantic"`: get a typed in-memory `GraphSnapshot`.
- `format="graphml"`: write/return a portable graph artifact.
- `format="cogx"`: create a Cognee archive that can be restored later.

If the user wants cloud upload rather than local export, route to [api-cli-services](../../api-cli-services/SKILL.md) for `push` / service guidance.

## Visualization

Public visualization APIs include:

```python
await cognee.visualize_graph(dataset="main_dataset")
await cognee.get_schema_inventory(dataset="main_dataset")
await cognee.visualize_memory_provenance(include_memory=True)
```

Use visualization when the user wants to inspect graph shape, schema inventory, memory provenance, or a smaller neighborhood around a query/seed.

Important knobs:
- `visualize_graph(..., full=False, max_nodes=500)` prevents accidental huge renders.
- `query`, `seed_node_ids`, and `recall_result` can narrow visualization.
- `include_session_events=True` includes session events in graph visualization when available.

## Temporal graphs

Use `temporal_cognify=True` in `cognify` when the user wants event/time extraction instead of ordinary entity-relation extraction. Temporal retrieval is then a search-mode question; route query tuning to [search-retrieval](../../search-retrieval/SKILL.md).

## Safety notes

- Migration and export need access to the selected dataset/backend.
- Visualization can be large; prefer bounded `max_nodes`, seed nodes, or a query scope.
- Do not assume migration source files exist. Ask the user for the path or object they want to migrate.

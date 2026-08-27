# Graph Workflows

## Typical flow

1. Ingest or identify the source documents.
2. Call `documents.extract(...)` or `collections.extract(...)` when you need extraction orchestration from the document or collection side.
3. Call `graphs.build(collection_id, settings=..., run_with_orchestration=True)` when you want the collection graph constructed.
4. Use `graphs.pull(collection_id)` if you need to refresh graph state in the server.
5. Inspect `graphs.list_entities()`, `graphs.list_relationships()`, and `graphs.list_communities()` to review the output.
6. Use the CRUD helpers only after you know what should exist.

## Useful calls

- `documents.extract(...)`
- `collections.extract(...)`
- `graphs.build(...)`
- `graphs.pull(...)`
- `graphs.reset(...)`
- `graphs.retrieve(...)`
- `graphs.create_entity(...)`, `graphs.create_relationship(...)`, `graphs.create_community(...)`
- `graphs.update_community(...)`, `graphs.delete_community(...)`

## Settings

Graph settings are passed as dictionaries or graph settings objects. Common names in the repository evidence include graph extraction, entity description, and communities-related configuration blocks.

## Example

```python
client.graphs.build(
    collection_id="collection-id",
    settings={"graph_extraction": {"enabled": True}},
    run_with_orchestration=True,
)
```

## Boundary note

If the user actually wants to search against the graph or use graph-backed retrieval, switch to `../retrieval-rag/SKILL.md`.

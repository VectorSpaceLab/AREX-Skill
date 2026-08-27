# Graph API Reference

## Key method signatures

- `documents.extract(id, settings=None, run_with_orchestration=True)`
- `collections.extract(id, settings=None, run_with_orchestration=True)`
- `graphs.build(collection_id, settings=None, run_with_orchestration=True)`
- `graphs.pull(collection_id)`
- `graphs.reset(collection_id)`
- `graphs.retrieve(collection_id)`

## Graph inspection and CRUD

- `graphs.list(collection_ids=None, offset=0, limit=100)`
- `graphs.list_entities(collection_id, offset=0, limit=100)`
- `graphs.list_relationships(collection_id, offset=0, limit=100)`
- `graphs.list_communities(collection_id, offset=0, limit=100)`
- `graphs.get_entity(collection_id, entity_id)`
- `graphs.get_relationship(collection_id, relationship_id)`
- `graphs.get_community(collection_id, community_id)`
- `graphs.create_entity(collection_id, name, description, category=None, metadata=None)`
- `graphs.create_relationship(collection_id, subject, subject_id, predicate, object, object_id, description, weight=None, metadata=None)`
- `graphs.create_community(collection_id, name, summary, findings=None, rating=None, rating_explanation=None)`
- `graphs.update_community(collection_id, community_id, name=None, summary=None, findings=None, rating=None, rating_explanation=None, level=None, attributes=None)`
- `graphs.delete_community(collection_id, community_id)`

## Practical guidance

- Use extraction for generating graph data, build/pull for collection graph orchestration, and CRUD only for explicit edits.
- Keep collection IDs and entity IDs distinct in examples.

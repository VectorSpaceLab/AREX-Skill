# Graph-build data formats

## Supported upload files

MiroFish accepts:

- `.pdf`: text extracted with PyMuPDF.
- `.md` / `.markdown`: read as text with encoding fallback.
- `.txt`: read as text with encoding fallback.

Unsupported extensions are rejected before parsing. The backend upload limit is 50 MB. Markdown and text files first try UTF-8, then charset detection, then replacement decoding.

## Text splitting

Default graph ingestion chunks:

```text
chunk_size = 500
chunk_overlap = 50
```

The splitter preserves sentence boundaries when practical and skips empty chunks. Long ontology prompts are sampled across the document so beginning, middle, and ending context are represented.

## Ontology schema

Top-level shape:

```json
{
  "entity_types": [
    {
      "name": "Person",
      "description": "Any natural person not covered by a more specific type.",
      "attributes": [
        {"name": "role", "type": "text", "description": "Current role."}
      ],
      "examples": ["Alice"]
    }
  ],
  "edge_types": [
    {
      "name": "WORKS_FOR",
      "description": "A person works for an organization.",
      "source_targets": [{"source": "Person", "target": "Organization"}],
      "attributes": []
    }
  ],
  "analysis_summary": "short explanation"
}
```

Naming rules:

- Entity type names: English PascalCase.
- Relation type names: English UPPER_SNAKE_CASE.
- Attribute names: English snake_case.
- Entity types should be actors that can speak or interact in a social simulation, not abstract topics.
- Relation types should capture interaction or real-world influence between actor types.

Service limits and reserved names:

- Keep entity and edge type lists within the service's 10-type limit.
- Keep attribute and source-target lists bounded to 10 entries each.
- Do not use reserved attribute names: `uuid`, `name`, `group_id`, `graph_id`, `name_embedding`, `summary`, `created_at`.
- If no usable attributes are supplied, the service can fall back to a generic `details` text attribute.

## Project record fields

A project record contains:

- `project_id`: `proj_...` identifier.
- `name`: display name.
- `status`: one of `created`, `ontology_generated`, `graph_building`, `graph_completed`, `failed`.
- `files`: uploaded file metadata.
- `total_text_length`: extracted text character count.
- `ontology`: generated ontology JSON.
- `analysis_summary`: LLM summary for the ontology.
- `graph_id`, `graph_build_task_id`, `zep_batch_id`, `zep_batch_operation_id`: graph build state.
- `simulation_requirement`: original prediction requirement.
- `chunk_size`, `chunk_overlap`: ingestion settings.
- `error`: latest failure message when status is `failed`.

## Task fields

Task records include:

- `task_id`
- `task_type` such as `graph_build`
- `status`: `pending`, `processing`, `completed`, `failed`
- `progress`: 0-100 integer
- `message`: localized user-facing progress text
- `result`: terminal success payload
- `error`: terminal failure text
- `metadata` and `progress_detail`

## Graph data fields

Graph visualization/inspection uses nodes and edges. Nodes generally include:

```json
{
  "uuid": "...",
  "name": "Alice",
  "labels": ["Entity", "Person"],
  "summary": "...",
  "attributes": {"role": "student"}
}
```

Edges generally include:

```json
{
  "uuid": "...",
  "name": "WORKS_FOR",
  "fact": "Alice works for Acme.",
  "source_node_uuid": "...",
  "target_node_uuid": "...",
  "attributes": {}
}
```

Temporal fields such as `created_at`, `valid_at`, `invalid_at`, and `expired_at` can appear when Zep provides them.

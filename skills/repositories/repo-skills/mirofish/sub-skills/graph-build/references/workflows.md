# Graph-build workflows

## 1. Document upload and ontology generation

MiroFish begins with one or more seed documents plus a simulation requirement. The web UI accepts drag/drop uploads and sends a multipart request to ontology generation. Programmatic callers should provide:

- `files`: one or more `.pdf`, `.md`, `.markdown`, or `.txt` files.
- `simulation_requirement`: the natural-language prediction or social-simulation question.
- `project_name`: optional display name.
- `chunk_size` and `chunk_overlap`: optional text-splitting controls; defaults are 500 and 50 characters.

The backend extracts text, stores a project record, and asks the LLM for a social-simulation ontology. The ontology generator is designed for social-media simulation: entity types should represent actors that can speak or interact, not abstract topics.

Expected ontology output:

```json
{
  "entity_types": [
    {
      "name": "Student",
      "description": "A student actor in the event.",
      "attributes": [{"name": "role", "type": "text", "description": "Role in the event."}],
      "examples": ["Alice"]
    }
  ],
  "edge_types": [
    {
      "name": "COMMENTS_ON",
      "description": "An actor comments on another actor or issue.",
      "source_targets": [{"source": "Student", "target": "Organization"}],
      "attributes": []
    }
  ],
  "analysis_summary": "..."
}
```

The generator normalizes names and attribute lists, rejects reserved attribute names, and limits overly large type/attribute lists. Use the bundled validator before manually sending a custom ontology.

## 2. Build the Zep graph

After ontology generation, build the graph for a project. The graph build flow:

1. Re-read the project and confirm it has `status: ontology_generated` or a recoverable failed state.
2. Check that no active build task is already pending or processing for the project.
3. Split extracted document text into chunks.
4. Create or reconcile a client-generated Zep graph id.
5. Set ontology.
6. Submit text chunks to Zep Batch API.
7. Wait for batch processing and fetch graph node/edge counts.
8. Mark the task completed and update the project with `graph_id`, `zep_batch_id`, and `zep_batch_operation_id`.

Builds are asynchronous. Always store the returned `task_id` and poll task status rather than assuming the graph is immediately ready.

## 3. Poll graph progress

Use the graph task endpoint until the task is terminal:

- `pending` / `processing`: continue polling; progress and message fields are user-facing.
- `completed`: read `result.graph_id` and refresh the project record.
- `failed`: inspect `error`. A stale after-restart build can be recoverable, but a hard Zep failure usually requires reset or retry.

Avoid launching simulation setup until both the task and project say the graph is complete.

## 4. Inspect graph data

A successful graph can be inspected as node/edge payloads. Expect each node to include identifiers, display name, labels, summary, attributes, and optional temporal metadata. Expect each edge to include identifiers, relation/fact text, source and target uuids, attributes, and temporal fields when available.

Use graph data to:

- Confirm the ontology produced meaningful entity labels.
- Estimate whether enough entities exist for simulation profiles.
- Diagnose missing or generic `Entity`-only nodes before simulation setup.

## 5. Reset or delete safely

Reset/delete operations first check active graph consumers. A graph is in use if any active build, running/stopping simulation, graph-memory updater, or report reader still references it. A safe reset:

1. Verify no build task is pending/processing.
2. Verify no simulation or report is actively using the graph.
3. Delete the Cloud graph if present.
4. Clear the local graph reference in the project.
5. Move the project back to `ontology_generated` when ontology still exists, otherwise `created`.

If a graph-in-use error appears, do not force local metadata changes. Stop or close the consuming simulation/report first, then retry reset.

## Hand-off to simulation setup

Proceed to `simulation-setup` only when:

- The project has `status: graph_completed`.
- The project has a non-empty `graph_id`.
- Graph data inspection can read node/edge counts.
- Entity labels are not all generic `Entity`/`Node`.

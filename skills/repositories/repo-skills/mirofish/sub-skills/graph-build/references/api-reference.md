# Graph-build API reference

All graph endpoints are under `/api/graph`. JSON responses use the common shape:

```json
{"success": true, "data": {}, "message": "optional"}
```

On errors, `success` is false and `error` contains a user-facing message. Axios callers in the frontend surface backend error strings from non-2xx responses.

## Project endpoints

| Endpoint | Method | Purpose | Important fields |
| --- | --- | --- | --- |
| `/project/list` | GET | list recent projects | query `limit`; returns `data[]` and `count` |
| `/project/<project_id>` | GET | fetch one project | project status, files, ontology, graph ids, error |
| `/project/<project_id>` | DELETE | delete project and its Cloud graph if safe | fails with 409 if graph has active consumers |
| `/project/<project_id>/reset` | POST | remove current Cloud graph and move project back before graph build | fails with 409 if build/simulation/report uses the graph |

Project status values:

- `created`: files exist, ontology not generated yet.
- `ontology_generated`: ontology exists, graph can be built.
- `graph_building`: build task is in progress.
- `graph_completed`: graph is ready for simulation setup.
- `failed`: latest build/setup action failed; check `error`.

## Ontology generation

`POST /ontology/generate` accepts multipart form data.

Common fields:

- `files`: one or more seed documents.
- `simulation_requirement`: required natural-language requirement.
- `project_name`: optional name.
- `chunk_size`, `chunk_overlap`: optional text split controls.

Returns a project record including `project_id`, uploaded file metadata, extracted text length, `ontology`, `analysis_summary`, and `status: ontology_generated` when successful.

The ontology is a JSON object with `entity_types`, `edge_types`, and `analysis_summary`. Use `scripts/validate_ontology_payload.py` before sending or editing custom ontologies.

## Graph build and task polling

| Endpoint | Method | Purpose | Important request/response fields |
| --- | --- | --- | --- |
| `/build` | POST | start graph build for an ontology-generated project | body `project_id`, optional `graph_name`, `chunk_size`, `chunk_overlap`, `force`; returns `task_id`, `graph_id`, `reused` when an active task is reused |
| `/task/<task_id>` | GET | get one build task | `status`, `progress`, `message`, `result`, `error`, `progress_detail` |
| `/tasks` | GET | list tasks | optional `task_type` |

Build-task status values are `pending`, `processing`, `completed`, and `failed`. A completed graph-build task result usually includes `graph_id`, `graph_info`, and `chunks_processed`.

If `/build` finds an already pending/processing task for the same project, it returns the existing task instead of starting a duplicate. If a stale build is detected after a restart, the endpoint can return a recoverable error; reset or retry based on the returned error fields.

## Graph inspection and deletion

| Endpoint | Method | Purpose | Important fields |
| --- | --- | --- | --- |
| `/data/<graph_id>` | GET | fetch graph nodes/edges for visualization and downstream checks | returns node and edge collections plus counts |
| `/delete/<graph_id>` | DELETE | delete a Cloud graph directly when no project/simulation/report is using it | use carefully; project reset is safer when a project owns the graph |

Graph inspection may hit live Zep Cloud. Authentication, permission, transport, and pagination errors should be treated as real errors, not empty graphs.

## Common caller sequence

```text
POST /api/graph/ontology/generate  -> project_id, ontology
POST /api/graph/build              -> task_id, graph_id
GET  /api/graph/task/<task_id>     -> wait for completed
GET  /api/graph/project/<id>       -> confirm graph_completed
GET  /api/graph/data/<graph_id>    -> inspect graph before simulation setup
```

## Safe reset sequence

```text
GET  /api/graph/project/<id>
POST /api/graph/project/<id>/reset
GET  /api/graph/project/<id>
```

Do not reset/delete when a simulation runner, memory updater, or report reader is active. The backend protects this with per-graph lifecycle locks and active-consumer checks.

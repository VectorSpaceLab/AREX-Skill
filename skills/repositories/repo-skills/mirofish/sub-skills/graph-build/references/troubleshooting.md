# Graph-build troubleshooting

Use this reference for Step 1 failures only. For backend installation, dependency setup, and secret provisioning, consult the root setup/troubleshooting references. For simulation/report consumers that are blocking a graph lifecycle operation, route to the relevant downstream sub-skill.

## Quick triage checklist

1. Load `GET /api/graph/project/{project_id}` if a project ID exists.
2. Note `status`, `error`, `graph_id`, `graph_build_task_id`, `zep_batch_id`, and `zep_batch_operation_id`.
3. If a graph-build task ID exists, call `GET /api/graph/task/{task_id}`. A `404` after restart is normal; then use the build recovery path.
4. If ontology JSON exists, run the bundled validator before rebuilding.
5. If reset/delete returns `409`, identify whether the blocker is an active build, simulation, graph-memory updater, or report reader.
6. Do not manually clear local graph IDs before Cloud deletion. MiroFish intentionally deletes the Cloud graph first, then clears local references.

## Upload and parsing failures

| Symptom or error | Likely cause | Recovery |
|---|---|---|
| `simulation_requirement` required / request rejected with `400` | Missing or empty requirement. | Resubmit multipart form with non-empty `simulation_requirement`. |
| file upload required / no pending files | Home page has no pending upload or form omitted `files`. | Return to Home, choose files, and restart, or send multipart `files` fields with curl/client code. |
| no document processed | Files were absent, had unsupported extensions, or failed parsing. | Use `.pdf`, `.md`, `.markdown`, or `.txt`; remember the UI only selects `.pdf`, `.md`, `.txt`. Convert Office/CSV/HTML to text or Markdown first. |
| unsupported file format | Backend rejected extension. | Rename only if content genuinely matches a supported text/PDF format; otherwise convert. |
| garbled Markdown/TXT text | Encoding fallback used replacement characters or guessed poorly. | Convert source documents to UTF-8 and retry. For critical non-UTF-8 documents, inspect extracted text by project before trusting the ontology. |
| PDF text is missing | PDF has scanned images or PyMuPDF cannot extract meaningful text. | OCR externally, save as `.txt`/`.md`, then rerun ontology generation. |
| request too large | Upload exceeds 50 MB request limit. | Split or summarize seed docs before upload; prefer smaller, representative source files. |

## Ontology and LLM failures

| Symptom or error | Meaning | Recovery |
|---|---|---|
| `LLM_API_KEY` missing or provider auth failure | Root LLM configuration is absent or invalid. | Fix root setup values for `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL_NAME`; retry ontology generation. |
| `LLM provider request failed (HTTP NNN)` | Provider returned an HTTP status. MiroFish hides provider body content and may include a sanitized request ID. | Check key, base URL, model name, quota/rate limits, and provider status. For 429/5xx, wait or use a smaller input. |
| `LLM JSON output was truncated at the token limit` | Model stopped before a complete JSON object. | Reduce seed text volume, provide concise additional context, or use a model with larger output capacity. The ontology generator already retries once without a completion cap. |
| `LLM returned invalid JSON`, `empty JSON content`, `no choices`, `multiple JSON values`, or top-level array error | OpenAI-compatible provider did not return exactly one usable JSON object. | Retry with a more reliable JSON-capable model/provider. MiroFish accepts one complete JSON object followed by plain text, but rejects multiple JSON documents and arrays. |
| Ontology generation response is `502` and includes `data.project_id` | A project was created before the ontology failure and then marked `failed`. | Use `GET /api/graph/project/{project_id}` to inspect the public `error`; then recreate the project with corrected inputs or reset/retry if appropriate. |
| entity/edge names look strange | The generator normalizes entity names to PascalCase and edge names to uppercase snake case. | Prefer inspecting the stored project ontology, not raw provider output. Hand-edited payloads should pass the bundled validator. |
| reserved ontology attributes such as `name`, `uuid`, `graph_id`, or `summary` | These collide with Zep/MiroFish node fields. The graph builder prefixes reserved attributes defensively, but that changes the schema name. | Rename attributes before build: use `full_name`, `org_name`, `role`, `position`, `location`, `stance`, `description`, or `source_url`. |
| missing edge types in Zep | Edge definitions without valid `source_targets` are not installed. Invalid endpoints may be dropped during generation. | Ensure every edge has at least one `{source, target}` pair that references a defined entity type or `Entity`; run the validator. |

Validator command examples:

```bash
python sub-skills/graph-build/scripts/validate_ontology_payload.py ontology.json
cat project-response.json | python sub-skills/graph-build/scripts/validate_ontology_payload.py -
python sub-skills/graph-build/scripts/validate_ontology_payload.py --self-test
```

## Build request failures

| Symptom or error | Meaning | Recovery |
|---|---|---|
| `ZEP_API_KEY` missing / config error | Zep Cloud key is absent. | Fix root setup and restart backend if needed. |
| `ZEP_API_URL is unsupported` | Environment tries to override the SDK endpoint. MiroFish is Cloud-only and rejects self-hosted override. | Unset `ZEP_API_URL`; keep `ZEP_API_KEY` for Zep Cloud. |
| `project_id` required | JSON body omitted `project_id`. | Send `{"project_id":"proj_..."}`. |
| project not found | Local project does not exist or was deleted. | Use `/project/list` to find valid projects or recreate from upload. |
| ontology not generated / ontology not found | Project is still `created` or lacks ontology. | Generate ontology first; reset/recreate if the project is inconsistent. |
| extracted text not found | Project metadata exists but extracted text file is missing. | Recreate the project from source documents; do not build from an incomplete project. |
| `force must be a JSON boolean` | Sent `force` as a string such as `"false"`. | Send a real JSON boolean: `false` or `true`. |
| `chunk_size must be a positive integer` | Invalid chunk size. | Use the default `500` unless you have a reason to tune. |
| `chunk_overlap must satisfy 0 <= chunk_overlap < chunk_size` | Overlap is negative, not an integer, or greater/equal to chunk size. | Use the default `50`, or set a smaller non-negative overlap. |
| `At least one text chunk is required` | Extracted text is empty after preprocessing. | Recreate the project with non-empty text/OCR output. |
| `A Zep batch cannot contain more than 50,000 items` | Chunking created too many pieces. | Increase `chunk_size` or reduce source size. |
| `Zep batch item exceeds 10,000 characters` | A chunk is too large for the Batch API. | Lower `chunk_size`; keep overlap below chunk size. |

## Zep Cloud ingestion failures

| Symptom or error | Meaning | Recovery |
|---|---|---|
| `Zep batch ... did not finish within 600s` | Batch ingestion remained non-terminal for the ingestion timeout. | Check Zep Cloud status/quota and project `zep_batch_id`; retry later or reset/rebuild if the batch will not complete. |
| `ended as partial|failed|invalid|canceled` | Zep Batch API reached a non-success terminal state. | Inspect first failed item/error if available; fix ontology/chunk data or Zep account limits; reset/rebuild. |
| `batch creation is unconfirmed` | The create response was lost and no matching operation metadata was found. | Avoid manual replay of non-idempotent calls. Let MiroFish recovery inspect the persisted operation; reset/rebuild if needed. |
| `Multiple Zep batches match operation` | Ambiguous persisted operation identity. | Do not guess. Inspect account batches manually or delete/reset the affected project graph after ensuring no consumers are active. |
| `item submission is unconfirmed` or acknowledged fewer items | A batch add response was ambiguous and reconciliation did not prove all items exist. | Treat the build as failed; reset/rebuild rather than replaying raw batch adds. |
| `source_uuid` and `episode_uuid` mismatch / incomplete item | Zep returned inconsistent item state. | Retry after Zep stabilizes; if persistent, reset/rebuild and consider reducing batch size/source complexity. |
| graph data endpoint returns auth/not found/error | `graph_id` is wrong, key cannot read it, graph was deleted, or Zep read failed. | Reload project to confirm `graph_id`, check `ZEP_API_KEY`, and avoid using stale graph IDs after reset/delete. |

Zep reads are retried only for safe read failures: transport errors, HTTP 408, HTTP 429, and 5xx. Mutating graph/batch calls are not blindly retried because replay can create duplicate Cloud state.

## Project lifecycle and `GraphInUseError`

`GraphInUseError` means the graph is actively consumed and reset/delete/rebuild-with-force must not proceed. The error text can include:

- `report:<report_id>`: a report reader lease is active.
- `sim_...` or another simulation ID: a simulation runner, graph-memory updater, or finalization path is active.

Recovery:

1. Wait for report generation, simulation execution, or graph-memory ingestion to finish.
2. If a simulation is paused/running/stopping, use the simulation sub-skill to stop or finish it cleanly.
3. Retry reset/delete only after active consumers disappear.
4. Do not manually remove graph references to bypass the guard; that can orphan a Cloud graph or race with simulation memory writes.

Active graph builds also block reset/delete. If a project is `graph_building`, poll the task first. If `/task/{task_id}` returns `404`, call `/build` for recovery:

- Reuses a still-active in-memory task when present.
- Resumes a persisted queued/processing/succeeded Zep batch when the project has `graph_id`, `zep_batch_id`, and `zep_batch_operation_id`.
- Returns `409` with `recoverable: true` and marks project `failed` when no automatic resume is possible.

## Reset/rebuild troubleshooting

| Goal | Recommended path | Notes |
|---|---|---|
| Retry a failed ontology generation | Recreate from upload. | Failed ontology projects may lack usable ontology or extracted text. |
| Retry a failed graph build with ontology intact | Call `/build` again, or reset first for an explicit clean state. | A failed project with a graph reference triggers guarded deletion before rebuild. |
| Rebuild a completed graph | Use `/project/{project_id}/reset` then `/build`, or call `/build` with `force: true`. | Reset gives the clearest state transition. |
| Delete all project files | `DELETE /project/{project_id}`. | Deletes Cloud graph before local project files. |
| Delete only graph and keep project ontology | `POST /project/{project_id}/reset` or `DELETE /delete/{graph_id}`. | Direct graph delete clears all local project references to that graph. |

## UI-specific hints

- If the Home page start button is disabled, ensure at least one accepted file and a non-empty simulation requirement are present.
- If Step 1 shows ontology entities but not relation tags, inspect the API response directly. The canonical backend key is `ontology.edge_types`.
- If the graph canvas shows no nodes after build completion, call `/api/graph/data/{graph_id}` directly. Empty `nodes`/`edges` means Zep built an empty graph or ontology/source text did not yield entities; an endpoint error means Zep access or graph ID failed.
- If manual refresh spins indefinitely, check the browser console/API response and the backend `/data/{graph_id}` error.

## What not to do

- Do not run simulation preparation or report generation while recovering a broken Step 1 graph; finish graph recovery first.
- Do not pass `force: "true"` or `force: "false"`; strings are rejected.
- Do not manually replay Zep batch create/add/process calls from a client. Let MiroFish reconcile by persisted graph/batch operation identity.
- Do not edit generated skill runtime files to include local project paths, original source links, secret values, or private environment names.

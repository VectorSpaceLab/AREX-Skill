# Report API reference

All routes in this reference are under the `/api/report` prefix. Responses usually use `{ "success": true, "data": ... }` on success and `{ "success": false, "error": "..." }` on failure.

## Endpoint map

| Method and path | Purpose | Request inputs | Success data | Common failures |
|---|---|---|---|---|
| `POST /generate` | Start asynchronous report generation or reuse a completed report. | JSON `simulation_id` required; `force_regenerate` optional JSON boolean. | `simulation_id`, `report_id`, maybe `task_id`, `status`, `message`, `already_generated`. | `400` missing/invalid input, missing graph id or requirement; `404` missing simulation/project; `409` active simulation/updater, non-terminal or failed simulation, graph not completed, stale graph; `500` unexpected exception. |
| `POST /generate/status` | Read TaskManager status for a generation task or detect completed report by simulation. | JSON `task_id` optional if `simulation_id` is provided; `simulation_id` optional. | Task dictionary, or completed report marker with `already_completed: true`. | `400` neither task nor simulation id; `404` task not found; `500` exception. |
| `GET /{report_id}` | Get report metadata and full content when available. | Path `report_id`. | `Report.to_dict()`: ids, status, outline, markdown content, timestamps, error. | `404` report not found; `500` exception. |
| `GET /by-simulation/{simulation_id}` | Find the report for a simulation. | Path `simulation_id`. | Report dictionary plus `has_report: true`. | `404` no report with `has_report: false`; `500` exception. |
| `GET /list` | List reports, newest first. | Query `simulation_id` optional; `limit` integer default 50. | Array of report dictionaries and `count`. | `500` exception. |
| `GET /{report_id}/download` | Download Markdown report. | Path `report_id`. | Markdown attachment named `{report_id}.md`. | `404` missing report; `500` exception. |
| `DELETE /{report_id}` | Delete one report. | Path `report_id`. | `message` confirming deletion. | `404` missing report; `500` exception. |
| `POST /chat` | Chat with Report Agent. | JSON `simulation_id`, `message`, optional `chat_history`. | `response`, `tool_calls`, `sources`. | `400` missing simulation id/message or graph id; `404` simulation/project missing; `500` exception. |
| `GET /{report_id}/progress` | Read live file-backed generation progress. | Path `report_id`. | `status`, `progress`, `message`, `current_section`, `completed_sections`, `updated_at`. | `404` no progress file yet; `500` exception. |
| `GET /{report_id}/sections` | List saved section Markdown files. | Path `report_id`. | `report_id`, `sections`, `total_sections`, `is_complete`. | `500` exception. Missing folder returns an empty `sections` list, not necessarily `404`. |
| `GET /{report_id}/section/{section_index}` | Read one saved section by 1-based index. | Path `report_id`, integer `section_index`. | `filename`, `section_index`, `content`. | `404` section file not found; `500` exception. |
| `GET /check/{simulation_id}` | Check report existence and Step 5 unlock state. | Path `simulation_id`. | `has_report`, `report_status`, `report_id`, `interview_unlocked`. | `500` exception. |
| `GET /{report_id}/agent-log` | Incrementally read structured Report Agent logs. | Query `from_line` integer default 0. | `logs`, `total_lines`, `from_line`, `has_more`. | `500` exception. Missing file returns empty logs. |
| `GET /{report_id}/agent-log/stream` | Read all structured Report Agent logs at once. | Path `report_id`. | `logs`, `count`. | `500` exception. |
| `GET /{report_id}/console-log` | Incrementally read console-style Report Agent and Zep tool logs. | Query `from_line` integer default 0. | `logs`, `total_lines`, `from_line`, `has_more`. | `500` exception. Missing file returns empty logs. |
| `GET /{report_id}/console-log/stream` | Read all console log lines at once. | Path `report_id`. | `logs`, `count`. | `500` exception. |
| `POST /tools/search` | Debug graph semantic search. | JSON `graph_id`, `query`, optional `limit`. | `SearchResult.to_dict()`. | `400` missing graph id/query; `500` Zep or unexpected failure. |
| `POST /tools/statistics` | Debug graph node/edge counts and type distributions. | JSON `graph_id`. | Graph statistics dictionary. | `400` missing graph id; `500` Zep or unexpected failure. |

## Generate request and barrier semantics

`POST /generate` performs checks twice: once before starting and once under the graph lifecycle lock immediately before task creation and reader registration. Treat a late `409` as a real race, not as a harmless duplicate.

### Input validation

- Missing `simulation_id` -> `400`.
- `force_regenerate` present but not a JSON boolean -> `400` with `force_regenerate must be a JSON boolean`.
- Missing `graph_id` or simulation requirement -> `400`.

### Missing state

- Unknown simulation -> `404`.
- Unknown project -> `404`.

### Active or incomplete simulation barriers

The report API blocks generation with `409` when:

- A `ZepGraphMemoryManager` updater exists for the simulation. The response includes `ingestion_pending: true`.
- The simulation runner is `starting`, `running`, `paused`, or `stopping`. The response may also include `ingestion_pending` when a graph-memory updater exists.
- The runner state is missing or is not `completed`/`stopped`. A failed run after restart is still blocked; a successfully completed or stopped run is required.

### Graph freshness barriers

The report API blocks generation with `409` when:

- Project status is not `GRAPH_COMPLETED`.
- The simulation's stored `graph_id` differs from the project's current `graph_id`; prepare the simulation against the current graph before reporting.
- The project graph changes while the report is starting.
- Simulation or Zep ingestion becomes active while the report is starting.

### Cached report reuse

If `force_regenerate` is false and a completed report already exists for the simulation, success data is:

```json
{
  "simulation_id": "sim_xxxx",
  "report_id": "report_existing",
  "status": "completed",
  "message": "...",
  "already_generated": true
}
```

No new `task_id` is required for this branch.

## Generation task status

`POST /generate/status` consumes JSON, not query parameters. Use one of:

```json
{"task_id": "task_xxxx"}
```

or:

```json
{"simulation_id": "sim_xxxx"}
```

When `simulation_id` has a completed report, it returns `status: "completed"`, `progress: 100`, `already_completed: true`, and the `report_id`. Otherwise a `task_id` is required and the API returns the TaskManager dictionary, usually including task id, type, status, progress, message, result, error, timestamps, and metadata.

## Report object schema

`GET /{report_id}`, report lists, and by-simulation lookups use this report shape:

```json
{
  "report_id": "report_ab12cd34ef56",
  "simulation_id": "sim_xxxx",
  "graph_id": "mirofish_xxxx",
  "simulation_requirement": "scenario text",
  "status": "pending|planning|generating|completed|failed",
  "outline": {
    "title": "...",
    "summary": "...",
    "sections": [
      {"title": "Section title", "content": "optional final content"}
    ]
  },
  "markdown_content": "# Full report...",
  "created_at": "ISO timestamp",
  "completed_at": "ISO timestamp",
  "error": null
}
```

If `markdown_content` is empty in metadata, `ReportManager.get_report` attempts to read `full_report.md` from the report folder.

## Progress schema

`GET /{report_id}/progress` reads `progress.json`:

```json
{
  "status": "pending|planning|generating|completed|failed",
  "progress": 0,
  "message": "localized message",
  "current_section": null,
  "completed_sections": [],
  "updated_at": "ISO timestamp"
}
```

Observed progress ranges:

- `pending`, 0: report folder initialized.
- `planning`, 5 to 15: outline planning and save.
- `generating`, around 20 to 95: sections and assembly.
- `completed`, 100: full report saved.
- `failed`, -1: generation exception. Inspect `error` logs and metadata.

## Sections schema

`GET /{report_id}/sections` returns:

```json
{
  "report_id": "report_ab12cd34ef56",
  "sections": [
    {
      "filename": "section_01.md",
      "section_index": 1,
      "content": "## Section title\n\n..."
    }
  ],
  "total_sections": 1,
  "is_complete": false
}
```

`GET /{report_id}/section/1` returns the same single-section shape without wrapping it in a sections array. Section indexes are one-based; filenames are zero-padded to two digits.

## Agent log schema

`GET /{report_id}/agent-log?from_line=0` returns:

```json
{
  "logs": [
    {
      "timestamp": "ISO timestamp",
      "elapsed_seconds": 12.34,
      "report_id": "report_ab12cd34ef56",
      "action": "tool_call",
      "stage": "generating",
      "section_title": "Section title",
      "section_index": 1,
      "details": {
        "iteration": 1,
        "tool_name": "insight_forge",
        "parameters": {"query": "..."},
        "message": "..."
      }
    }
  ],
  "total_lines": 1,
  "from_line": 0,
  "has_more": false
}
```

Malformed JSONL rows are skipped when building `logs`, but `total_lines` still advances as the file is read. This means an incremental poller should advance from `from_line + len(logs)` for normal operation, but a forensic investigation of parse gaps should inspect the raw file.

## Console log schema

`GET /{report_id}/console-log?from_line=0` returns plain strings from `console_log.txt`:

```json
{
  "logs": ["[19:46:14] INFO: graph search completed"],
  "total_lines": 1,
  "from_line": 0,
  "has_more": false
}
```

The console logger attaches to Report Agent and Zep tool loggers during generation and is closed at the end of report generation, including failure paths.

## Chat schema

`POST /chat` request:

```json
{
  "simulation_id": "sim_xxxx",
  "message": "What explains the sentiment reversal?",
  "chat_history": [
    {"role": "user", "content": "Prior question"},
    {"role": "assistant", "content": "Prior answer"}
  ]
}
```

Response data:

```json
{
  "response": "assistant text",
  "tool_calls": [
    {"name": "panorama_search", "parameters": {"query": "..."}}
  ],
  "sources": ["..."]
}
```

The chat loop executes at most one tool per iteration and at most two tool calls per chat response. It strips generated `<tool_call>` blocks and fabricated `<tool_result>` blocks before returning the assistant response.

## Debug tool schemas

`POST /tools/search` success data:

```json
{
  "facts": ["fact text"],
  "edges": [
    {
      "uuid": "edge uuid",
      "name": "RELATION",
      "fact": "fact text",
      "source_node_uuid": "source uuid",
      "target_node_uuid": "target uuid"
    }
  ],
  "nodes": [
    {
      "uuid": "node uuid",
      "name": "entity name",
      "labels": ["Entity", "Person"],
      "summary": "summary text"
    }
  ],
  "query": "original query",
  "total_count": 1
}
```

`POST /tools/statistics` success data:

```json
{
  "graph_id": "mirofish_xxxx",
  "total_nodes": 123,
  "total_edges": 456,
  "entity_types": {"Person": 10},
  "relation_types": {"MENTIONS": 20}
}
```

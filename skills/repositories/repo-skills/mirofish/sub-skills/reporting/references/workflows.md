# Reporting workflows

This reference covers the operating sequence for MiroFish reporting: generate a report from a terminal simulation, stream progress/logs/sections, read or manage generated report files, enter Step 5 Report Agent chat, and use report-side graph tools for debugging.

## 1. Decide whether reporting is allowed

A report is allowed only when all of these are true:

- The caller has a real `simulation_id` known to `SimulationManager`.
- The simulation runner has a successful terminal status: `completed` or `stopped`.
- The runner is not `starting`, `running`, `paused`, or `stopping`.
- No `ZepGraphMemoryManager` updater is still active for the simulation.
- The project exists and has status `GRAPH_COMPLETED`.
- The project has a current `graph_id`.
- If the simulation stores a `graph_id`, it matches the project's current `graph_id`; otherwise the simulation may point at an older graph and must be prepared again.
- The project has a non-empty `simulation_requirement`; this becomes the Report Agent's scenario context.

If any precondition is a graph-build or simulation-run issue, do not improvise in this sub-skill. Route to the sibling owner, then return to reporting after the blocker is cleared.

## 2. Generate a report

Use the backend API directly:

```http
POST /api/report/generate
Content-Type: application/json

{
  "simulation_id": "sim_xxxx",
  "force_regenerate": false
}
```

Important details:

- `force_regenerate` is optional but, if present, must be a JSON boolean. Do not send the string `"true"`.
- With `force_regenerate: false`, a completed cached report for the same simulation can be returned immediately with `already_generated: true` and status `completed`.
- With `force_regenerate: true`, the frontend Step 3 path starts a fresh report and then navigates to Step 4 using the returned `report_id`.
- On success for a new report, the API returns both `report_id` and `task_id` immediately while a background thread writes report artifacts.
- The report registers itself as a graph reader until the background worker exits, so graph deletion and graph-memory restart should wait.

Successful new-report response shape:

```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_xxxx",
    "report_id": "report_ab12cd34ef56",
    "task_id": "task_xxxx",
    "status": "generating",
    "message": "...",
    "already_generated": false
  }
}
```

## 3. Poll progress, logs, and sections

The Step 4 frontend follows the Report Agent by polling logs rather than waiting on only task status:

- `GET /api/report/{report_id}/agent-log?from_line=N` about every 2 seconds.
- `GET /api/report/{report_id}/console-log?from_line=N` about every 1.5 seconds.
- Start with `from_line=0`; after each response set `N = response.data.from_line + len(response.data.logs)`.
- `has_more` is always `false` for these file-backed reads; use the new line count, not `has_more`, to continue incremental polling.

Use structured `agent_log.jsonl` milestones to build UI or agent state:

| Log action | Meaning | Operating response |
|---|---|---|
| `report_start` | Report Agent initialized with `simulation_id`, `graph_id`, and `simulation_requirement`. | Start elapsed timer and confirm the report is tied to the expected simulation. |
| `planning_start` | Outline planning began. | Expect `outline.json` only after planning completes. |
| `planning_context` | Simulation graph context was fetched for planning. | Useful when the outline seems unsupported by graph evidence. |
| `planning_complete` | Outline is available under `details.outline`. | Render/read `title`, `summary`, and `sections`. |
| `section_start` | One section is now active. | Mark `section_index` as in-progress. |
| `react_thought` | ReACT iteration rationale for a section. | Debug only; do not treat as durable report content. |
| `tool_call` | Report Agent invoked an internal graph/interview tool. | Inspect `details.tool_name` and `details.parameters`. |
| `tool_result` | Tool output was injected into generation. | Inspect full `details.result`; it is not intentionally truncated in the report log. |
| `llm_response` | Raw LLM response for an iteration. | Use to diagnose invalid tool-call formatting or fabricated tool result tags. |
| `section_content` | Draft section content was generated. | Do not treat as durable final section; wait for `section_complete`. |
| `section_complete` | A section file has been saved and `details.content` contains full `## Title` markdown. | Store/display content for that section. |
| `report_complete` | Full report assembled and saved. | Stop polling and mark Step 4 completed. |
| `error` | Report generation failed. | Read `details.error`, `meta.json.error`, and console tail. |

Supplement log polling with file-backed endpoints when needed:

- `GET /api/report/{report_id}/progress` returns `status`, integer `progress`, `message`, `current_section`, `completed_sections`, and `updated_at`.
- `GET /api/report/{report_id}/sections` returns every saved `section_*.md`, a count, and `is_complete` based on report status.
- `GET /api/report/{report_id}/section/{section_index}` returns a single section by 1-based index using names such as `section_01.md`.
- `POST /api/report/generate/status` accepts `{ "task_id": "..." }`, or `{ "simulation_id": "..." }` to detect an already completed report for that simulation.

## 4. Read, download, list, or delete reports

Use these after or during generation:

- `GET /api/report/{report_id}` returns report metadata, outline, status, full markdown content when available, timestamps, and errors.
- `GET /api/report/by-simulation/{simulation_id}` returns the report for a simulation or `404` with `has_report: false`.
- `GET /api/report/list?simulation_id=sim_xxxx&limit=50` lists reports, newest first, optionally filtered by simulation.
- `GET /api/report/{report_id}/download` downloads Markdown. If `full_report.md` is missing but metadata has `markdown_content`, the backend streams a temporary Markdown file.
- `DELETE /api/report/{report_id}` removes the report folder; legacy single-file reports are also cleaned up when present.

Local artifact inspection is often faster than repeated HTTP calls in debugging. Use the bundled helper:

```bash
python scripts/report-log-summary.py /path/to/report_xxxx
```

The helper is read-only and tolerates missing report files. Use `--json` if you need machine-readable output.

## 5. Step 4 behavior

Step 4 is a report-generation workbench:

1. It receives a `report_id` in the report route.
2. Its outer view loads `GET /api/report/{report_id}` to discover `simulation_id`, then loads simulation and graph metadata for display.
3. It starts log polling as soon as `report_id` exists.
4. It builds the outline from the `planning_complete` log, not by polling `outline.json` directly.
5. It populates generated sections from `section_complete` logs, not from `section_content` drafts.
6. It marks completion only on `report_complete`, then stops both log pollers.
7. Its workflow display is effectively: Planning / Outline -> each section number -> Complete. If a user says "Step 4 is stuck at section 2", inspect `agent_log.jsonl`, `console_log.txt`, and `progress.json` around that section.

## 6. Step 5 Report Agent chat

Step 5 is an interaction workbench. For Report Agent chat:

1. Start from a completed `report_id` when possible.
2. Load `GET /api/report/{report_id}` to recover `simulation_id`.
3. Load all report-agent logs once with `GET /api/report/{report_id}/agent-log?from_line=0` to reconstruct outline and sections for display.
4. Send chat messages to:

```http
POST /api/report/chat
Content-Type: application/json

{
  "simulation_id": "sim_xxxx",
  "message": "Explain the main trend shift.",
  "chat_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ]
}
```

5. Keep only recent history; the frontend sends the last ten prior messages.
6. The backend response contains `response`, `tool_calls`, and `sources`.

Backend chat can technically run when there is graph context but no completed report; in that case the system prompt says no report is available. For user-facing Step 5, prefer `GET /api/report/check/{simulation_id}` and require `interview_unlocked: true` before presenting report-based interaction.

## 7. Internal Report Agent tools

During generation and chat, `ReportAgent` can invoke these internal tools:

| Tool | Purpose | Parameters |
|---|---|---|
| `insight_forge` | Deep analysis over simulation graph evidence; decomposes questions and combines semantic facts, entity insights, and relationship chains. | `query`, optional `report_context` |
| `panorama_search` | Broad graph overview including active and historical/expired facts. | `query`, optional `include_expired` |
| `quick_search` | Lightweight search for a direct fact check. | `query`, optional `limit` |
| `interview_agents` | Calls simulated agents through the simulation interview path to collect quotations. | `interview_topic` or `query`, optional `max_agents` up to 10 |

Legacy internal tool names are redirected: `search_graph` -> `quick_search`; `get_simulation_context` -> `insight_forge`; `get_graph_statistics`, `get_entity_summary`, and `get_entities_by_type` remain compatibility paths inside `ReportAgent._execute_tool`.

## 8. Report-side debug tools

The public report API exposes two debug endpoints:

```http
POST /api/report/tools/search
Content-Type: application/json

{
  "graph_id": "mirofish_xxxx",
  "query": "keyword or semantic query",
  "limit": 10
}
```

This uses `ZepToolsService.search_graph` and returns a `SearchResult` dictionary with `facts`, `edges`, `nodes`, `query`, and `total_count`. The query sent to Zep is capped by the Zep utility layer, while the original query remains in the result object for traceability.

```http
POST /api/report/tools/statistics
Content-Type: application/json

{
  "graph_id": "mirofish_xxxx"
}
```

This uses `ZepToolsService.get_graph_statistics` and returns `graph_id`, `total_nodes`, `total_edges`, `entity_types`, and `relation_types`.

Use these endpoints to verify the report graph has searchable content before blaming the Report Agent. If they fail with Zep authentication, permission, missing graph, or transient read errors, treat the failure as real; report tools should not silently convert such errors into empty data.

# Reporting troubleshooting

Use this reference when report generation, progress streaming, report artifacts, Report Agent chat, or report-side graph tools fail in predictable ways.

## Quick triage checklist

1. Identify whether you have a `simulation_id`, a `report_id`, or both.
2. If report generation failed before returning a `report_id`, inspect the HTTP status and JSON error from `POST /api/report/generate`.
3. If a `report_id` exists, read:
   - `GET /api/report/{report_id}/progress`
   - `GET /api/report/{report_id}/agent-log?from_line=0`
   - `GET /api/report/{report_id}/console-log?from_line=0`
   - `GET /api/report/{report_id}`
4. If local file access is available, run `python scripts/report-log-summary.py REPORT_DIR` for a compact report-directory summary.
5. Route graph build or simulation finalization blockers to their sibling sub-skills instead of trying to bypass report barriers.

## `POST /api/report/generate` returns 409

| Symptom/error text | Likely cause | What to do |
|---|---|---|
| `Simulation or Zep graph ingestion is still active; wait for a terminal run status before generating a report` with `ingestion_pending: true` | A graph-memory updater is still ingesting simulation results into Zep. | Wait for ingestion to finish. Use the simulation-run sub-skill to inspect runner/updater status. Do not force report generation. |
| Same active-ingestion message without updater pending | The simulation runner is still `starting`, `running`, `paused`, or `stopping`. | Wait for `completed` or `stopped`. `stopping` is not terminal for reporting. |
| `A successfully completed or stopped simulation is required before generating a report` | Runner state is missing, failed, or not a successful terminal state. | Re-run or repair the simulation via the simulation-run sub-skill. A failed run after restart is not reportable. |
| `The project graph must be completely built before reporting` | Project status is not `GRAPH_COMPLETED`. | Route to graph-build; complete graph construction before reporting. |
| `The simulation references an older graph; prepare it again before generating a report` | Simulation state points at a stale graph id compared with the project. | Re-prepare the simulation against the current graph before reporting. |
| `The project graph changed while reporting was starting` | A graph lifecycle race occurred between precheck and lock-protected start. | Re-read project/simulation state; if graph truly changed, route to graph-build or simulation setup. |
| `Simulation or Zep graph ingestion became active; retry after it reaches a terminal state` | A simulation or updater started during report startup. | Wait for terminal state and retry generation. |

Why the barrier exists: report generation registers a background graph-reader lease. While the lease is active, graph deletion and graph-memory restarts should be blocked so the report does not read a graph that is being deleted or mutated.

## Missing or stale graph data

Symptoms:

- `400` missing graph id.
- `400` missing simulation requirement.
- `404` project not found.
- Report starts but graph-tool calls fail with authorization, missing graph, or read errors.
- Report content looks empty or generic despite a completed simulation.

Actions:

1. Confirm the simulation maps to the expected project and graph id.
2. Confirm project status is `GRAPH_COMPLETED`.
3. Use `POST /api/report/tools/statistics` with the report graph id. Zero nodes/edges or a Zep exception points to graph-build or credential problems.
4. Use `POST /api/report/tools/search` with a short query from the simulation requirement. If this fails, do not blame outline generation first; fix graph access/search.
5. If simulation graph id and project graph id differ, prepare the simulation again before reporting.

Report-side Zep tool failures should remain visible. Authentication, permission, not-found, or repeated transient read failures should not be converted into empty search results.

## Progress says failed or stops changing

Symptoms:

- `progress.status == "failed"` and `progress.progress == -1`.
- No new `agent_log.jsonl` entries for a long period.
- Step 4 remains on one section or on finalizing.

Actions:

1. Read `meta.json.error` through `GET /api/report/{report_id}`.
2. Read `agent_log.jsonl` and find the last action. If the last action is `error`, use `details.error` and `details.message`.
3. Read the last console log lines for Zep, LLM, tool, or parsing failures.
4. Compare `progress.updated_at` with the newest agent-log timestamp.
5. If all sections exist but no `report_complete` exists, check whether `full_report.md` was written. A report may have failed during final assembly or metadata save.
6. If only `section_content` exists for the active section, wait or investigate; durable section completion is `section_complete`.

## Missing logs or log gaps

| Situation | Meaning | Action |
|---|---|---|
| `agent-log` returns empty logs just after `POST /generate` | The background worker may not have initialized `ReportLogger` yet, or report startup failed very early. | Poll again briefly; also check task status and progress endpoint. |
| `console-log` returns empty logs | The console log file may not exist yet or no attached logger wrote lines. | Not fatal by itself; inspect structured logs and progress. |
| `agent-log` total lines advances but logs seem fewer than expected | Malformed JSONL rows are skipped by the API parser. | Inspect the raw file if local access is available. The summary script reports parse errors. |
| Step 4 UI is behind even though files exist | Step 4 reconstructs outline and sections from structured logs, not direct file reads. | Query `agent-log` from line 0 and check for `planning_complete` and `section_complete`. |
| Poller repeats same data | Caller failed to advance `from_line`. | Set next `from_line` to the previous `from_line` plus number of parsed returned logs or lines. |

## Section file surprises

Symptoms:

- `section_01.md` exists but the UI still marks it in-progress.
- Content headings appear as bold text instead of Markdown headings.
- Downloaded `full_report.md` has fewer headings than raw LLM output.

Explanation:

- The durable UI boundary is `section_complete`, not just the existence of a file or `section_content`.
- `ReportManager` removes duplicate section titles and converts inner headings to bold text before saving sections.
- Full-report post-processing preserves the main title and section titles while cleaning duplicate/deeper headings.

Actions:

1. Use `GET /api/report/{report_id}/sections` for file-backed section state.
2. Use `GET /api/report/{report_id}/agent-log?from_line=0` to verify whether `section_complete` was logged.
3. Compare `section_*.md` with `full_report.md` only after `report_complete`.

## Chat prerequisites and failures

| Symptom | Likely cause | Action |
|---|---|---|
| `POST /api/report/chat` returns `400` requiring simulation id | Missing `simulation_id`. | Load report metadata first to recover the simulation id. |
| Chat returns `400` requiring message | Empty `message`. | Send a non-empty user message. |
| Chat returns missing graph id | Simulation/project has no graph id. | Route to graph-build or simulation setup. |
| Chat works but answer says no report is available | Backend can chat with graph context even before a completed report is loaded. | For Step 5 report interaction, check `GET /api/report/check/{simulation_id}` and require `interview_unlocked: true`. |
| Chat answer omits expected tool-result text | The Report Agent strips fabricated `<tool_result>` blocks from LLM output. | Inspect `tool_calls` and real `tool_result` logs for generation. For chat, the returned response is sanitized. |
| Tool calls stop after one or two calls | Chat loop intentionally executes at most one tool per iteration and two total tool calls. | Ask a narrower follow-up or use debug tool endpoints for direct graph inspection. |

Step 5 also supports direct simulated-agent interviews and surveys, but those use simulation APIs. Route those operations to the simulation-run sub-skill.

## Fabricated `<tool_result>` tags

Report Agent sanitization removes model-fabricated tool-result blocks from LLM text before using or returning responses. It handles:

- Lowercase or uppercase `<tool_result>` tags.
- Nested fake tool-result blocks.
- Unclosed or malformed opening tags.
- Stray closing tags.

This prevents a model from inventing tool output in the same response that requested a real tool call. If a user asks why a chunk of text disappeared, inspect the raw `llm_response` log and compare it to the cleaned section or chat response. Real tool output should appear as `tool_result` log entries, not as inline fabricated tags inside an LLM response.

## Tool result or graph debug failures

Use these clues:

- `tool_call` without a matching `tool_result`: tool execution may have raised before result logging, or generation was interrupted.
- `tool_result` beginning with an error phrase: `ReportAgent._execute_tool` catches many internal tool errors and returns an error string for the LLM to handle.
- `/tools/search` or `/tools/statistics` returns `500`: public debug endpoint propagated a Zep or unexpected error.
- Very long search query: the Zep query sent to the API is normalized/capped, but the original query remains in the result for traceability.

Actions:

1. Try `/tools/statistics` first to confirm the graph is readable.
2. Try `/tools/search` with a short query from the simulation requirement.
3. If debug endpoints fail, fix graph credentials, graph id, or Zep availability through graph-build before regenerating.
4. If debug endpoints work but internal `insight_forge` or `panorama_search` fails, inspect console logs for LLM sub-query generation, entity reads, edge reads, or relationship traversal errors.

## Delete/download issues

- `GET /{report_id}/download` requires the report metadata to exist. If `full_report.md` is missing but metadata contains `markdown_content`, the backend streams a temporary Markdown file.
- `DELETE /{report_id}` removes the report folder. It also knows how to delete legacy single JSON/Markdown files for the same id.
- After deletion, by-report lookups should return `404`, while list responses simply omit the report.

## Verification candidates this troubleshooting supports

Later verification can adapt native candidates around:

- Fake tool-result sanitization: ensure fabricated `<tool_result>` blocks are stripped while legitimate text is preserved.
- Report generation barriers: active runner/updater, failed runner, stale graph, and graph reader leases should block unsafe reporting or graph mutation.
- Zep Cloud report-tool contracts: search query capping, visible read failures, and graph statistics/search behavior should remain explicit.

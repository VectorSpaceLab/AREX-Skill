---
name: reporting
description: "Generates, monitors, reads, chats with, manages, and troubleshoots
  MiroFish simulation reports and report-side graph tools."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# reporting

Use this sub-skill when a task asks to generate a MiroFish report from a completed simulation, follow report progress, read `section_01.md`, inspect `agent_log.jsonl` or `console_log.txt`, download or delete a report, chat with the Report Agent, diagnose `report returns 409`, understand Step 4/5 report interaction, or reason about `insight_forge` / `panorama_search` / report graph-tool behavior.

## Route first

- If the graph is not built, stale, being deleted, or needs Zep ingestion work, route to the sibling `graph-build` sub-skill.
- If the simulation has not been prepared, started, stopped, or finalized, route to the sibling `simulation-run` sub-skill before attempting report generation.
- If the user wants Step 5 direct interviews or surveys with simulated platform agents rather than Report Agent chat, route those simulation interview calls to `simulation-run`; keep only Report Agent chat here.

## Read or run the bundled material

- Read [references/workflows.md](references/workflows.md) when generating a report, polling logs/sections/progress, moving from Step 4 to Step 5, chatting with the Report Agent, or using report-side debug tools.
- Read [references/api-reference.md](references/api-reference.md) when constructing `/api/report/*` requests, interpreting response payloads, or deciding what an HTTP status code means.
- Read [references/report-artifacts.md](references/report-artifacts.md) when inspecting report directories, `progress.json`, `outline.json`, `meta.json`, `section_*.md`, `full_report.md`, `agent_log.jsonl`, or `console_log.txt`.
- Read [references/troubleshooting.md](references/troubleshooting.md) when report generation is blocked, stale, missing logs, missing graph data, failing in a report tool, or affected by fabricated `<tool_result>` tags.
- Run `python scripts/report-log-summary.py --help` to inspect the bundled report-directory summarizer, or `python scripts/report-log-summary.py --self-test` to smoke-check it without MiroFish services.

## Minimal safe operating loop

1. Start with either a completed `simulation_id` or an existing `report_id`. Do not generate a report while simulation execution or Zep graph-memory ingestion is active.
2. For a new report, call `POST /api/report/generate` with JSON `{ "simulation_id": "...", "force_regenerate": false }` or `true`; `force_regenerate` must be a JSON boolean.
3. Store both `report_id` and `task_id` from the response. The report directory and log endpoints can be polled immediately after the request returns.
4. Poll `GET /api/report/{report_id}/agent-log?from_line=N` and `GET /api/report/{report_id}/console-log?from_line=N`; optionally poll `GET /api/report/{report_id}/progress` and `GET /api/report/{report_id}/sections` for file-backed state.
5. Treat `planning_complete` as the outline boundary, `section_complete` as the durable section boundary, and `report_complete` plus `progress.status == "completed"` as final completion.
6. After completion, read or download `full_report.md`, use `GET /api/report/check/{simulation_id}` to confirm interaction unlock state, and use `POST /api/report/chat` for Report Agent follow-up.

# Report artifacts

MiroFish report generation writes a self-contained report folder under the backend upload area's `reports/` directory. The exact upload root is a runtime configuration detail; avoid baking local checkout paths into instructions. Work from a `report_id` and either use report API endpoints or inspect the report folder resolved by the running backend.

## New report folder layout

```text
reports/
  {report_id}/
    meta.json
    outline.json
    progress.json
    agent_log.jsonl
    console_log.txt
    section_01.md
    section_02.md
    ...
    full_report.md
```

Older single-file report layouts may still be read or deleted by compatibility code, but new generation uses a folder per report.

## `meta.json`

`meta.json` is the durable report metadata written by `ReportManager.save_report`. It has the same shape as `GET /api/report/{report_id}`:

```json
{
  "report_id": "report_ab12cd34ef56",
  "simulation_id": "sim_xxxx",
  "graph_id": "mirofish_xxxx",
  "simulation_requirement": "scenario text",
  "status": "pending|planning|generating|completed|failed",
  "outline": null,
  "markdown_content": "",
  "created_at": "ISO timestamp",
  "completed_at": "",
  "error": null
}
```

Lifecycle notes:

- Created early with `status: "pending"`.
- Updated with `status: "planning"` and an outline after outline planning.
- Updated with `status: "completed"`, `completed_at`, and `markdown_content` after full assembly.
- Updated with `status: "failed"` and `error` if generation raises an exception.
- If `markdown_content` is empty, the backend may still return content by reading `full_report.md`.

## `outline.json`

`outline.json` is saved after planning completes:

```json
{
  "title": "Report title",
  "summary": "Short report summary",
  "sections": [
    {"title": "Executive Summary", "content": ""},
    {"title": "Trend Analysis", "content": ""}
  ]
}
```

The `planning_complete` log also embeds this outline under `details.outline`. Step 4 uses that log event to render its initial outline.

## `progress.json`

`progress.json` is the file-backed progress state:

```json
{
  "status": "generating",
  "progress": 42,
  "message": "localized progress text",
  "current_section": "Trend Analysis",
  "completed_sections": ["Executive Summary"],
  "updated_at": "ISO timestamp"
}
```

Important values:

- `status`: `pending`, `planning`, `generating`, `completed`, or `failed`.
- `progress`: 0 at initialization, 5/15 during planning, roughly 20-95 during section generation and assembly, 100 on success, -1 on failure.
- `current_section`: section title while a section is active, otherwise `null`.
- `completed_sections`: titles of saved sections, not merely drafted sections.
- `updated_at`: useful for detecting a stuck report if it stops changing while no terminal log appears.

## `section_*.md`

Each saved section is a Markdown file named with a one-based, zero-padded index:

```text
section_01.md
section_02.md
section_10.md
```

Each file starts with a system-added level-2 title:

```markdown
## Section title

Section content...
```

Section cleaning behavior:

- Repeated leading title lines matching the section title are removed before saving.
- Headings inside generated section content are converted to bold text, because the section title itself owns the heading level.
- Leading empty lines and leading Markdown separators are removed.
- The `section_complete` agent log stores the full section markdown under `details.content`; use it as the durable event boundary.
- The earlier `section_content` log can contain final-looking text, but it is a draft boundary and does not prove the file was saved.

## `full_report.md`

The full report is assembled from the outline and saved sections:

```markdown
# Report title

> Report summary

---

## First section

...

## Second section

...
```

Post-processing behavior:

- The main `#` report title and `##` section titles are preserved.
- Duplicate headings near each other are removed.
- Headings at deeper levels are converted to bold text or removed according to the report post-processor.
- Extra blank lines and repeated separators are cleaned.
- Sections are concatenated in sorted filename order.

If a user reports that downloaded content differs from the UI, compare `section_*.md`, `full_report.md`, and `meta.json.markdown_content`.

## `agent_log.jsonl`

`agent_log.jsonl` is structured JSON Lines. Each line is one log entry:

```json
{
  "timestamp": "ISO timestamp",
  "elapsed_seconds": 3.21,
  "report_id": "report_ab12cd34ef56",
  "action": "section_complete",
  "stage": "generating",
  "section_title": "Trend Analysis",
  "section_index": 2,
  "details": {
    "content": "## Trend Analysis\n\n...",
    "content_length": 1234,
    "message": "localized text"
  }
}
```

Common action details:

| Action | Typical `details` keys |
|---|---|
| `report_start` | `simulation_id`, `graph_id`, `simulation_requirement`, `message` |
| `planning_start` | `message` |
| `planning_context` | `message`, `context` |
| `planning_complete` | `message`, `outline` |
| `section_start` | `message` |
| `react_thought` | `iteration`, `thought`, `message` |
| `tool_call` | `iteration`, `tool_name`, `parameters`, `message` |
| `tool_result` | `iteration`, `tool_name`, `result`, `result_length`, `message` |
| `llm_response` | `iteration`, `response`, `response_length`, `has_tool_calls`, `has_final_answer`, `message` |
| `section_content` | `content`, `content_length`, `tool_calls_count`, `message` |
| `section_complete` | `content`, `content_length`, `message` |
| `report_complete` | `total_sections`, `total_time_seconds`, `message` |
| `error` | `error`, `message` |

Tool outputs are intentionally complete in `agent_log.jsonl`; they can be large. Prefer summaries when showing them to users.

## `console_log.txt`

`console_log.txt` stores text log lines from Report Agent and Zep tool loggers while generation is active. Lines use a console-style prefix such as:

```text
[19:46:14] INFO: graph search completed
[19:46:15] WARNING: section conflict retry
```

Use it for:

- Zep read/search failures.
- Tool execution failures.
- Long gaps between structured milestones.
- Warnings about invalid or conflicting LLM tool-call formatting.

If the file is missing, the API returns an empty log list. Missing console logs are not by themselves proof of failure; check `progress.json`, `meta.json`, and `agent_log.jsonl`.

## Read-only local summarization

The bundled script summarizes a report directory without importing MiroFish:

```bash
python scripts/report-log-summary.py /path/to/report_ab12cd34ef56
python scripts/report-log-summary.py /path/to/report_ab12cd34ef56 --json
```

It reports missing files as warnings rather than failing. It is safe to run against a live report folder because it only reads files.

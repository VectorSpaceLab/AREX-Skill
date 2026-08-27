# Session Parser Reference

Session parsing is deliberately separated from local source discovery. CLI adapters locate and deliver stable raw records; server parsers and classifiers convert those raw records into stored event rows and frontend trace events.

## Two parser paths

### Ingest/write path

`observal-server/services/session_ingest.py` receives raw lines from `POST /api/v1/ingest/session` and performs:

1. Agent id/version normalization.
2. Deduplication by `(session_id, project_id, user_id, harness, source line index)`.
3. Conflict detection when an already acknowledged source line is retried with different content.
4. Strict harness classifier lookup through `services.session_parsers.ingest_classify.get_classifier(harness)`.
5. Event type, preview, tool name/id, timestamp, token/model usage, uuid/parent uuid extraction.
6. Raw-line redaction and ClickHouse insert into `session_events`.
7. Optional extra rows, currently used for Kiro credit metadata.
8. Aggregate refresh and checkpoint advancement.
9. Final integrity hash validation and repair rewinds when needed.

`ingest_classify.py` maps `session_parser` ids to classifier triples:

```text
parser id -> (classify_fn, preview_fn, tool_info_fn)
```

It also owns timestamp extractor registration and extra-row dispatch.

### Read/display path

`observal-server/services/session_parsers/__init__.py` dispatches raw ClickHouse rows to parser modules for session-detail display:

```text
HARNESS_REGISTRY[harness]["session_parser"] -> _PARSERS[parser_id] -> parse_rows(rows)
```

Dispatch is strict: an unknown harness or missing parser id raises instead of silently using the wrong format. Parser modules should accept untrusted raw lines, use helpers from `services/session_parsers/base.py`, and fall back to `basic_event(row)` when a line is malformed or outside the known format.

## Current parser id map

| Parser id | Harnesses using it | Raw format summary | Important behaviors |
|---|---|---|---|
| `claude-code` | `claude-code` | JSONL with top-level `type` and `message.content` blocks | Handles user/assistant/system/attachment/meta, thinking, tool use/results, token usage. |
| `cursor` | `cursor` | Claude-like content blocks but top-level `role` | Strips Cursor XML prompt wrappers; timestamps usually fall back to ingest time. |
| `kiro` | `kiro` | Top-level `kind`: `Prompt`, `AssistantMessage`, `ToolResults`; payload under `data` | Merges `ToolResults` into prior tool use by `toolUseId`; strips Kiro-internal tool input keys; synthetic Kiro credit rows become `kiro_credits`. |
| `codex` | `codex` | `event_msg`, `response_item`, `session_meta`, `turn_context` records | Handles user/agent messages, token counts, function calls/results, developer/context rows. |
| `copilot-cli` | `copilot`, `copilot-cli` | Copilot envelope `{agentId, ts, event:{type,...}}` plus flat fallback | Merges tool results into calls by parent id; supports VS Code materialized hook records. |
| `goose` | `goose` | Observal mirror records: `session`, `message`, `session_end` | Parses Goose content blocks, usage/cost, failed tools, orphan tool results, delegated sessions. |
| `opencode` | `opencode` | OpenCode plugin emits Claude-Code-compatible records | Read parser and ingest classifier delegate to Claude Code format until the plugin format diverges. |
| `pi` | `pi` | Entry-level `type` plus `message.role`; tool calls use `toolCall` | Handles model/thinking changes, branch summaries, bash execution, cost data, toolResult role. |
| `antigravity` | `antigravity` | Transcript rows with `step_index`, `source`, `type`, `status`, `created_at`, `content`, `tool_calls` | Strips `<USER_REQUEST>` wrappers, links tool results to prior planner responses by step index, marks tool errors. |

## Adding or changing a parser

Use this checklist when a harness has a new raw format or an existing format changes:

1. Confirm the registry `session_parser` id. Reuse an existing id only when the raw wire/source format is actually compatible.
2. Add or update `observal-server/services/session_parsers/<parser_id>.py` with `parse_rows(rows: list[dict]) -> list[dict]`.
3. Register `parse_rows` in `_PARSERS` inside `services/session_parsers/__init__.py`.
4. Add ingest classifier functions in `ingest_classify.py`: classify, preview, and tool info.
5. Register the parser id in `_CLASSIFIERS`.
6. Add a timestamp extractor in `_TS_EXTRACTORS` if the format carries source timestamps; return `None` when no trustworthy timestamp exists.
7. Add extra rows only when durable metadata cannot be represented as ordinary source records. Kiro credits are the reference.
8. Add token/model extraction in `session_ingest.py` `_USAGE_EXTRACTORS` when the format is not Claude-like.
9. Add uuid/parent uuid extraction in `_UUID_EXTRACTORS` when the format does not use `uuid` and `parentUuid`.
10. Add tests for parser output, classifier output, preview/tool info, timestamp handling, malformed records, usage extraction, uuid extraction, ingest dedupe/conflict behavior, and API display routing.

## Parser implementation rules

- Treat every raw line as untrusted. Use `load_line`, `str_field`, `dict_field`, and `list_field` to avoid crashes on scalar/list/object shape mismatches.
- Never drop unknown meaningful records silently. Skip only known filler/continuation lines; otherwise emit a system/basic event.
- Keep source discovery out of server parsers. The parser sees ClickHouse rows, not local files.
- Keep transport and checkpoint logic out of parsers. The ingest service and CLI outbox own that behavior.
- Redact previews through the ingest service; parser display code should still avoid expanding huge raw bodies unnecessarily.
- Preserve tool-call/tool-result relationships when the raw format provides ids or stable ordering.
- Preserve token usage and model metadata when the source includes them.
- For host formats without timestamps, return `None` from timestamp extraction so ingestion uses the safe fallback/inherited timestamp.

## Expected normalized event surfaces

The frontend trace viewer expects dictionaries with fields like:

- `timestamp`: ClickHouse-compatible or ISO-derived string.
- `event_name`: examples include `hook_userpromptsubmit`, `hook_assistant_response`, `hook_assistant_thinking`, `hook_pretooluse`, `hook_posttooluse`, `hook_toolresult`, `hook_sessionstart`, `hook_sessionend`, `system`, `meta`, and parser-specific rows such as `kiro_credits`.
- `body`: short display text.
- `attributes`: tool names, tool inputs/results, token/model data, ids, status, costs, or credits.
- `service_name`: harness id.

Raw ingest rows also store `event_type`, `tool_name`, `tool_id`, `uuid`, `parent_uuid`, `input_tokens`, `output_tokens`, cache token counts, `model`, `content_preview`, `source_end_offset`, `line_hash`, and `raw_line`.

## Verification commands

Run parser coverage first:

```bash
python skills/disco/observal/sub-skills/harness-telemetry/scripts/check_harness_registry.py --repo-root . --pretty
```

Expected signal: no missing `read_parser`, `ingest_classifier`, or `timestamp_extractor` entries.

Run focused parser and ingest tests:

```bash
cd observal-server && uv run pytest ../tests/test_session_ingest.py -q
cd observal-server && uv run pytest ../tests/test_claude_code_session_parser.py ../tests/test_kiro_session_delivery.py -q
cd observal-server && uv run pytest ../tests/test_goose_session_parser.py ../tests/test_goose_session_delivery.py -q
cd observal-server && uv run pytest ../tests/test_antigravity_session_parser.py ../tests/test_antigravity_session_delivery.py -q
cd observal-server && uv run pytest ../tests/test_pi_session_parser.py -q
```

Expected signal: malformed-record tests do not crash; parser-specific trace events match expected names/attributes; ingest rejects unknown harness/classifier gaps before writing rows.

For API display routing:

```bash
cd observal-server && uv run pytest ../tests/test_sessions_api.py::test_session_parser_failure_propagates -q
```

Expected signal: parser dispatch errors are visible and not silently converted to misleading events.

## Common parser failure signatures

| Symptom | Likely cause | Fix |
|---|---|---|
| `KeyError` for parser id | Registry `session_parser` does not match `_PARSERS` or `_CLASSIFIERS` | Register the parser id in both read and ingest paths, or point the registry to a proven compatible parser id. |
| Raw rows stored but trace detail is empty | Classifier returns `None` for too many real lines, or read parser skips meaningful rows | Narrow skip rules to known filler lines; emit system/basic events for unknown records. |
| Tool results appear as orphan rows | Parser lacks id/parent merge logic or uses wrong id field | Add a tool-call index keyed by the host's stable call id; test call/result pairing. |
| Token totals are zero despite source usage | `_USAGE_EXTRACTORS` missing or reading wrong field names | Add harness-specific usage extractor and tests in `tests/test_session_ingest.py`. |
| Timestamps all show ingest time | Timestamp extractor returns `None` or reads wrong source field | Implement parser-specific timestamp extraction; return `None` only when the host truly lacks timestamps. |
| Permanent 422/400 ingest rejection | Request shape violates API bounds or parser/classifier raised bad data | Check line sizes, ordered byte offsets, source format assumptions, and raw-line JSON object shape. |

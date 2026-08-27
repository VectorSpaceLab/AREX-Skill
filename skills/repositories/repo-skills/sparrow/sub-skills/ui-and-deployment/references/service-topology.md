# Service topology reference

Sparrow's UI shells are thin orchestration surfaces. They validate user input, collect deployment metadata, call the LLM API, and optionally read/write Oracle-backed operational data. They do not own model execution semantics.

## Topology overview

```text
Browser
  ├─ Gradio UI process
  │    ├─ POST LLM API /api/v1/sparrow-llm/inference
  │    ├─ POST LLM API /api/v1/sparrow-llm/instruction-inference
  │    ├─ optional Oracle DB pool for keys, dashboard, feedback
  │    └─ local Gradio temporary-file cleaner
  │
  └─ Next UI server
       ├─ /process page
       ├─ /dashboard page
       ├─ /feedback page
       ├─ /api/inference -> server action -> LLM API /inference
       ├─ /api/summarize -> server action -> LLM API /instruction-inference
       └─ optional Oracle DB pool for keys, dashboard, feedback

Optional side services
  ├─ OCR API: independent /api/v1/sparrow-ocr/inference service
  └─ Agents API: independent /api/v1/sparrow-agents service with async task support
```

## Default service roles and ports

| Service | Default observed port | UI relationship | Owner skill |
| --- | ---: | --- | --- |
| Gradio UI | `7861` | Direct user shell; calls LLM API server-side. | `ui-and-deployment` |
| Next UI dev server | `3000` | React/Next user shell; browser calls same-origin Next API routes. | `ui-and-deployment` |
| LLM API | `8002` | Required for extraction and summarization. | `api-engine-and-cli` |
| OCR API | `8003` | Optional standalone OCR endpoint; not directly required by standard UI extraction path unless a backend pipeline uses it. | `ocr-service` |
| Agents API | `8001` | Optional workflow service; not part of process-page extraction unless explicitly deployed/integrated. | `agent-workflows` |
| Oracle DB | deployment-specific | Optional for keys, rate limits, dashboard, feedback, and LLM API logging. | UI checks config; query/schema ownership remains outside UI. |

## UI to LLM API contract boundary

The UI shells forward user-facing extraction inputs to the LLM API. Treat the following as wiring, not as backend semantics:

- File upload under form field `file`.
- `query`, either wildcard `*` or JSON object/array schema serialized as text.
- `pipeline` set to `sparrow-parse` for document extraction.
- `table`, `table_template`, and model-option augmentation for table-only extraction.
- `validation_off` marker in options when validation is disabled.
- `sparrow_key`, `client_ip`, and `country` for protected access/logging context.
- Summarization call uses `pipeline` `sparrow-instructor` and derives an instruction endpoint by replacing `/inference` with `/instruction-inference` in the configured LLM API URL.

If field meaning, valid pipeline names, model options, validation behavior, or backend error status codes are in question, route to `api-engine-and-cli`.

## Oracle DB paths by feature

Oracle DB is optional, but several UI-visible features depend on it when enabled.

| Feature | DB dependency | UI-visible symptom when unavailable |
| --- | --- | --- |
| Protected key verification | Key table lookup through the UI DB pool or backend API DB/config validation. | Invalid-key message or no anonymous access. |
| Anonymous/restricted access | PL/SQL function that obtains a rate-limited Sparrow key by client IP. | "Rate limit exceeded or no available keys" even for first-time anonymous users if DB is disabled or function fails. |
| LLM API logging | API-side inference log insertion and duration update. | Dashboard has no data or success/duration metrics are incomplete. |
| Dashboard | Reads inference logs and unique-user country aggregates. | Empty dashboard when DB disabled; server-side action/pool errors when DB enabled but unreachable/misconfigured. |
| Feedback | Inserts email/body into feedback storage. | Feedback form validation passes but submission returns failure. |
| GeoIP country | Optional GeoIP database maps IP to country before logging/display. | Country becomes `Unknown`; extraction should still work. |

Important distinction: dashboard data is created mainly by LLM API logging during inference. A dashboard rendering issue can therefore originate from API logging, Oracle configuration, or Next/Gradio rendering. Use the troubleshooting decision tree before changing UI components.

## Startup order

1. Start Oracle DB first only if protected anonymous keys, dashboard data, feedback persistence, or API logging are required for the deployment.
2. Start the LLM API and verify it answers its documentation endpoint or service-root endpoint before launching UI inference tests.
3. Start optional OCR and agents services only if the deployment explicitly needs their workflows. Their service-health details belong to their owner skills.
4. Start one UI shell. Running Gradio and Next at the same time is useful during migration, but do not expose both publicly unless routing/proxy behavior is intentional.
5. Run one valid extraction and one intentionally invalid upload. The invalid upload should stop at the UI; the valid extraction should reach the LLM API and produce either data or a backend-owned error.

## CORS and proxy notes

- The LLM API includes permissive CORS settings, but both Gradio and Next standard paths call it server-side, so browser CORS usually appears only in custom direct-browser integrations.
- Next API routes return newline-delimited JSON chunks with periodic `processing` heartbeats and a final `done` or `error` chunk. Reverse proxies must avoid buffering these routes; otherwise the browser may show a long hang despite server progress.
- Keep proxy body limits above the UI cap. The UI rejects files above `5 MB`, and the Next server-action limit is `6mb`; a proxy below those values causes confusing upstream failures.
- Align public URLs and internal ports. A common local shape is browser -> UI on `3000` or `7861`, UI -> LLM API on `8002`, optional agents on `8001`, optional OCR on `8003`.

## Deployment smoke checks

Use these checks as UI/deployment probes. Do not treat them as backend model-quality validation.

```bash
# Package metadata only; no npm install.
python scripts/ui_config_check.py --package-json <next-package.json>

# Print expected package scripts and dependency groups.
python scripts/ui_config_check.py --embedded
```

Manual probes:

1. Open the process page and upload a deliberately unsupported file extension. Expect an immediate local validation message and no backend traffic.
2. Stop or mispoint the LLM API, then upload a valid small image/PDF. Expect the UI to enter running/submitting state and then report backend connection/status failure.
3. Enable database-backed features in a staging configuration and verify: key validation path, anonymous restricted-key assignment, one dashboard time-period load, and one feedback submission.
4. For Next behind a proxy, trigger a long request and confirm heartbeat chunks are not buffered until completion.

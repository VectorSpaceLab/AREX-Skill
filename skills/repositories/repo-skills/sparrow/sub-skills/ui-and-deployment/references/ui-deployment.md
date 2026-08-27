# UI deployment reference

This reference covers Sparrow's user-facing shells: a Gradio shell and a Next shell. It is about operating and deployment wiring only; route backend API semantics to `api-engine-and-cli`, OCR internals to `ocr-service`, and agent workflows to `agent-workflows`.

## Shell choice

### Gradio shell

Use the Gradio shell when the deployment is a single Python UI process that directly calls the LLM API.

Responsibilities distilled from the source:

- Process page: accepts document uploads, schema/wildcard queries, model choice, table-only extraction, validation toggle, optional Sparrow key, and result summarization.
- Dashboard page: reads usage and performance aggregates from optional Oracle-backed inference logs.
- Feedback page: validates email/body locally and persists feedback through the optional Oracle database pool.
- Navigation: process, dashboard, and feedback are mounted in one Gradio app.
- Runtime cleanup: copied inference inputs are deleted after each backend call; a background Gradio temp cleaner periodically removes stale Gradio cache entries.
- Default launch shape: binds to all interfaces on port `7861`, queues requests with API access closed, disables analytics, and starts/stops database pool and temp cleaner around app lifetime.

Common Gradio run command from the shell directory:

```bash
python app.py
```

Required Python-side UI packages include Gradio, GeoIP lookup, Oracle DB access, PDF page counting, and Plotly dashboard rendering. Installing and validating the Python environment belongs to the broader repo-skill environment flow; from this sub-skill, verify only that the UI dependencies match the intended shell.

### Next shell

Use the Next shell when the deployment is a Node/React UI with server routes that proxy long-running requests to the LLM API.

Responsibilities distilled from the source:

- `/` redirects to `/process`.
- `/process` handles upload, query/schema, table-only extraction, validation toggle, model choice, optional Sparrow key, and result display/summarization.
- `/dashboard` renders KPI cards, duration/page charts, model usage, country distributions, and empty states from Oracle-backed action data.
- `/feedback` validates email/body and calls server-side feedback persistence.
- `/api/inference` streams newline-delimited heartbeat/status chunks while server-side inference runs.
- `/api/summarize` uses the same heartbeat-streaming pattern for instruction summarization.
- Long backend calls use an Undici dispatcher with extended fetch timeouts.
- Next config raises the server-actions body size limit to `6mb`, while the UI upload gate is `5 MB`.

Package scripts expected by this sub-skill:

```bash
npm run dev
npm run build
npm run start
npm run lint
```

Do not install npm packages just to inspect configuration. From this sub-skill directory, run the bundled metadata checker first and point it at the Next package file:

```bash
python scripts/ui_config_check.py --package-json <next-package.json>
```

If no package file is available, print the embedded expectation set:

```bash
python scripts/ui_config_check.py --embedded
```

## Configuration keys

### Gradio configuration file keys

The Gradio shell reads a properties-style configuration at process startup. The operational keys are:

| Key | Purpose | Failure shape |
| --- | --- | --- |
| `backend_url` | Full LLM API inference URL used by process extraction. Summarization derives the instruction endpoint by replacing `/inference` with `/instruction-inference`. | Wrong host/port/path causes backend request failure after upload/query validation passes. |
| `backend_options_N` | Comma-separated model backend, model id, and friendly display name. The selected friendly model maps back to the backend/model pair sent to the LLM API. | Missing options falls back to a default model; wrong formatting can break model dropdown or backend options. |
| `version` | UI footer/version display. | Cosmetic unless missing config raises startup errors. |
| `use_database` | Enables Oracle database pool for keys, dashboard, feedback, and logging support where applicable. | Disabled DB yields empty dashboard and failed feedback persistence; enabled but misconfigured DB yields pool/query errors. |
| `protected_access` | Shows/key-gates Sparrow key access and free-tier logic. | With protected access and no database-backed restricted keys, anonymous users can be blocked. |
| `database.*` | Oracle user, password, host, port, and service. | Connection pool failure, dashboard empty/errors, feedback save failure, key verification failure. |

### Next environment variables

The Next shell reads deployment state from environment variables:

| Variable | Purpose | Notes |
| --- | --- | --- |
| `BACKEND_URL` | Full LLM API inference URL for server-side extraction. | Required for inference and summarization. Summarization derives `/instruction-inference` from this URL. |
| `BACKEND_OPTIONS_1`, `BACKEND_OPTIONS_2`, ... | Comma-separated backend, model id, and friendly display name. | Friendly display names must match UI selections or the server falls back to the first model option. |
| `PROTECTED_ACCESS` | Protected access is enabled unless this value is exactly `false`. | Be explicit in local/dev deployments if unrestricted access is intended. |
| `USE_DATABASE` | Enables Oracle DB access when exactly `true`. | Needed for dashboard data, feedback persistence, and anonymous restricted-key assignment. |
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_SERVICE` | Oracle connection pool settings. | Missing or wrong values appear as server-side DB errors and empty/failed dashboard or feedback actions. |
| GeoIP database file in process working directory | Optional country lookup for logging and dashboards. | Missing file degrades to `Unknown`; it should not block extraction. |

## Upload validation

### Gradio upload behavior

- UI file picker allows `.jpg`, `.jpeg`, `.png`, and `.pdf`.
- Runtime validation checks both extension and MIME family for JPEG, PNG, and PDF.
- Maximum upload size is `5 MB`; oversize files are deleted and rejected before backend inference.
- Empty file, missing file, missing query, invalid JSON schema, non-object JSON, and invalid object-array schema are rejected before a backend call.
- Table-only extraction forces wildcard query `*`, sets table flags, and appends a table OCR model option while disabling query/model controls.
- PDF page limits are enforced when protected access is active: stricter anonymous free-tier limit and higher valid-key limit.

### Next upload behavior

- Browser-side validation allows PDF, PNG, JPEG, TIFF, and WebP MIME types, with a `5 MB` size cap.
- PDF page count is detected client-side with `pdfjs-dist` and sent to server-side inference for protected-access limits.
- Non-PDF images get an object URL preview; object URLs are revoked when the file is cleared.
- The server action validates file presence, non-empty query, JSON object/array/wildcard query shape, protected access, and page limits before forwarding to the LLM API.
- Be aware of compatibility mismatch: the Next client accepts TIFF/WebP, while the Gradio shell and LLM API evidence are image/PDF oriented. If TIFF/WebP uploads pass the UI but fail downstream, either narrow the UI accept list or confirm backend support in `api-engine-and-cli`.

## Deployment checklist

1. Pick one public UI port and one LLM API endpoint. Default observed ports are `7861` for Gradio, `3000` for Next dev, and `8002` for LLM API.
2. Start the LLM API before UI inference tests. If dashboard/feedback/key limits are in scope, start and verify Oracle DB before UI tests.
3. For Next, run `python scripts/ui_config_check.py --package-json <next-package.json>` before `npm run build` or `npm run lint`.
4. For reverse proxies, disable buffering for streaming Next API routes and preserve request body limits above `5 MB`.
5. For protected deployments, decide whether anonymous free-tier access is allowed. If yes, database-backed restricted key assignment must work; otherwise users without keys will see rate-limit/no-key messages.
6. Test one invalid file type and one valid small PDF/image while the backend API is intentionally stopped. The invalid type should fail locally; the valid type should fail as backend unavailable. This separates upload gates from service connectivity.

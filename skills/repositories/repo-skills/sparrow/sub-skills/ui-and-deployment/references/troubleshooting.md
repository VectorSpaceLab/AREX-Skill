# UI and deployment troubleshooting

Use this reference to classify UI-visible failures before changing code or handing off to another Sparrow sub-skill.

## First split: local validation vs backend failure

| Symptom | Likely layer | What to check | Next action |
| --- | --- | --- | --- |
| Error appears immediately after choosing/dropping file; submit is not the deciding step. | UI upload validation. | MIME type, extension, size, browser file metadata, accept list. | Fix UI validation or user input. Do not debug the LLM API first. |
| Upload/query accepted, UI enters running state, then returns `fetch failed`, `Request failed with status`, stream `error`, or Gradio JSON error. | LLM API connectivity or API-side error. | `BACKEND_URL`/`backend_url`, host, port, endpoint path, API process status, proxy timeout. | If endpoint/field semantics are unclear, route to `api-engine-and-cli`. |
| Dashboard shows no data but extraction works. | Database/logging/dashboard path. | `USE_DATABASE`/`use_database`, Oracle pool, API logging procedures, inference log rows, selected dashboard period. | Continue below; route API logging semantics to `api-engine-and-cli` if needed. |
| Feedback validates locally but fails to submit. | Database feedback persistence. | Oracle pool configuration, feedback table/write permission, server-side action logs. | Treat as Oracle/config issue unless form validation is wrong. |
| Anonymous protected user gets no key or rate-limit message. | Restricted-key/Oracle configuration. | Protected access flag, database enabled, restricted-key function, key table, client IP extraction. | Decide if anonymous access should be disabled or DB fixed. |

## Backend API unavailable

Expected UI symptoms:

- Gradio: validation passes, then response object contains a non-200 backend status or the request raises a connection exception in the server log.
- Next: `/api/inference` or `/api/summarize` starts streaming, then returns a final error or browser console shows a fetch/stream failure.
- Both: invalid upload-type errors should still appear immediately even while the backend API is down.

Checks:

1. Confirm the UI-configured LLM API URL is the full inference URL, not just a host root, for extraction.
2. Confirm the LLM API port is reachable from the UI server process, not merely from the browser.
3. Confirm the instruction endpoint is derivable by replacing `/inference` with `/instruction-inference`.
4. If a reverse proxy is in front of the UI or API, check upstream path rewriting and timeout limits.
5. Once connectivity is proven and the backend still rejects payloads, route field semantics and endpoint status to `api-engine-and-cli`.

## Invalid upload type

Gradio and Next do not currently have identical accept lists:

- Gradio accepts JPEG, PNG, and PDF by extension and MIME family.
- Next accepts PDF, PNG, JPEG, TIFF, and WebP in browser validation.

Triage:

1. If an unsupported file is rejected before submit or before a network request, the UI is working as designed.
2. If TIFF/WebP passes Next upload validation but the LLM API rejects or mishandles it, treat it as a compatibility mismatch. Either narrow the Next accept list or verify backend support through `api-engine-and-cli`.
3. If a file has a valid extension but empty/unknown MIME, browser-side Next validation may reject it while Gradio's MIME guess may behave differently. Reproduce with a known-good PDF/PNG before debugging backend.
4. Oversize files are UI-owned: both shells enforce a `5 MB` cap, and Next allows slightly larger server-action body overhead through a `6mb` limit.

## Oracle DB dashboard, logging, and feedback

Dashboard data can fail for three different reasons:

1. **Oracle DB config/pool issue**: database access is enabled but credentials, host, port, service, native driver state, or network reachability fail. Expect server-side pool/query errors and failed dashboard/feedback/key features.
2. **API logging issue**: extraction succeeds but no inference log rows or duration updates are written. Dashboard rendering can be correct while data remains empty or incomplete. Route log-procedure semantics to `api-engine-and-cli`.
3. **UI rendering issue**: server actions return populated dashboard data, but charts/cards do not render correctly. This belongs to the Gradio or Next UI component layer.

Feature-specific checks:

- Dashboard empty with database disabled is expected behavior, not a chart failure.
- Dashboard empty with database enabled: verify selected time period, excluded countries/unknown-country filters, data extraction log type, and successful duration updates.
- Feedback failure after valid email/body: verify database enabled and feedback insert permissions.
- GeoIP database missing should degrade country to `Unknown`; it should not block extraction or feedback.

## Protected access and restricted keys

Protected access combines UI display, key validation, anonymous key assignment, and page limits.

Important behavior:

- Next protected access is on unless `PROTECTED_ACCESS` is exactly `false`.
- Gradio reads a protected-access flag from its configuration, with deployment defaults controlled by that file.
- With protected access on and no user-provided key, anonymous use depends on a database-backed restricted-key function.
- With protected access on and a user-provided key, database-backed validation should confirm the key when DB is enabled; when DB validation is disabled, deployments must be explicit about the intended trust model.
- Free-tier PDFs are limited to fewer pages than valid-key PDFs. Page-limit errors are access-policy errors, not backend API downtime.

Triage:

1. Ask whether the deployment is intended to be unrestricted, key-only, or anonymous free-tier.
2. If unrestricted, set the protected-access flag off explicitly for the active shell.
3. If key-only, ensure UI messaging does not promise anonymous free tier.
4. If anonymous free-tier, database access and restricted-key assignment must work.
5. If users see invalid key, distinguish typo/disabled key from database lookup failure by checking server logs.

## Gradio temp files

The Gradio process makes a temporary working copy for inference and deletes it in a `finally` block after the backend request completes. It also starts a cleaner thread for Gradio's own temporary cache under the system temp area.

Checks:

- If a user sees "file was removed after processing," ask them to re-upload; the previous temp file aged out or was cleaned.
- If disk fills after crashes or forced kills, stop the UI and clean stale Gradio temp cache entries according to deployment policy.
- Do not disable cleanup to work around backend failures; fix the backend URL, timeout, or file validation issue instead.
- For sensitive deployments, document temp retention expectations: copied inference files are intended to be short-lived; Gradio cache cleanup is periodic and age-based.

## Next API routes and streaming

Next `/api/inference` and `/api/summarize` stream newline-delimited JSON:

- Periodic chunk: `{ "status": "processing" }`
- Final success chunk: `{ "status": "done", "result": ... }`
- Final failure chunk: `{ "status": "error", "message": ... }`

Failure modes:

- Browser waits forever then fails: proxy buffering or timeout may suppress heartbeat chunks.
- Immediate 413/request-body error: proxy or server body limit below UI file cap.
- Final error with backend status: LLM API was reached; route semantics/status to `api-engine-and-cli` after recording status/text.
- Summary works but extraction fails, or vice versa: compare `BACKEND_URL` and derived instruction URL, model options, and protected key resolution.

Deployment fixes:

- Preserve `Content-Type: application/x-ndjson` responses and disable buffering for these routes.
- Keep idle timeouts longer than the maximum expected inference time.
- Keep body limits above `5 MB` plus multipart overhead.
- Ensure the UI server, not just the browser, can reach `BACKEND_URL`.

## npm build/lint dependency state

Run metadata checks before invoking npm scripts:

```bash
python scripts/ui_config_check.py --package-json <next-package.json>
```

Interpretation:

- Missing `dev`, `build`, `start`, or `lint` script is a package metadata problem.
- Missing `next`, `react`, or `react-dom` blocks all Next runtime work.
- Missing `pdfjs-dist` affects PDF page-count detection.
- Missing `oracledb` affects protected-key, dashboard, and feedback paths when DB is enabled.
- Missing `maxmind` affects GeoIP country lookup only.
- Missing `undici` affects long-timeout fetch dispatcher used for long inference calls.
- Missing `eslint`, `eslint-config-next`, or `typescript` affects lint/build tooling state.

If `node_modules` is absent, `npm run lint` and `npm run build` may fail even when package metadata is correct. That is dependency installation state, not a UI logic failure. This sub-skill may report it, but should not install packages unless the user explicitly asks.

## CORS and service ports

- Default local port shape: Next dev `3000`, Gradio `7861`, LLM API `8002`, agents API `8001`, OCR API `8003`.
- Standard Gradio and Next paths call the LLM API from the server side; browser CORS is usually not the cause of process-page extraction failures.
- Custom browser-to-LLM integrations may depend on the LLM API CORS policy. If CORS appears, identify whether the browser is bypassing the UI server.
- Port conflicts often appear as UI unable to connect, not as validation errors. Confirm which process owns each port before editing configs.

## Difficult synthetic usability cases

Use these as usability probes; if they are converted into formal tests, store those tests outside the runtime skill tree:

1. **Same user-visible upload failure region, different root cause**: first upload `notes.txt` while the backend is healthy, then upload a valid small PNG while the LLM API port is stopped. The first should fail locally as invalid type with no backend call; the second should reach running state and fail as backend unavailable.
2. **Dashboard attribution split**: seed or mock one path where Oracle access is disabled, one where Oracle is enabled but API logging writes no rows, and one where populated dashboard data reaches the Next action but a chart component fails. The operator should classify them as DB config, API logging, and Next rendering respectively.

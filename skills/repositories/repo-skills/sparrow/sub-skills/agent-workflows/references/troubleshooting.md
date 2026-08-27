# Agent Workflow Troubleshooting

Start with payload shape and service prerequisites. Many Sparrow Agent failures are orchestration/configuration issues rather than model-quality issues.

## Unknown agent name

Symptom:

- synchronous endpoint returns a server error with detail similar to `Agent '<name>' not found`;
- async task reaches `FAILURE` with the same error;
- `/agents` does not list the requested name.

Checks:

1. Use exact, case-sensitive names: `medical_prescriptions`, `trading`, or `bonds`.
2. Call `/api/v1/sparrow-agents/agents` on the same service instance that will execute the request.
3. For async jobs, remember that worker registration can differ from web registration. The standard worker manager registers `medical_prescriptions` and `trading`, not `bonds`.
4. If a custom agent was added, confirm it is registered in both the web process and any Celery worker process.

## Medical PDF-only and multi-page constraints

Symptoms:

- `Document must be PDF. Received: ...`;
- `Document must contain multiple pages`;
- uploaded image, text file, or one-page PDF fails before extraction.

Rules:

- The medical workflow accepts PDFs only. The check passes when `content_type` is `application/pdf` or the filename ends with `.pdf`.
- The PDF must contain more than one page.
- The uploaded bytes must be parseable as a PDF.
- Page conversion to images must be supported in the runtime.

Good request pattern:

```bash
curl -s -X POST 'http://localhost:8003/api/v1/sparrow-agents/execute/file' \
  -F 'agent_name=medical_prescriptions' \
  -F 'extraction_params={"sparrow_key":"123456"}' \
  -F 'file=@prescription.pdf;type=application/pdf'
```

If the file is valid but `total_pages_processed` is zero, check the classified page types against `page_type_to_process`.

## Sparrow backend URL and key configuration

Symptoms:

- medical extraction fails with a non-200 backend response;
- bonds risk/decision steps fail while cached search succeeds;
- `sparrow_key` KeyError or backend authorization failure;
- the agent API health route is green but workflows fail when calling Sparrow LLM.

Checks:

1. Do not confuse the agent API URL with the Sparrow LLM backend URL.
2. Medical workflows use the `backend_url` config value and call the LLM inference path.
3. Bonds workflows use `backend_url_bonds` and call the LLM instruction path.
4. Medical file requests must include `extraction_params` JSON with a `sparrow_key` string.
5. If backend routes or model options changed, route LLM API details to `api-engine-and-cli` and base extraction details to `document-extraction`.

## Malformed `extraction_params` JSON

Symptoms:

- file endpoint returns a server error with a JSON decode message;
- async file endpoint reports `Failed to submit task: ... Invalid extraction_params JSON format`;
- medical workflow later fails because `sparrow_key` is missing.

Rules:

- `extraction_params` is a form string, not nested multipart fields.
- It must parse as a JSON object.
- Quote it carefully in shell commands.
- It should include `sparrow_key` for medical workflows.

Good:

```bash
-F 'extraction_params={"sparrow_key":"123456"}'
```

Bad:

```bash
-F 'extraction_params={sparrow_key:123456}'
-F 'sparrow_key=123456'
```

Use the smoke script before calling the service:

```bash
python scripts/agent_payload_smoke.py --case medical_file
```

## Trading payload validation

Symptoms:

- `Symbols list is required`;
- `Account balance is required`;
- numeric conversion errors for `account_balance` or `risk_tolerance`.

Rules:

- Use a non-empty `symbols` list.
- Use a non-zero/truthy `account_balance` convertible to float.
- Use a `risk_tolerance` value convertible to float; keep it in the user-facing range `0` to `1` unless deliberately testing behavior outside that range.
- Do not send trading requests to `/execute/file`; use `/execute/data`.

## Tavily credential avoidance and cached bond search results

Symptoms:

- `tavily_api_key` placeholder or missing-key failure;
- network/DNS/API-rate failure during bonds search;
- nondeterministic bond decision results from changing web search summaries.

Avoidance path:

```json
{
  "agent_name": "bonds",
  "input_data": {"search_results_file": "search_results.json"}
}
```

This causes the bonds workflow to load cached enriched search results instead of calling Tavily. Use a simple basename such as `search_results.json` or `search_results_1.json`; avoid absolute paths and directory traversal.

If cached loading fails:

1. confirm the cache file exists in the runtime agent package;
2. confirm it contains top-level `enriched_positions`;
3. confirm each position has `isin`, `instrument_name`, `history_summary`, and `outlook_summary` fields;
4. retry with another available cached filename.

## Redis/Celery worker prerequisites

Symptoms:

- async submit succeeds but task stays `PENDING` forever;
- task quickly enters `FAILURE` without model activity;
- cancellation reports success but task does not stop;
- Flower shows no worker or no queues.

Checks:

1. Start Redis or set `REDIS_URL` to an accessible Redis instance.
2. Start a worker that imports the agent tasks and listens to both queues:

   ```bash
   celery -A tasks worker --loglevel=info -Q data_queue,file_queue
   ```

3. Confirm the web process and worker use the same Redis URL.
4. Confirm the worker process can import the same agent dependencies as the web process.
5. Confirm the selected async agent is registered in the worker; default worker registration excludes `bonds`.
6. For file jobs, confirm uploaded content is serializable for the configured Celery JSON serializer. Large binary uploads can be a poor fit for queue transport.

## Task polling states

Interpret `GET /task/{task_id}` as follows:

- `PENDING`: the task is queued, unknown, expired, or no worker has picked it up.
- `PROCESSING`: the worker updated task state before executing the agent.
- `SUCCESS`: the worker returned a wrapped result.
- `FAILURE`: the worker raised an exception; inspect `error`.
- other states such as `RETRY` or `REVOKED`: inspect `progress.message` for the raw Celery state.

Do not assume `PENDING` means healthy queueing. If it persists beyond expected startup time, check Redis, queue names, worker logs, and task id age.

## Cancellation semantics

`DELETE /task/{task_id}` requests Celery revocation with termination. It returns `status: "cancelled"` when the revocation request was sent, not when all downstream work is guaranteed stopped.

Practical implications:

- pending tasks are usually revoked cleanly;
- running tasks may keep executing until the worker process terminates or the underlying I/O call returns;
- external requests already sent to Sparrow LLM or Tavily may still complete server-side;
- subsequent polling may show `REVOKED`, `FAILURE`, another transient state, or no useful result depending on timing.

For workflows with expensive downstream calls, prefer validating payloads and service readiness before submitting async jobs rather than relying on cancellation.

## Endpoint selection mistakes

Common mistakes:

- sending `medical_prescriptions` to `/execute/data` without file content;
- sending `trading` to `/execute/file`;
- sending `bonds` to `/execute/file` because `/agents` reports a file-derived type;
- using async `bonds` without extending worker registration.

Preferred routing:

- `medical_prescriptions`: file endpoint;
- `trading`: data endpoint;
- `bonds`: synchronous data endpoint, with cached search when credentials should be avoided.

# Sparrow Agents API

The Sparrow Agents service exposes a FastAPI app for workflow agents under the `/api/v1/sparrow-agents` prefix. The service registers three built-in agents in the web process: `medical_prescriptions`, `trading`, and `bonds`.

Use this reference for the agent orchestration surface only. For the lower-level Sparrow LLM inference endpoints called by some agents, route to `api-engine-and-cli`. For base document extraction payloads, route to `document-extraction`.

## Service startup and discovery

Typical local startup pattern:

```bash
python api.py --port 8003
```

Common discovery routes:

```bash
curl -s http://localhost:8003/api/v1/sparrow-agents/health
curl -s http://localhost:8003/api/v1/sparrow-agents/agents
curl -s http://localhost:8003/api/v1/sparrow-agents/openapi.json
```

The OpenAPI JSON is exposed at `/api/v1/sparrow-agents/openapi.json`; interactive docs are exposed at `/api/v1/sparrow-agents/docs`.

`GET /health` returns a small status object with `status`, the registered agent names, and a `prefect_status` string. It proves the FastAPI process is reachable, not that downstream LLM backends, Redis, Celery workers, Poppler, Tavily, or model runtimes are healthy.

`GET /agents` returns each registered agent's `capabilities` and a derived `type`. The derived type is `file` when the agent advertises `document_analysis`; this is useful but not a complete endpoint compatibility guarantee. For example, `bonds` advertises document capabilities but is best invoked through the data endpoint because it loads positions internally and does not need an uploaded file.

## Synchronous data execution

Route:

```text
POST /api/v1/sparrow-agents/execute/data
Content-Type: application/json
```

Request shape:

```json
{
  "agent_name": "trading",
  "input_data": {
    "symbols": ["AAPL", "GOOGL"],
    "account_balance": 100000,
    "risk_tolerance": 0.5
  }
}
```

Response shape:

```json
{
  "flow_run_id": "timestamp-like-id",
  "status": "success",
  "result": {}
}
```

Use this endpoint when the result is needed immediately and the workflow is expected to finish quickly. The web process calls the selected agent directly through the agent manager. Unknown `agent_name` values raise an internal error with a detail similar to `Agent '<name>' not found`.

Recommended data-agent examples:

```bash
curl -s -X POST 'http://localhost:8003/api/v1/sparrow-agents/execute/data' \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_name": "trading",
    "input_data": {
      "symbols": ["AAPL", "GOOGL"],
      "account_balance": 100000,
      "risk_tolerance": 0.5
    }
  }'
```

```bash
curl -s -X POST 'http://localhost:8003/api/v1/sparrow-agents/execute/data' \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_name": "bonds",
    "input_data": {"search_results_file": "search_results.json"}
  }'
```

## Asynchronous data execution

Route:

```text
POST /api/v1/sparrow-agents/execute/data/async
Content-Type: application/json
```

Request shape is the same as synchronous data execution. The web process submits a Celery task and immediately returns:

```json
{
  "task_id": "celery-task-id",
  "status": "submitted",
  "message": "Task submitted successfully. Use GET /api/v1/sparrow-agents/task/<id> to check status."
}
```

Async data execution requires:

1. a reachable Redis broker/result backend;
2. a Celery worker that imports the Sparrow agent tasks;
3. the worker listening to `data_queue`;
4. the chosen agent registered in the worker process.

Important worker-registration quirk: the web process registers `medical_prescriptions`, `trading`, and `bonds`, but the Celery task manager registers only `medical_prescriptions` and `trading`. Synchronous `bonds` can be listed and called by the API process, but async `bonds` will fail in the worker unless the worker registration is extended.

## Synchronous file execution

Route:

```text
POST /api/v1/sparrow-agents/execute/file
Content-Type: multipart/form-data
```

Form fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `agent_name` | yes | Usually `medical_prescriptions` for file workflows. |
| `extraction_params` | no | JSON string; defaults to `{ "sparrow_key": "12345" }`. |
| `file` | yes | Uploaded file bytes plus filename and content type. |

The web process reads the upload, parses `extraction_params` with JSON decoding, constructs an internal input object containing `content`, `filename`, `content_type`, and `extraction_params`, then calls the selected agent directly.

Medical-prescription example:

```bash
curl -s -X POST 'http://localhost:8003/api/v1/sparrow-agents/execute/file' \
  -F 'agent_name=medical_prescriptions' \
  -F 'extraction_params={"sparrow_key":"123456"}' \
  -F 'file=@prescription.pdf;type=application/pdf'
```

Use a real multi-page PDF for medical prescriptions. Single-page PDFs and non-PDF uploads are rejected by the medical workflow before any extraction proceeds.

## Asynchronous file execution

Route:

```text
POST /api/v1/sparrow-agents/execute/file/async
Content-Type: multipart/form-data
```

Form fields match the synchronous file endpoint. The web process reads the upload, parses `extraction_params`, submits a Celery task to `file_queue`, and returns a `TaskResponse` with a `task_id`.

Async file execution requires Redis and a Celery worker listening to `file_queue`. The same worker-registration quirk applies: workers register `medical_prescriptions` and `trading`, not `bonds`.

Malformed `extraction_params` should be treated as a client payload error. In practice, the service may wrap this in a generic task-submission failure, so inspect the response `detail` string for JSON parse errors rather than relying only on the HTTP status code.

## Task polling

Route:

```text
GET /api/v1/sparrow-agents/task/{task_id}
```

Response shape:

```json
{
  "task_id": "celery-task-id",
  "status": "PENDING",
  "result": null,
  "error": null,
  "progress": {"message": "Task is waiting in queue"}
}
```

Common states:

| State | Meaning | Typical response fields |
| --- | --- | --- |
| `PENDING` | Redis has no finished result yet, or the task is waiting. | `progress.message` says waiting. |
| `PROCESSING` | Worker called `update_state` before running the agent. | `progress` may include `status`, `agent`, `filename`, and `progress`. |
| `SUCCESS` | Worker returned normally. | `result` contains the wrapped agent result. |
| `FAILURE` | Worker raised an exception. | `error` contains the exception text. |
| `RETRY`, `REVOKED`, or other | Celery produced another state. | `progress.message` reports the raw state. |

Poll at a moderate interval. Repeated `PENDING` usually means the worker is not running, is not listening to the right queue, cannot reach Redis, or the task id is unknown/expired.

## Task cancellation

Route:

```text
DELETE /api/v1/sparrow-agents/task/{task_id}
```

The service calls Celery `revoke(terminate=True)` and returns:

```json
{
  "task_id": "celery-task-id",
  "status": "cancelled",
  "message": "Task cancellation requested"
}
```

Cancellation is best-effort. A pending task can usually be revoked cleanly. A running task may continue until the worker termination takes effect or until the underlying I/O/model call stops. Poll the task after cancellation and expect `REVOKED`, `FAILURE`, or another Celery state depending on timing.

## Agent-side Sparrow API clients

Some agents are orchestrators around Sparrow LLM endpoints:

- `medical_prescriptions` calls the Sparrow LLM inference endpoint with multipart form data, `pipeline=sparrow-parse`, page type options, crop size, debug flags, `sparrow_key`, and image/PDF bytes.
- `bonds` calls the Sparrow LLM instruction endpoint with form-encoded `query`, `pipeline=sparrow-instructor`, options, and debug flags.
- `trading` uses a placeholder market client by default and does not require the Sparrow LLM backend unless customized.

Keep these responsibilities separate: this sub-skill helps assemble and operate the agent workflows; backend model/runtime tuning belongs to the LLM/API and document-extraction sub-skills.

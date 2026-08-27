# Agent Workflow Configuration

Sparrow Agents configuration combines a local properties file for agent behavior, environment variables for Celery/Redis, and downstream service availability for Sparrow LLM inference and optional web search.

## Agent properties

The agent service reads `config.properties` from its working directory. Keep the service process and Celery worker working directories aligned so both read the same values.

### `[settings-medical-prescriptions]`

| Key | Purpose | Operating notes |
| --- | --- | --- |
| `backend_url` | Base URL for the Sparrow LLM inference backend used by the medical workflow. | The medical client posts to `/api/v1/sparrow-llm/inference` under this base URL. |
| `page_type` | Comma-separated page types used during page classification. | Passed as the `page_type` form field for the first Sparrow Parse call. |
| `page_type_to_process` | Comma-separated subset of page types to keep after classification. | Pages outside this list are skipped. |
| `options_page_type` | Backend/model option string for page classification. | Example format is backend name followed by model id, separated by a comma. |
| `query_adjudication_table` | JSON-like query/schema for table-family pages. | Used for `adjudication_table` and `invoice_request_form`. |
| `options_adjudication_table` | Backend/model option string for table-family extraction. | Should match the backend available at `backend_url`. |
| `query_adjudication_details` | JSON-like query/schema for details-family pages. | Used for `adjudication_details`, `application_for_coverage`, and `patient_info`. |
| `options_adjudication_details` | Backend/model option string for details-family extraction. | Should match the backend available at `backend_url`. |
| `crop_size_adjudication_details` | Crop-size parameter forwarded for details extraction. | Empty crop size is used for table-family pages; this key controls details pages. |

Operational implications:

- `backend_url` must point to a running Sparrow LLM API, not the agent API itself.
- `sparrow_key` is not read from this config section; it is expected in each file request's `extraction_params` JSON.
- The medical agent requires PDF parsing and PDF-to-image conversion support in addition to Python packages.
- If `page_type_to_process` does not overlap with the page types returned by classification, the workflow can succeed with zero processed pages.

## `[settings-bonds]`

| Key | Purpose | Operating notes |
| --- | --- | --- |
| `backend_url_bonds` | Base URL for the Sparrow LLM instruction backend used by the bonds workflow. | The bonds client posts to `/api/v1/sparrow-llm/instruction-inference` under this base URL. |
| `options_bonds_instructor` | Backend/model option string for Sparrow Instructor calls. | Used for both risk analysis and sell/hold decisions. |
| `tavily_api_key` | API key for Tavily search when cached search results are not supplied. | Avoid this dependency by passing `search_results_file` in the bonds payload. |

Operational implications:

- `backend_url_bonds` is independent of the agent API URL.
- If `search_results_file` is omitted, Tavily credentials and network access are required.
- If `search_results_file` is supplied, it must name a cached search JSON file available to the agent package.
- Sparrow Instructor failures can cause risk analysis or decisions to report `failed` or `skipped` status.

## Celery and Redis settings

Async endpoints use Celery with Redis for both broker and result backend.

| Setting | Default | Meaning |
| --- | --- | --- |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker/result backend URL used by the Celery app. |
| `result_expires` | 3600 seconds | Completed results expire after one hour. |
| `task_time_limit` | 3600 seconds | Hard worker time limit. |
| `task_soft_time_limit` | 3300 seconds | Soft worker time limit. |
| `worker_prefetch_multiplier` | 1 | Worker takes one task at a time. |
| `worker_max_tasks_per_child` | 50 | Worker process is recycled after 50 tasks. |

Task routes:

| Task | Queue |
| --- | --- |
| `tasks.process_data_agent` | `data_queue` |
| `tasks.process_file_agent` | `file_queue` |

Typical async stack startup:

```bash
redis-server
celery -A tasks worker --loglevel=info -Q data_queue,file_queue
```

Optional monitoring:

```bash
celery -A tasks flower --port=5555 --basic_auth=admin:welcome1
```

## FastAPI and Prefect settings

The agent FastAPI app disables Prefect analytics in-process with `PREFECT_SERVER_ANALYTICS_ENABLED=false` before registering flows. Agent methods are Prefect flows/tasks, so local execution can emit Prefect run logs even when no separate Prefect UI is being used.

Typical API startup:

```bash
python api.py --port 8003
```

The local server binds to `0.0.0.0` and serves docs under `/api/v1/sparrow-agents/docs`.

## Python package expectations

The agent stack uses FastAPI, Uvicorn, aiohttp, Prefect, pydantic, Python multipart parsing, rich, Typer, NumPy, PDF parsing/conversion packages, Celery, Redis, Flower, and Tavily client libraries.

Medical PDF conversion may need non-Python system support for PDF-to-image conversion. If PDF uploads fail after passing schema validation, check the troubleshooting reference before debugging Sparrow LLM prompts.

## Configuration sanity checks

Before running an agent workflow:

1. Confirm the agent API is reachable with `/health`.
2. Confirm registered agents with `/agents`.
3. For medical workflows, confirm `backend_url` points to a live Sparrow LLM inference backend and the request includes `extraction_params.sparrow_key`.
4. For bonds workflows, confirm `backend_url_bonds` points to a live Sparrow LLM instruction backend.
5. For bonds smoke tests, pass `{"search_results_file": "search_results.json"}` to avoid Tavily.
6. For async workflows, confirm Redis is reachable from both web and worker processes and the worker is listening to the required queue.
7. For async bonds workflows, confirm the worker has been customized to register `bonds`; otherwise use synchronous execution.

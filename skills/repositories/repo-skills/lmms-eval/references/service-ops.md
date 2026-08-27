# Service operations

This reference covers the HTTP eval server, Python clients, MCP tooling, and the web/TUI backend.

## HTTP eval server

Start it with:

```bash
lmms-eval serve --host 0.0.0.0 --port 8000
```

Core implementation lives in `lmms_eval/entrypoints/`.

| File | Role |
| --- | --- |
| `server_args.py` | Server config object |
| `job_scheduler.py` | Queueing and subprocess execution |
| `protocol.py` | Pydantic request/response models |
| `http_server.py` | FastAPI routes |
| `client.py` | `EvalClient` and `AsyncEvalClient` |

## Server API summary

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/health` | GET | Health check |
| `/evaluate` | POST | Submit a job |
| `/jobs/{job_id}` | GET | Fetch job status/result |
| `/jobs/{job_id}` | DELETE | Cancel a queued job |
| `/queue` | GET | Queue state |
| `/tasks` | GET | Task list |
| `/models` | GET | Model list |
| `/merge` | POST | FSDP2 checkpoint merge |

## Client methods

`EvalClient` and `AsyncEvalClient` expose the same core ideas:

- `health()` / `is_healthy()`
- `list_tasks()`
- `list_models()`
- `evaluate(...)`
- `get_job(job_id)`
- `wait_for_job(job_id, ...)`
- `cancel_job(job_id)`
- `get_queue_status()`

The installed runtime exposes the following `ServerArgs` shape:

```python
ServerArgs(host='localhost', port=8000, max_completed_jobs=100, temp_dir_prefix='lmms_eval_')
```

## Job lifecycle

Queued jobs move through:

`queued -> running -> completed | failed | cancelled`

The scheduler is sequential by design so GPU-backed jobs do not overlap unexpectedly.

## MCP tooling

The MCP command starts the agent-facing interface:

```bash
lmms-eval mcp --transport stdio
```

The MCP server exposes discovery and evaluation tools such as:

- list tasks/models
- inspect task/model metadata
- submit evaluations
- poll run status / retrieve results
- cancel queued runs

If the server import fails because `mcp.server.fastmcp` is missing, that is a package-version issue, not a code bug in the repo.

## Web UI and terminal UI

- `lmms-eval ui` launches the web UI and auto-builds the frontend when needed.
- `lmms-eval tui` launches the terminal UI.
- The web UI backend is FastAPI-based and uses the discovery helpers in `tui/discovery.py`.
- The frontend requires Node.js 18+ when a build is needed.

## Operational cautions

- Treat the server as trusted-network-only unless you add authentication and isolation.
- Port conflicts are the first thing to check when startup fails.
- Queue backlogs usually mean a previous job is still running or a child process was not reaped cleanly.
- Never use a long-running production job as the first smoke test; prefer help output and a tiny local probe.

## Safe smoke checks

- `lmms-eval serve --help`
- `lmms-eval mcp --help`
- `lmms-eval ui --help`
- `python -I -c "from lmms_eval.entrypoints import ServerArgs, EvalClient"`
- `python -I -c "import lmms_eval.tui.server, lmms_eval.mcp.server"`

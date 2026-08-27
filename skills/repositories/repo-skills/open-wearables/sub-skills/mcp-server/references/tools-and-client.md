# MCP Tools and API Client

## Purpose

Read this when adding, reviewing, or debugging Open Wearables MCP tools. It distills the FastMCP server entry point, mounted tool routers, REST API client contract, prompt, test strategy, and error-envelope behavior so a future agent does not need to reopen the source tree.

## Runtime Shape

- Package distribution: `open-wearables-mcp` version `0.1.0`.
- Python requirement: `>=3.13`.
- Dependencies: `fastmcp`, `httpx`, `pydantic`, and `pydantic-settings`.
- Console script: `start` resolves to `app.main:main` and runs a FastMCP server named `open-wearables` over stdio.
- Routers mounted at startup: users, activity, sleep, workouts, timeseries, and prompts.
- The MCP server is decoupled from the backend. It talks to the backend REST API with `X-Open-Wearables-API-Key`; it does not share database sessions or backend internals.

## API Client Contract

`OpenWearablesClient.__init__(self) -> None` reads settings at construction time:

| Setting | Meaning | Runtime behavior |
| --- | --- | --- |
| `OPEN_WEARABLES_API_URL` | Base backend API host, defaulting to `http://localhost:8000` | Trailing slash is stripped; client appends API paths such as `/api/v1/users`. |
| `OPEN_WEARABLES_API_KEY` | Backend API key | Sent as `X-Open-Wearables-API-Key`; missing keys fail before network calls. |
| `REQUEST_TIMEOUT` | HTTP timeout in seconds | Passed to `httpx.AsyncClient(timeout=...)`. |

Important methods and paths:

| Client method | Backend path | Parameters |
| --- | --- | --- |
| `get_users(search=None, limit=100)` | `GET /api/v1/users` | `limit`, optional `search` |
| `get_user(user_id)` | `GET /api/v1/users/{user_id}` | user UUID |
| `get_activity_summaries(user_id, start_date, end_date, limit=100)` | `GET /api/v1/users/{user_id}/summaries/activity` | dates as `YYYY-MM-DD`, page limit |
| `get_sleep_summaries(user_id, start_date, end_date, limit=100)` | `GET /api/v1/users/{user_id}/summaries/sleep` | dates as `YYYY-MM-DD`, page limit |
| `get_workouts(user_id, start_date, end_date, record_type=None, limit=100)` | `GET /api/v1/users/{user_id}/events/workouts` | dates, optional workout record type, page limit |
| `get_timeseries(user_id, start_time, end_time, types, resolution="raw", limit=100, cursor=None)` | `GET /api/v1/users/{user_id}/timeseries` | ISO-8601 times, list of series type codes, resolution, page limit, optional cursor |

Client error mapping:

| Backend/config signal | Client exception | Tool-level behavior |
| --- | --- | --- |
| Missing `OPEN_WEARABLES_API_KEY` | `ConfigurationError` before HTTP | Tool returns an `error` envelope. `get_users` also returns `users: []` and `total: 0`. |
| HTTP 401 | `AuthenticationError("Invalid API key...")` | Tool returns an `error` envelope mentioning invalid key. |
| HTTP 404 | `NotFoundError("Resource not found: <path>")` | Summary/timeseries tools return `User not found: <uuid>` when the lookup is what failed; other 404s become generic errors. |
| HTTP 5xx, timeout, DNS, refused connection, malformed JSON | `httpx`/generic exception | Tool returns `Failed to fetch ...` with the underlying error text. |

## Tool Catalog

| MCP tool | Signature | Use when | Backend calls | Output envelope |
| --- | --- | --- | --- | --- |
| `get_users` | `(search: str | None = None, limit: int = 10) -> dict` | Discover accessible users before calling health-data tools; narrow large orgs by name/email. | `GET /api/v1/users` | `users` list with `id`, `first_name`, `last_name`, `email`; `total`; optional `error`. |
| `get_activity_summary` | `(user_id: str, start_date: str, end_date: str) -> dict` | Daily steps, distance, active/total calories, active/sedentary minutes, heart-rate summary, intensity minutes, floors/elevation. | `GET /api/v1/users/{id}` then `/summaries/activity` | `user`, `period`, `records`, `summary`, or `error`. |
| `get_sleep_summary` | `(user_id: str, start_date: str, end_date: str) -> dict` | Sleep nights in a date range: start/end times, duration, provider source, aggregate duration stats. | `GET /api/v1/users/{id}` then `/summaries/sleep` | `user`, `period`, `records`, `summary`, or `error`. |
| `get_workout_events` | `(user_id: str, start_date: str, end_date: str, workout_type: str | None = None) -> dict` | Discrete workouts such as running/cycling/swimming/strength training with duration, distance, calories, pace, HR, elevation. | `GET /api/v1/users/{id}` then `/events/workouts`; `workout_type` maps to client `record_type`. | `user`, `period`, `records`, `summary`, or `error`. |
| `get_timeseries` | `(user_id: str, start_time: str, end_time: str, types: list[str], resolution: str = "raw") -> dict` | Granular samples such as weight, SpO2, HRV, intraday heart rate, respiratory rate, glucose, blood pressure, steps, or energy. | `GET /api/v1/users/{id}` then paginated `/timeseries` | `user`, `period`, `records`, `summary`, `truncated`, or `error`. |

### Date and Time Expectations

- `get_activity_summary`, `get_sleep_summary`, and `get_workout_events` require `start_date` and `end_date` in `YYYY-MM-DD` form.
- `get_timeseries` requires `start_time` and `end_time` in ISO-8601 form, for example `2026-04-05T00:00:00Z`.
- The tools do not infer dates for the caller. The server instructions tell the assistant to default to the last 2 weeks when the user gives no time period.
- Sleep record `date` is based on wake/end date. A sleep period often starts the prior calendar day.
- Prefer `get_activity_summary` for daily heart-rate/steps questions. Use `get_timeseries` when the user needs intraday samples or metrics not exposed by a summary tool.
- For multi-day timeseries, prefer `resolution="1min"` or coarser unless the user explicitly needs raw samples.

### Timeseries Pagination Safety

`get_timeseries` walks cursor pagination internally with a hard ceiling of 100 pages. With the client default page size of 100, one tool call can return up to about 10,000 samples. If the ceiling is hit, the tool returns `truncated: true`; guide the user to narrow the time window, reduce the `types` list, or use a coarser `resolution`.

## Prompt Presentation

The server mounts a prompt named `present_health_data() -> list[PromptMessage]`. Use it when formatting health results for people:

- Lead with insights, not raw dumps.
- Format steps, distance, calories, duration, heart rate, and percentages with units.
- Convert meters to kilometers for presentation; convert minutes to hours/minutes when useful.
- Highlight patterns such as best/worst days, trends, and notable changes.
- Keep source/provider differences visible when they matter.

## Adding or Changing a Tool

1. Decide whether the backend endpoint already exists. If it does not, route the endpoint work to [backend-core](../../backend-core/SKILL.md) before changing MCP behavior.
2. Add or update an `OpenWearablesClient` method with a small typed signature, the exact backend path, and parameter names that match the backend API.
3. Add an async FastMCP tool on an existing router or a focused new router. Tool names are the public MCP contract; choose stable snake_case names.
4. For user-scoped health data, fetch `get_user(user_id)` first and return `{"error": "User not found: <uuid>", "details": ...}` if that lookup returns 404.
5. Transform backend paginated payloads into compact MCP envelopes. Avoid leaking backend pagination internals unless they are needed, as with timeseries truncation.
6. Catch `OpenWearablesError` for expected configuration/auth/not-found failures and catch generic exceptions for HTTPX/5xx/network cases. Return error dictionaries instead of bubbling raw exceptions to the assistant client.
7. Mount any new router in the server entry point and update the server instructions so assistants know when to use it.
8. Update assistant-facing references and add mocked tests. Native MCP tests invoke FastMCP `FunctionTool.fn(...)` with `pytest-httpx` responses; they should not call a live backend.

## Test and Review Hooks

- Native MCP candidates after whole-skill integration: `uv run pytest -q` from the MCP package directory.
- Focused client cases: missing key raises `ConfigurationError`, 401 raises `AuthenticationError`, 404 raises `NotFoundError`, and all typed errors inherit from `OpenWearablesError`.
- Focused tool cases: `get_users` returns an empty user envelope on auth errors; summary/timeseries tools return the `User not found` envelope on user-lookup 404; downstream 401/5xx become generic `error` envelopes.
- Safe preflight before a live assistant test: run `scripts/check_mcp_config.py` from this sub-skill to validate local config shape and importability without making API requests.

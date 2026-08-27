# MCP Troubleshooting

## Purpose

Use this reference when the MCP server starts but tools fail, assistant clients cannot see tools, or health-data requests return confusing error envelopes. The default diagnostic path avoids live API calls until credentials and backend target are intentionally provided.

## First Safe Checks

```bash
python <skill-root>/sub-skills/mcp-server/scripts/check_mcp_config.py \
  --mcp-root <open-wearables-checkout>/mcp \
  --env-file <open-wearables-checkout>/mcp/config/.env
```

Then verify the local server command from the MCP package directory:

```bash
uv run start
```

Stop the server after it initializes unless an assistant client is supposed to own the stdio process.

## Failure Matrix

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `OPEN_WEARABLES_API_KEY is not configured` or startup warning about missing key | `.env` was not created, the wrong package directory is being used, the key variable is blank, or a placeholder was left in place. | Copy the env template to `config/.env`, set `OPEN_WEARABLES_API_KEY` to a real key only on the operator machine, run the bundled checker, then restart the assistant client. |
| `Invalid API key` or HTTP 401 | Key is wrong, revoked, scoped to the wrong app/user/team, or the backend is reading a different credential than expected. | Regenerate/check the key through the Open Wearables credential UI or backend developer API-key workflow. If the backend auth contract changed, route that work to [backend-core](../../backend-core/SKILL.md). |
| `Connection refused`, `ConnectError`, `Failed to fetch users`, or timeout before HTTP status | Backend is not running, the API URL points to the wrong host/port, Docker services are still starting, or network access is blocked. | For local development, start the backend stack and wait for readiness. Confirm `OPEN_WEARABLES_API_URL` is an API base URL such as `http://localhost:8000`. Increase `REQUEST_TIMEOUT` only for slow but reachable backends. |
| `Resource not found: /api/v1/users` or HTTP 404 on users | API URL points to the frontend/dashboard instead of the backend API, the backend route prefix changed, or the deployed backend is an incompatible version. | Set `OPEN_WEARABLES_API_URL` to the backend API host, not a portal URL. If routes changed, coordinate with [backend-core](../../backend-core/SKILL.md) and update the MCP client paths/tests. |
| `User not found: <uuid>` | The selected UUID is not accessible through the API key or no longer exists. | Call `get_users` again, use `search` to match by name/email, and only pass returned IDs to health-data tools. |
| HTTP 5xx wrapped as `Failed to fetch ...` | Backend error, dependency outage, malformed backend response, or unhandled MCP client path. | Check backend logs and route endpoint/service defects to [backend-core](../../backend-core/SKILL.md). Keep MCP tests mocked unless the user explicitly wants a live repro. |
| Assistant client shows no Open Wearables tools | Claude/Cursor config JSON is in the wrong file, the client was not restarted, `uv` is not on the assistant process PATH, or the `--directory` argument points away from the MCP package. | Validate the JSON, restart the assistant, use the full local path to `uv` if needed, and ensure the command runs `uv run --frozen --directory /path/to/open-wearables/mcp start`. |
| Import errors mention the wrong `app` package | The backend and MCP packages both use top-level module name `app`; the Python path points at the backend package while running MCP checks. | Run MCP commands from the MCP package directory or pass `--mcp-root <open-wearables-checkout>/mcp` to the bundled checker. Avoid mixing backend and MCP package imports in one ad hoc Python process. |

## No Users Found

`get_users` can legitimately return `{"users": [], "total": 0}` with no error. Diagnose it differently from 401/404:

1. Confirm the API key is valid and scoped to users the operator expects to access.
2. If this is a fresh local stack, create/seed users through the backend workflow before testing MCP queries.
3. If multiple users exist, use `get_users(search="name-or-email-fragment")` instead of raising the `limit` blindly.
4. If the assistant asks about `my` data and multiple users are returned, ask the human which user to select; do not guess.

## Date-Range and Time-Range Issues

The server instructions define assistant-side defaults; the tools themselves still require explicit arguments.

- If the user provides no date range for activity, sleep, or workouts, default to the last 2 weeks: `start_date = today - 14 days`, `end_date = today`.
- For `last week`, calculate a 7-day window unless the user expects calendar-week semantics; if ambiguous, clarify.
- Use `YYYY-MM-DD` for `get_activity_summary`, `get_sleep_summary`, and `get_workout_events`.
- Use ISO-8601 timestamps for `get_timeseries`, for example `2026-04-05T00:00:00Z` to `2026-04-05T23:59:59Z`.
- Sleep `date` means the wake/end date, not necessarily the bedtime date.
- Raw multi-day timeseries can be large. Prefer `resolution="1min"`, `"5min"`, `"15min"`, or `"1hour"` for broad windows; if `truncated: true`, narrow the window or type list.

## 401 vs 404 vs 5xx Decision Tree

1. Missing or placeholder key before a request: fix `OPEN_WEARABLES_API_KEY` locally.
2. HTTP 401 from backend: key reached the backend but was rejected; check credential validity/scope.
3. HTTP 404 on `/api/v1/users`: likely wrong API base URL or route mismatch.
4. HTTP 404 on `/api/v1/users/{user_id}`: selected user is invalid or inaccessible; call `get_users` again.
5. HTTP 5xx or transport error: backend/service/network issue; do not paper over it in MCP unless the MCP client path or error mapping is wrong.

## When Updating Code

- Preserve the error-envelope convention: assistant-facing tools should return dictionaries with `error` fields for expected failures.
- Add mocked HTTPX tests for every new path, including at least one auth/not-found failure path.
- Keep backend route implementation and data semantics in [backend-core](../../backend-core/SKILL.md); MCP should adapt the REST contract, not redefine it.
- Update [tools-and-client.md](tools-and-client.md) whenever a public MCP tool name, parameter, output envelope, or backend path changes.

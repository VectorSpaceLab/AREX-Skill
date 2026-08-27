# Auth and Troubleshooting

## Authentication modes

### stdio
- Requires `AIRWEAVE_API_KEY` and `AIRWEAVE_COLLECTION`.
- `AIRWEAVE_BASE_URL` is optional.
- Missing either required variable should fail fast with a clear config error.

### HTTP API-key mode
- Accepts `X-API-Key`.
- Accepts `Authorization: Bearer <api-key>`.
- `X-API-Key` takes priority if both headers are present.
- Bearer parsing is case-insensitive for the scheme.

### HTTP OAuth mode
- Enabled with `MCP_OAUTH_ENABLED=true`.
- Requires the Auth0 and MCP base URL settings documented in the overview.
- A valid JWT bearer token takes the OAuth path.
- A structurally valid JWT that fails verification returns a `401` JSON-RPC error that tells the client the token is expired or invalid.
- A bearer value that is not a JWT falls back to API-key handling when OAuth verification fails.

## Organization resolution

OAuth requests resolve the organization for the selected collection before the MCP server is created:

1. List organizations for the user.
2. Probe each organization for the target collection.
3. Cache the winning organization id for a short period.

If the collection cannot be found, the server returns a readable `400` with the organization list it checked. If the user belongs to no organizations, it returns a clear error instead of hanging.

## Readable failure messages to expect

- Missing API key.
- Missing collection.
- Authentication required.
- Token expired or invalid.
- Organization resolution failed.
- Collection not found in any organization.
- Airweave API error with HTTP status details.
- Redis connection failed when OAuth auth state cannot start.

## Metrics and health clues

- `GET /health` should show the transport, protocol, and mode.
- `GET /metrics` should expose both default Node metrics and the MCP counters/histograms.
- `POST /mcp` without auth should fail with a clear JSON-RPC error instead of a transport hang.

## Practical troubleshooting order

1. Check the env vars or headers for the selected mode.
2. Run `scripts/mcp-smoke.sh` to verify build, tests, and entrypoints.
3. Confirm `get-config` and `tools/list` on HTTP before trying search.
4. For OAuth issues, verify the Auth0 and Redis settings before debugging search behavior.

## Dashboard cross-link

Only switch to `frontend-dashboard` when a dashboard flow changes how the user obtains the API key, collection readable id, or auth context for MCP setup.

# API, MCP, and Web Troubleshooting

## 401 vs 403

- `401`: authentication failed or no recognized credential was provided.
- `403`: credential was accepted but lacks the required permission.

For API keys, verify whether the request uses `X-API-Key` or
`Authorization: Bearer <key>`. For global keys, confirm Community singleton
Workspace mode and non-empty `api.global_api_key`.

## Route Exists in Source but Returns 404

- Confirm the module containing the route group is imported by the controller
  preregistration path.
- Confirm the group class decorator base path and route rule combine as
  expected.
- Use the bundled route extractor to inspect static registration.
- Confirm the request path is not swallowed by SPA fallback for non-API paths.

## MCP Tool Missing

- Check that the tool is registered in `LangBotMCPServer._register_tools()`.
- Make sure it is a curated public agent operation, not an internal-only HTTP
  route.
- Restart/reinitialize the MCP mount after code changes.
- Use the manual MCP smoke for transport/auth/tool-listing checks.

## Web UI Cannot Reach Backend

- Confirm dev `VITE_API_BASE_URL` and backend `api.port`.
- Check CORS only after base URL and auth are correct.
- Ensure the backend process is not serving stale built assets when testing
  frontend source changes.

## Public Webhook/Embed Auth Confusion

`/bots/<uuid>` and selected embed assets are public at the HTTP route layer.
Security belongs in the adapter's signature scheme or widget/bot config. Do not
add user-token auth to vendor webhook routes unless redesigning the adapter
contract.

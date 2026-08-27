# API Route and MCP Surface Extraction

LangBot registers HTTP route groups with `@group.group_class(name, path)` and
nested `self.route(...)` calls. The MCP server registers a curated tool set in
`LangBotMCPServer._register_tools()` using `@mcp.tool`.

Use the bundled route extractor when a task needs a fresh route inventory:

```bash
python scripts/extract_langbot_routes.py --repo-root /path/to/LangBot --format markdown
python scripts/extract_langbot_routes.py --repo-root /path/to/LangBot --format json
```

## Route Auth Model Summary

- `NONE`: public endpoint.
- `ACCOUNT_TOKEN`: account-level token without Workspace permission checks.
- `USER_TOKEN`: web UI JWT and Workspace context.
- `API_KEY`: API key only.
- `USER_TOKEN_OR_API_KEY`: browser JWT or API key.

Permissions such as `RESOURCE_VIEW`, `RESOURCE_MANAGE`, `RUNTIME_OPERATE`,
`PROVIDER_SECRET_MANAGE`, `API_KEY_MANAGE`, `AUDIT_VIEW`, and `DATA_EXPORT` are
checked after authentication when the route declares them.

## MCP Tool Surface Summary

The current MCP server exposes system info plus resource operations for bots,
pipelines, LLM/embedding models, providers, knowledge bases, external MCP
servers, and installed skills. Tools call service classes directly rather than
HTTP round-tripping.

When a new HTTP endpoint should be agent-accessible:

1. Add or update the HTTP route and service logic.
2. Add or update the MCP tool in the MCP server.
3. Update the relevant skill/reference route when the public agent contract
   changes.
4. Add focused API/MCP tests.

Do not expose every internal route through MCP by default. Keep the MCP surface
small, permission-scoped, and service-layer aligned.

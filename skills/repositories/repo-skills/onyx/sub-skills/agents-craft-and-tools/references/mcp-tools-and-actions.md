# MCP tools and actions

## Runtime server surface

- The MCP server runs over HTTP with FastMCP + FastAPI.
- Clients authenticate with an Onyx personal access token or API key in the `Authorization: Bearer ...` header.
- Authentication is delegated to the API server's `/me` check.
- The default tool surface is:
  - `search_indexed_documents`
  - `search_web`
  - `open_urls`
- The default resource surface includes `indexed_sources`.

## What each tool is for

- `search_indexed_documents`: use for private, indexed Onyx knowledge.
- `search_web`: use for public web search results and snippets.
- `open_urls`: use to fetch full text from URLs you already trust or that came from search results.
- `indexed_sources`: use it to discover valid source filters before querying private indexed search.

## Client and admin flows

- The backend MCP admin flow manages server records, connection configs, tool discovery, OAuth, and user-specific credentials.
- `resolve_craft_mcp_servers` filters the session-visible MCP servers to only the ones the user can access and authenticate.
- Disabled tools are still tracked per server, so session config can hide or deny them explicitly.
- `craft_mcp_fingerprint` changes whenever the server set, URLs, or disabled-tool sets change. That fingerprint is what tells Craft sessions to refresh.
- Build sessions inject MCP servers into the per-session OpenCode config with session-scoped headers so the proxy can attribute tool calls correctly.

## Tool visibility and external apps

- Tool visibility is a backend concern, not just a UI concern.
- If a tool or external app should not be exposed, keep it out of the resolved server/tool set and keep the backend ACLs aligned.
- Custom tools and external apps should always be reachable only through the server-side auth and visibility checks that already exist.
- When a build session needs to see a new MCP server, the session config must be regenerated so the runtime picks up the new tool set.

## Security and SSRF

- Never trust a stored server URL or OAuth metadata URL without validation.
- All outbound MCP HTTP hops are guarded by the SSRF transport wrapper, including redirects.
- OAuth discovery, token exchange, and redirect hops are all subject to the same outbound URL validation.
- `open_urls` should not be repurposed as a generic arbitrary fetch API.
- Keep bearer tokens and refreshed `Authorization` headers server-side; do not expose them to the client.
- If an MCP server starts failing only after auth changes, confirm whether the problem is bearer auth, OAuth state, token refresh, or SSRF blocking.

## When to read this reference

Read this before changing MCP server endpoints, MCP client plumbing, OAuth connect/callback code, tool exposure rules, or any flow that fetches remote URLs on behalf of the user.

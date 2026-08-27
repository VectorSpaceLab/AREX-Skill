# Transport and Tools

## Tool surface

The MCP server registers two tools per configured collection:

1. `search-<collection>`
2. `get-config`

The collection name is part of the search tool name, so clients should always inspect `tools/list` or `get-config` before invoking a search.

## Search tool behavior

### Parameters
- `query` — required text query.
- `tier` — `instant`, `classic`, or `agentic`.
- `retrieval_strategy` — only meaningful for `instant`.
- `limit` — result cap.
- `offset` — pagination offset.
- `thinking` — optional agentic toggle.
- `filter` — structured filter groups, with OR across groups and AND within a group.

### Tier notes
- `instant` is the fastest path and maps to direct retrieval.
- `classic` is the default tier.
- `agentic` enables deeper multi-step search and can use `thinking`.

### Output
- Success responses are Markdown-like text blocks with the collection, tier, score, breadcrumbs, content, and links.
- Validation errors are returned as readable parameter messages.
- Backend and network failures are surfaced as readable error text with debugging hints.

### Mock-friendly local path
When the API key is `test-key` and the base URL points at localhost, the client returns deterministic mock search results. The smoke helper uses this path so the server can be exercised without a live Airweave backend.

## Config tool behavior

`get-config` returns:
- collection id
- base URL
- whether an API key is configured
- the search tool name shown in the available-commands text

Use it as the first sanity call after `tools/list`.

## Collection handling

- In stdio mode, collection selection is fixed at startup by `AIRWEAVE_COLLECTION`.
- In HTTP mode, the request can override the default with `X-Collection-Readable-ID`.
- If no collection source is available in HTTP mode, the server returns a guidance message instead of creating the MCP server for that request.

## Search semantics boundary

For the search route contract, collection filtering, and backend result semantics, switch to the `backend-api` sub-skill instead of expanding this transport layer note.

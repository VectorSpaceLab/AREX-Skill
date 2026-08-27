# MCP Server Overview

This sub-skill covers the Strands Agents MCP server package: a FastMCP stdio server that exposes curated documentation lookup through `search_docs` and `fetch_doc`. It is for agents modifying or debugging the server package itself, not for Python SDK MCP client implementation details or docs-site content editing.

## Canonical facts

| Item | Value |
| --- | --- |
| Distribution | `strands-agents-mcp-server` |
| Verified package version | `0.2.9` |
| FastMCP app name | `strands-agents-mcp-server` |
| Console entry point | `strands-agents-mcp-server` |
| Server entry point | `strands_mcp_server.server:main` |
| Public MCP tools | `search_docs(query: str, k: int = 5)` and `fetch_doc(uri: str = "", section: str = "")` |
| Default catalog source | `https://strandsagents.com/llms.txt` |
| Allowed document host | exactly `https://strandsagents.com` |
| Small-document threshold | `8192` bytes |
| Search snippet hydration cap | top `5` unique ranked URLs |
| Prefetch environment variable | `STRANDS_MCP_PREFETCH_ALL` truthy values: `1`, `true`, `yes` |

## Owned behavior

- Startup initializes a title-only documentation catalog from curated `llms.txt` links.
- Search is title-first and hydration-sensitive: title-like queries work immediately after catalog load; body-only terms work after a page has been fetched or background-prefetched.
- Search results contain `url`, `title`, `score`, and `snippet`; scores are unbounded TF-IDF ordering values, not probabilities.
- Fetch supports catalog mode, TOC mode, section mode, and small-document full-content mode.
- Fetch rejects non-HTTPS URLs and any host other than exactly `strandsagents.com`.
- Cache hydration updates the search index before committing a fetched page to cache, so transient indexing failures remain retryable.
- Offline unit tests patch network-facing pieces; live integration tests intentionally access `strandsagents.com` and can be skipped.

## Boundaries and routing

Use this sub-skill for MCP server packaging, server launch, `search_docs`/`fetch_doc`, llms catalog parsing, cache/prefetch behavior, snippets, section parsing, URL validation, and the server's test strategy.

Route elsewhere when the request is about:

- MCP clients in the Python SDK, transport adapters, or `MCPClient` usage by agents.
- Docs site MDX pages, `sourceLinks`, Astro catalog generation, or site navigation metadata.
- Provider/model integration tests that require credentials rather than documentation-server behavior.

## Fast checks

- Use [../scripts/mcp-smoke.sh](../scripts/mcp-smoke.sh) when the package is installed in the active environment and you need an import/entry-point smoke without network fetches.
- Use [../scripts/mcp-unit-check.sh](../scripts/mcp-unit-check.sh) from a compatible checkout when you need the server's selected offline pytest suite.

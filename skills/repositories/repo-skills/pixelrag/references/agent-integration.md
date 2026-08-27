# Agent Integration

## Hosted search API

PixelRAG exposes an HTTP search API that agents can call with text or image queries. Minimal tool behavior:

1. POST `/search` with `queries: [{"text": "..."}]` and `n_docs`.
2. Use hit `url`, score, and tile coordinates to decide whether more context is needed.
3. Fetch images by `/tile/{article_id}/{tile_index}/{chunk_index}` only when the reader needs visual evidence.
4. Keep `include_images` false for broad searches to avoid huge payloads.

## Agent tool shape

A lightweight search tool can expose:

```json
{
  "query": "natural language search query",
  "n_results": 5
}
```

Internally it posts:

```json
{"queries": [{"text": "..."}], "n_docs": 5}
```

Return concise hit summaries: title/url, score, article ID, tile/chunk coordinate.

## pixelbrowse / Claude plugin

PixelRAG also ships a Claude Code plugin concept (`pixelbrowse`) that gives an agent visual page capture through `pixelshot`. This repo skill does not install or export cross-agent plugins. For an ordinary package workflow, ensure `pixelshot` is on `PATH` (for example with `uv tool install pixelrag` or `pipx install pixelrag`) and let the agent call the CLI.

## When to use capture vs search

- Use `render-capture` when the user gives a URL/document and wants to see or tile it.
- Use `serve-search` when the user asks to find relevant information in an existing visual index.
- Use `index-build` when the user has a document collection that must become searchable.

## Safety and privacy

- Do not log private queries or screenshots unless the user permits it.
- Do not embed credentials in tool definitions.
- For authenticated screenshots, use a user-controlled CDP endpoint and avoid closing the browser.
- Keep hosted API URLs and local ports configurable.

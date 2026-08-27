---
name: serve-search
description: "Use PixelRAG serve and search APIs for FAISS or Qdrant visual
  retrieval indexes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PixelRAG Serve Search

Use this sub-skill when the task is to run `pixelrag serve`, query a PixelRAG search endpoint, debug search results, choose FAISS/Qdrant serving options, or integrate PixelRAG search into an agent.

## Start Here

1. Ensure an index exists. If not, use `../index-build/SKILL.md`.
2. Start the API:

   ```bash
   pixelrag serve --index-dir ./index --articles-json ./index/articles.json --tiles-dir ./index/tiles --port 30001
   ```

3. Check readiness:

   ```bash
   curl -s http://localhost:30001/health
   curl -s http://localhost:30001/status
   ```

4. Query:

   ```bash
   curl -s -X POST http://localhost:30001/search \
     -H "Content-Type: application/json" \
     -d '{"queries":[{"text":"overview diagram"}],"n_docs":5}'
   ```

## Read or Run

- Read [api-reference.md](references/api-reference.md) for request/response fields and endpoints.
- Read [index-layout-and-backends.md](references/index-layout-and-backends.md) for FAISS, Qdrant, tile paths, departments, and memory mapping.
- Read [troubleshooting.md](references/troubleshooting.md) for server startup, backend, model, tile, and query errors.
- Run [pixelrag_search_smoke.py](scripts/pixelrag_search_smoke.py) to check `/health`, `/status`, and optionally a text query.

## Common Routes

| Request | Action |
| --- | --- |
| "Serve this local index" | Use `pixelrag serve --index-dir ... --articles-json ... --tiles-dir ...`. |
| "Search and include tile images" | POST `/search` with `include_images: true`; watch payload size. |
| "Use Qdrant" | Start with `--backend qdrant --qdrant-url ... --collection ...`, or let `summary.json` infer backend. |
| "Filter by department" | Call `/departments`, then pass `department` in `/search`; departments come from local-source subdirectories. |
| "Use precomputed embeddings" | Send `queries: [{"embedding": [...]}]` and do not mix with text/image queries in the same request. |
| "Render missing tiles on demand" | Use `--render-on-demand --kiwix-url ...` for Kiwix-backed indexes; expect slower first queries. |

## Safety Defaults

- Do not launch a long-running server without user approval in restricted sessions.
- Do not download models or indexes implicitly; serving loads the query encoder for text/image queries.
- Do not expose filesystem paths from server responses to end users; PixelRAG returns relative tile paths and `/tile/...` endpoints.
- Keep API keys for Qdrant Cloud or downstream agents in environment variables, not in generated notes.

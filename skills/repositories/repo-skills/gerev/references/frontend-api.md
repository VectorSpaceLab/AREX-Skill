# Frontend and HTTP API contract

This reference summarizes the backend routes that the React UI and connector flows call.

## Search and status

| Method | Route | Purpose | Notes |
| --- | --- | --- | --- |
| `GET` | `/api/v1/search` | Search documents and return ranked results | Query params: `query`, optional `top_k`. Uses the search/rerank stack in `search-indexing`. |
| `GET` | `/api/v1/status` | Report queue and indexing progress | Returns `docs_in_indexing`, `docs_left_to_index`, and `docs_indexed`. |
| `POST` | `/clear-index` | Clear Faiss/BM25 and delete all documents/paragraphs | Destructive maintenance route. |
| `POST` | `/check-for-new-documents` | Force indexing checks across connected sources | Can trigger external connector activity. |

## Data-source management

| Method | Route | Purpose | Notes |
| --- | --- | --- | --- |
| `GET` | `/api/v1/data-sources/types` | List connector types for the add panel | Returns display name, config fields, icon, and `has_prerequisites`. |
| `GET` | `/api/v1/data-sources/connected` | List connected sources | Used to render the active data-source badges. |
| `POST` | `/api/v1/data-sources` | Create a connected data source | Body: `{ name, config }`. Starts an indexing task after creation. |
| `DELETE` | `/api/v1/data-sources/{id}` | Remove a connected data source | Deletes the source and its documents. |
| `POST` | `/api/v1/data-sources/{name}/list-locations` | Ask a connector for selectable locations | Used only by connectors that expose location selection. |

## UI behavior

- `ui/src/api.ts` points the browser client at `/api/v1` on the current host and uses port `8000` in development.
- `ui/src/components/data-source-panel.tsx` expects `ConfigField` objects with `name`, `label`, `placeholder`, and `input_type` values.
- `ui/src/components/search-result.tsx` renders document, message, issue, and comment result variants and relies on the backend to provide `type`, `file_type`, `status`, and parent/child nesting.
- `ui/src/App.tsx` polls the status endpoint and swaps between the search view and the connector panel.

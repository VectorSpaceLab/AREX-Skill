# Local Web API Reference

## Purpose

Read this when a task needs to automate, inspect, or troubleshoot Semantra's
local Flask web app after documents have been indexed.

## Server startup

Semantra starts Flask unless `--no-server` is passed. Defaults:

- host: `127.0.0.1`;
- port: `8080`;
- static assets: bundled Semantra `client_public` package data;
- files served: the documents passed to the current Semantra process.

Change the port when 8080 is busy:

```sh
semantra --port 8081 <files>
```

Expose beyond localhost only with explicit approval:

```sh
semantra --host 0.0.0.0 --port 8080 <files>
```

The web app exposes document contents through local routes, so LAN exposure can
leak sensitive files.

## Static routes

| Route | Purpose |
| --- | --- |
| `/` | Serve the bundled web app `index.html`. |
| `/<path>` | Serve bundled static JS/CSS/assets from package data. |

If static files are missing, the Python package likely lacks the built frontend
assets or package data is misinstalled.

## Data routes

| Route | Method | Purpose | Response shape |
| --- | --- | --- | --- |
| `/api/files` | GET | List files in the current Semantra session. | JSON list with `basename`, `filename`, and `filetype` (`text` or `pdf`). |
| `/api/text?filename=...` | GET | Return token/text chunks for a file. | JSON list of strings. |
| `/api/getfile?filename=...` | GET | Serve the original file. | File response. |
| `/api/pdfpositions?filename=...` | GET | Return PDF page offsets and page sizes. | JSON list of `{char_index, page_width, page_height}`; empty list for text files. |
| `/api/pdfpage?filename=...&page=...&scale=...` | GET | Render one PDF page image. | PNG response for PDF files. |
| `/api/pdfchars?filename=...&page=...` | GET | Return PDF characters and boxes for a page. | JSON list of `[character, box]`; empty list for non-PDF files. |

The browser uses `/api/text` to rebuild document text and token offsets, then
uses PDF-specific routes only for PDF viewers.

## Query routes

### `/api/query`

Method: POST.

Request JSON:

```json
{
  "queries": [{"query": "economic growth", "weight": 0.309016994375}],
  "preferences": []
}
```

The route dispatches based on CLI flags:

- if `--svm` was selected, it uses the SVM route;
- else if Annoy is enabled, it uses the Annoy route;
- else it performs exact cosine search over embedding matrices.

Response JSON has:

```json
{
  "results": [["filename", [/* search result objects */]]],
  "sort": "desc"
}
```

Each search result includes text, score/distance, token offset, index, filename,
queries, and preferences.

### `/api/queryann`

Uses the first Annoy index for each document. It calls
`get_nns_by_vector(..., include_distances=True)` and converts angular distance
to a cosine-like score with `1 - distance**2 / 2`.

### `/api/querysvm`

Requires `scikit-learn` because it imports `sklearn.svm` lazily. It trains a
`LinearSVC` per query with stored document embeddings as negative class and the
combined query/preference embedding as the positive class. Semantra rejects SVM
mode for asymmetric models before the server starts.

### `/api/explain`

Request JSON includes `filename`, `offset`, `queries`, and `preferences`. The
route repeatedly embeds versions of the selected result window with splits
removed, then returns chunks marked as `highlight` or `normal`.

This route may call the active embedding model multiple times per result. With
OpenAI mode it can make external API calls; with local transformer models it can
consume noticeable compute.

## Automation cautions

- The server is session-bound: it only knows the files passed to the running
  process.
- The API exposes raw filenames and file contents to clients that can reach the
  server.
- Long-lived automated clients should handle stale caches and restarted server
  processes.
- Use `--no-server` for indexing-only automation; use the API only when a local
  search session is intentionally running.

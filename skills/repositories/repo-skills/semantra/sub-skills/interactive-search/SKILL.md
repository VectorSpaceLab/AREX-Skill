---
name: interactive-search
description: "Guides Semantra local web search, query arithmetic, preference
  tags, result interpretation, and Flask API troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Semantra Interactive Search

Use this sub-skill after documents have been indexed and the task is to operate,
explain, automate, or troubleshoot Semantra's local browser search experience.

## Read first

- [query-semantics.md](references/query-semantics.md) for plus/minus query
  arithmetic, numeric weights, preference tags, normalization, result scores,
  and examples.
- [web-api-reference.md](references/web-api-reference.md) for the local Flask
  endpoints, request/response shapes, text/PDF navigation, and static asset
  behavior.
- [troubleshooting.md](references/troubleshooting.md) for stale UI state, low
  semantic scores, port conflicts, LAN exposure, SVM issues, PDF page/char
  failures, and missing frontend assets.
- Run [parse_semantra_query.py](scripts/parse_semantra_query.py) when you need
  to mirror the web UI's query parsing and normalized weights without starting
  Semantra.

## Route here when

- The user asks how to search with `+`, `-`, or weighted query phrases.
- The user wants to use plus/minus result tags to steer a query.
- The user asks why Semantra always returns some results, why scores around
  `0.50` can be meaningful, or why exact-word matches are not guaranteed.
- The local UI is stale, filtered, collapsed, sorted in the wrong view, or not
  navigating to a result.
- The user wants to call Semantra's local JSON endpoints from a script.
- The server cannot bind to `localhost:8080`, needs another port, or needs
  careful LAN exposure.

Route document preprocessing, cache inspection, PDF extraction, and `--windows`
to [document-indexing](../document-indexing/SKILL.md). Route model choice,
OpenAI/Hugging Face/CUDA, and SVM dependency planning to
[models-and-embeddings](../models-and-embeddings/SKILL.md).

## Start the local UI

After choosing documents and a model, run Semantra without `--no-server`:

```sh
semantra --semantra-dir ./semantra-cache <files>
```

By default the Flask server binds to `127.0.0.1:8080`. If port 8080 is busy,
choose another port:

```sh
semantra --port 8081 <files>
```

Use `--host 0.0.0.0` only when the user intentionally wants other machines to
connect. Semantra serves the user's documents through the local app routes, so
LAN exposure is a privacy decision.

## Query arithmetic workflow

Semantra's browser search bar accepts query terms joined by `+` and `-` signs:

```text
economic growth - unchecked capitalism + war
```

The UI parses this into weighted query phrases, embeds each phrase, and combines
the embeddings. Positive search-result tags add embeddings to the positive side;
negative tags add embeddings to the negative side. Use the bundled parser helper
to explain the query shape without running a server:

```sh
python path/to/parse_semantra_query.py "economic growth - unchecked capitalism + war"
```

## Result behavior

Semantra ranks windows, not whole documents, then groups or sorts the returned
windows in the UI. Exact exhaustive search uses cosine similarity. The default
Annoy path queries an angular index and converts Annoy distances back to a
cosine-like score. The optional SVM path trains a small linear SVM against the
combined query/preference vector and document window embeddings.

## UI controls to remember

- The yellow search bar means the query or tags have changed and results are
  stale until the user reruns the search.
- The results pane can group by file or switch to individual-result ordering.
- The filter box filters filenames; the eye button filters to the currently
  displayed file.
- The tab bar changes the active document; clicking a result navigates the text
  or PDF viewer to the result window.
- PDF views use `/api/pdfpositions`, `/api/pdfpage`, and `/api/pdfchars` in
  addition to the token stream from `/api/text`.

## Validation signals

A good answer for an interactive-search problem should include:

- whether the issue is indexing/model setup or web-query behavior;
- the exact query string, tag state, and filter/view state involved;
- the relevant server URL, host, and port;
- the endpoint or UI control to check next;
- privacy warnings before exposing the server beyond localhost.

# RAGFlow SDK and HTTP Troubleshooting

Use this guide when a public HTTP, SDK, OpenAI-compatible, streaming, retrieval, or auth integration fails. Start with the smallest non-destructive check: URL construction, server health, API key presence, then a list/read endpoint.

## Quick triage

1. Confirm the server origin, for example `http://localhost:9380`, and verify `GET /api/v1/system/healthz`.
2. Confirm protected requests include `Authorization: Bearer <RAGFLOW_API_KEY>`.
3. Confirm raw HTTP paths include `/api/v1`, while SDK `base_url` does not.
4. Reproduce with a non-stream request before debugging streaming parsers.
5. Check whether the JSON body contains `code != 0` even when the HTTP status is 200.
6. Confirm resource IDs are the right type and belong to each other: dataset → document → chunk, chat → session, agent → session, memory → message.

## 401, 403, and “No authorization.”

Symptoms:

- HTTP `401 Unauthorized`.
- HTTP `403 Forbidden`.
- JSON payload with `code: 102` and message such as `No authorization.`.
- SDK raises `Exception("No authorization.")`.

Fixes:

- Use exactly `Authorization: Bearer <key>`; do not omit `Bearer`.
- Remove copied trailing newlines from API keys.
- Verify the key belongs to the tenant that owns the dataset, chat, agent, or memory.
- If the request uses team/shared resources, check the dataset or memory permission setting.
- Do not pass login JWT examples as API keys unless the target endpoint explicitly uses that auth context.
- Try a simple protected read such as `GET /api/v1/datasets?page=1&page_size=1` to separate auth problems from payload problems.

## Wrong `base_url` or version prefix

Raw HTTP and SDK clients differ:

- Raw HTTP URL: `http://server:port/api/v1/datasets`.
- SDK constructor: `RAGFlow(api_key, base_url="http://server:port", version="v1")`.
- OpenAI-compatible constructor: `OpenAI(api_key, base_url="http://server:port/api/v1/openai/<chat_id>/chat")`.

Common mistakes:

- Passing `base_url="http://server:port/api/v1"` to the SDK creates duplicated paths such as `/api/v1/api/v1/datasets`.
- Omitting `/api/v1` from raw HTTP produces 404s.
- Using `/v1/system/healthz` works only as a deprecated alias; use `/api/v1/system/healthz`.
- Using `https` against a local `http` server, wrong port, or a frontend port instead of the backend port.

Use the bundled helper to print the prepared health request without network access:

```bash
python scripts/ragflow_api_smoke.py --base-url http://localhost:9380 --print-curl
```

## Server not running or unhealthy

Symptoms:

- Connection refused or timeout.
- Health check returns `status: nok`.
- Retrieval, parsing, or upload calls fail with HTTP 500.

Fixes:

- Verify the backend service is reachable at the server origin.
- Call `GET /api/v1/system/healthz`; dependency keys include `db`, `redis`, `doc_engine`, `storage`, and top-level `status`.
- If health is `nok`, resolve the named dependency before retrying API calls.
- Do not use dataset upload, parsing, retrieval, or chat calls as the first availability probe; those have many unrelated prerequisites.

## OpenAI-compatible base URL issues

Correct pattern:

```python
from openai import OpenAI

client = OpenAI(
    api_key="<RAGFLOW_API_KEY>",
    base_url="http://localhost:9380/api/v1/openai/<CHAT_ID>/chat",
)
client.chat.completions.create(
    model="model",
    messages=[{"role": "user", "content": "Hello"}],
    stream=False,
)
```

Troubleshooting:

- If the request goes to `/chat/completions/completions`, the base URL is too long; it should end at `/chat` because the OpenAI client appends `/completions`.
- If the request goes to `/api/v1/chat/completions`, you are using RAGFlow’s native chat endpoint, not the OpenAI-compatible endpoint.
- If the server says the last content is not from user, ensure the last `messages` item has `role: "user"`.
- If references are missing, include `extra_body={"reference": True}` and wait for the final chunk/event.
- If metadata is missing from references, include `extra_body={"reference_metadata": {"include": True}}` and optionally `fields`.

## Streaming final reference chunk handling

Streaming outputs vary by endpoint:

- OpenAI-compatible chat streams use OpenAI-style chunks and finish with `data:[DONE]`.
- With `extra_body.reference=true`, references can appear on the final chunk at `choices[0].delta.reference` rather than on every token chunk.
- Native chat streams send RAGFlow JSON payloads and finish with `data: {"code": 0, "data": true}`.
- Native agent streams emit events such as `message`, `message_end`, and `node_finished`, then `data:[DONE]`.

Fixes:

- Do not treat the first chunk without `reference` as proof that citations are absent.
- Buffer the latest `reference` object seen during the stream and attach it to the final answer.
- For native chat, skip chunks that only contain `start_to_think` or `end_to_think` markers if the user requested final visible answer text only.
- Preserve `message_end.reference` for native agent streams.

## Dataset, document, and chunk ID confusion

Symptoms:

- `The dataset doesn't exist`.
- `You do not own the dataset ...`.
- `The dataset does not have the document.`
- `Chunk not found` or `Invalid Chunk ID`.
- Chunk delete reports zero deleted.

Fixes:

- List datasets and confirm `dataset.id` before using it in document paths.
- List documents under the specific dataset and confirm `document.id` before using it in chunk paths.
- List chunks under the specific document and use the returned chunk `id` in chunk operations.
- Use `chunk_ids` in chunk delete bodies, not `ids`.
- Use `document_ids` when starting or stopping parsing; do not pass chunk IDs there.
- Ensure all `document_ids` used in `/api/v1/retrieval` belong to datasets with compatible embedding models.

## DELETE request bodies are missing

Many HTTP libraries make it easy to accidentally omit DELETE JSON bodies. RAGFlow bulk delete endpoints expect them.

Correct bodies:

- Datasets: `DELETE /api/v1/datasets` with `{"ids": [...], "delete_all": false}`.
- Documents: `DELETE /api/v1/datasets/{dataset_id}/documents` with `{"ids": [...], "delete_all": false}`.
- Chunks: `DELETE /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks` with `{"chunk_ids": [...], "delete_all": false}`.
- Chat assistants and sessions: use `ids` or `delete_all` bodies.
- Stop parsing: `DELETE /api/v1/datasets/{dataset_id}/chunks` with `{"document_ids": [...]}`.

In Python `requests`, use `requests.delete(url, json=payload, headers=headers)`. In curl, include both `--request DELETE` and `--data '{...}'` with `Content-Type: application/json`.

## Deprecated endpoint aliases

When adapting old scripts:

- Replace `/api/v1/chats_openai/{chat_id}/chat/completions` with `/api/v1/openai/{chat_id}/chat/completions`.
- Replace `PUT /api/v1/chats/{chat_id}/sessions/{session_id}` with `PATCH /api/v1/chats/{chat_id}/sessions/{session_id}`.
- Replace `POST /api/v1/chats/{chat_id}/completions` with `POST /api/v1/chat/completions`.
- Replace `PUT /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks/{chunk_id}` with `PATCH` on the same path.
- Replace old file routes under `/api/v1/file/...` with `/api/v1/files...` routes.

Keep the request body shape unless the replacement endpoint documents a field rename. For chunk deletes, use `chunk_ids`; for most other bulk deletes, use `ids`.

## SDK install or import problems

Symptoms:

- `ModuleNotFoundError: No module named 'ragflow_sdk'`.
- Confusion between `ragflow-sdk`, `ragflow_sdk`, and `ragflow`.
- Full server editable install fails due to package discovery around GraphRAG.

Fixes:

- Install the client package with `pip install ragflow-sdk`.
- Import with `from ragflow_sdk import RAGFlow`.
- Use the SDK for client integrations; do not require a full editable server install to call public APIs.
- RAGFlow 0.26.1 declares Python `>=3.13,<3.14`; use a compatible interpreter for local SDK work.
- If full server package installation fails because the project metadata lists a top-level `graphrag` package while the source is nested under the RAG source tree, treat it as server environment/package troubleshooting, not a client SDK usage issue.

## Retrieval returns empty or irrelevant chunks

Check:

- Documents have been parsed and reached a done status.
- Chunks are available; chunk availability can be toggled off.
- `dataset_ids` and `document_ids` point to the intended resources.
- `similarity_threshold` is not too high.
- `vector_similarity_weight` fits the query type; lower values emphasize keyword similarity, higher values emphasize vector similarity.
- Metadata filters use valid field names and comparison operators.
- `use_kg` is enabled only after a knowledge graph has been constructed.
- `toc_enhance` is enabled only for documents with extracted table of contents.

## Difficult synthetic usability cases

Use these when verifying this sub-skill:

1. Migrate a legacy shell script that calls `/api/v1/chats_openai/{chat_id}/chat/completions`, `PUT` session updates, and old file routes to current `/api/v1` endpoints while preserving request bodies, auth headers, and streaming behavior.
2. Build a Python OpenAI-compatible client request with `extra_body.reference=true`, `reference_metadata.include=true`, a metadata filter, and a non-stream fallback that extracts answer text plus final references from both response modes.

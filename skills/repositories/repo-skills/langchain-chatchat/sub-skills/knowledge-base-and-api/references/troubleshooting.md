# API and RAG Troubleshooting

## Route selection problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| 404 for an expected route | Calling the wrong route family or old API path | Run `scripts/api_surface_probe.py --json` in the installed package, then use the current route path. |
| Browser/API docs unavailable | API server is not running or wrong host/port | Start `chatchat start --api`; check `basic_settings.yaml` API host/port. |
| SDK method path differs from current route | SDK wrapper and server route versions may drift | Prefer route reference from current installed server; inspect SDK with SDK probe and reconcile base URL/path. |

## Provider/model errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `/v1/models` returns empty/error | Provider endpoint not reachable or unsupported | Validate provider independently; fix `MODEL_PLATFORMS`; do not debug Chatchat request payloads first. |
| Chat request says model not found | `model` field does not match configured provider model name | Use provider model list and `model_settings.yaml`; update `DEFAULT_LLM_MODEL` and request payload. |
| Embedding/vector rebuild fails | Embedding model is missing/unreachable | Fix embedding provider and `DEFAULT_EMBEDDING_MODEL`; test a minimal embedding request if provider supports it. |

## Streaming and response shape

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Client receives chunks with `data:` prefixes | Route is streaming SSE | Use an SSE-aware client or SDK streaming generator; collect chunks until final result. |
| Agent/tool response includes status/tool events | Agent workflows stream intermediate tool steps | Treat status/tool chunks as expected; filter only final text if user needs final answer. |
| Non-streaming client hangs on stream route | `stream=True` used without consuming stream | Set `stream=False` where supported or iterate response content. |

## Knowledge-base quality

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| RAG answer ignores uploaded docs | Docs were not vectorized, wrong KB, high threshold, or provider generated unrelated answer | Check `list_files`, direct `search_docs`, and `return_direct=True`; then adjust indexing/search settings. |
| Search returns no docs | Wrong query language/model, score cutoff too strict, vector store not rebuilt | Lower/raise threshold according to backend semantics, rebuild after embedding/chunk changes, verify exact phrase search. |
| File upload succeeds but later download/search fails | Filename/path mismatch or content not persisted/vectorized | Use API response file names; list files; avoid assuming local filenames survive unchanged. |

## Tool calls

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Tool name rejected | Tool not registered or disabled | Fetch `/tools`; use exact tool name and check tool config. |
| Model picks wrong tool/arguments | Model tool-calling ability is weak | Use explicit `tool_choice` and `extra_body.tool_input` for manual tool input. |
| Tool call errors internally | Missing API key, service, or invalid input for that tool | Inspect tool schema from `/tools`; verify external service/credentials only with user approval. |

## External vector DBs

If non-FAISS vector stores fail, isolate the backend:

1. Confirm the service is running outside Chatchat.
2. Validate host/port/credentials/DB name from `kb_settings.yaml`.
3. Run a tiny service-specific connection test if the user approves.
4. Only then rerun Chatchat KB operations.

## Safe fallback

When a live provider or vector DB is unavailable, still produce useful static artifacts: route list, request skeletons, configuration checklist, direct retrieval debugging steps, and clear unverified-service notes.

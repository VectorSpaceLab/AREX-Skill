# Knowledge and OCR troubleshooting

Use this reference to classify Yuxi KB/OCR failures without broad service restarts or credential exposure. Start from the symptom, then verify the smallest responsible layer.

## Fast triage checklist

1. **KB type:** `milvus`, `dify`, or `notion`? Only Milvus supports upload/parse/index/file/graph/evaluation generation workflows.
2. **Permission:** is the current user allowed to read or manage the KB? Public APIs enforce read/manage permissions.
3. **File state:** for Milvus, inspect file metadata status: `uploaded`, `parsing`, `parsed`, `error_parsing`, `indexing`, `indexed`, or `error_indexing`.
4. **Services:** live ingestion needs API, tasker/worker, Postgres, Redis, MinIO, and Milvus. Graph adds Neo4j and model/embedding provider access. Cloud OCR adds network and credentials.
5. **Config source:** DB option values override environment fallbacks. Sensitive fields are redacted on read.
6. **Native proof:** prefer the CPU parser facade test first; run E2E only after service prerequisites are ready.

## Common symptoms and fixes

| Symptom | Likely cause | Minimal check | Correct action |
| --- | --- | --- | --- |
| `Unsupported knowledge base type` or KB omitted from list | Stale metadata or unsupported `kb_type` | `GET /api/knowledge/types`; inspect KB type in database detail | Create/update with one of `milvus`, `dify`, `notion`; do not resurrect historical LightRAG as supported. |
| Dify/Notion rejects upload/open/find/download | Public document operations are gated to document-supporting KBs | Check `supports_documents` in accessible KB response | Use retrieval only, or create a Milvus KB for file workflows. |
| Milvus KB creation fails with embedding error | Missing or non-embedding `embedding_model_spec` | Check model provider cache/config for model type | Configure a real embedding provider/model before creating Milvus KB. |
| Duplicate upload returns conflict | Same content hash already exists in KB | Compare upload response `content_hash` and existing file list | Reuse existing file, rename if only name differs, or intentionally delete/reupload. |
| Upload/import rejects file type | Extension outside supported parser set | `GET /api/knowledge/files/supported-types` | Convert file to a supported format or add parser support deliberately. |
| Upload/import rejects size | 100 MB per-file limit | Check uploaded or workspace file size | Split/compress/convert source; do not bypass limit in tests. |
| URL fetch rejected | URL whitelist disabled/missing, unsupported scheme, or private IP target | Check URL whitelist and final URL | Add an explicit safe whitelist entry; do not allow broad/private fetches. |
| Parse selected files fails with status error | File not in `uploaded`, `error_parsing`, or legacy failed state | Inspect document status | Reset/re-upload or choose pending parse workflow. Do not parse already parsing/indexing files. |
| Index selected files fails with status error | File was not parsed or is in active processing state | Inspect `markdown_file` and status | Parse first; re-index only from `parsed`, `error_indexing`, `indexed`, or legacy done. |
| Index says file has no Markdown and marks unparsed | `markdown_file` missing despite index request | `GET /api/knowledge/databases/{kb_id}/documents/{file_id}/basic` | Re-run parse; investigate parser storage failure. |
| Query returns empty results | File never indexed, high threshold, wrong mode, missing service, or provider failure | Check chunks, file status, query params, and service logs | Lower threshold, switch search mode, re-index, fix embedding/Milvus connectivity, or tune chunking. |
| Reranker query silently falls back | Reranker model missing or failed | Inspect query params and logs | Set `reranker_model` when `use_reranker=true`; confirm provider credentials. |
| File-name scoped query returns no hits | `file_name` filter matched no file IDs | Search document filenames first | Use exact/partial filename that exists or remove filter. |
| Agent `query_kb` says KB not enabled | Runtime context has no visible/enabled KB | Call `list_kbs`; inspect agent context knowledges | Enable the KB for the agent/session; do not hard-code unseen KB IDs. |
| `open_kb_document` says no parsed Markdown | File not parsed or connector is read-only | Confirm file ID from `query_kb` and KB type | Parse/index Milvus file; for Dify/Notion rely on query snippets. |
| `download_kb_file` cannot write output | Missing runtime file scope or invalid binary file record | Check thread/user context and file metadata | Run inside an agent sandbox context; choose a file with original bytes. |

## OCR and parser failures

| Symptom | Likely cause | Minimal check | Correct action |
| --- | --- | --- | --- |
| `不支持的 OCR 引擎` | Invalid engine id or stale default | `GET /api/system/ocr/options` | Use one of the supported IDs or `disable`; update `default_ocr_engine`. |
| `OCR 文件缺少已解析的 ocr_engine` | Low-level `parse_pdf`/`parse_image` called directly without facade resolution | Review call site | Call `parse_document` or resolve task params first. |
| Image parse says OCR must be enabled | `ocr_engine=disable` for image | Inspect parse params | Choose a real engine such as `rapid_ocr`; `enable_ocr` legacy field is ignored. |
| PDF text parse unexpectedly OCRs pages | Default OCR engine applied because no explicit engine was supplied | Inspect `processing_params.ocr_engine` and system default | Use explicit `ocr_engine="disable"` for text PDFs when OCR is not desired. |
| RapidOCR first parse slow/fails | Local ONNX models lazy load/download or environment lacks dependencies | Run parser facade tests; inspect logs around model load | Prepare CPU parser deps/cache; retry after model download; do not classify as cloud/service issue. |
| MinerU unavailable | `mineru-api` service not running or wrong URL | `GET /api/system/ocr/health`; service logs | Start/configure MinerU service; use correct internal URL for containers; account for GPU/build time. |
| MinerU timeout | Large PDF or GPU service overloaded | Check timeout and service logs | Increase `MINERU_TIMEOUT`/`timeout_seconds`, reduce file size/pages, or use cloud/CPU alternative. |
| MinerU result parse/download failure | Service returned malformed/missing ZIP/Markdown | Inspect parser error code and response body preview | Re-run on a small file; upgrade/fix service; keep failure evidence. |
| MinerU Official missing key | No `MINERU_API_KEY` or saved API key | Config options sensitive state | Configure key only after confirming cloud data transfer is allowed. |
| PP-Structure-V3 unavailable | PaddleX service not healthy | OCR health and `/health` result | Start/configure service, usually GPU-backed; verify `PADDLEX_URI`/DB URL. |
| DeepSeek OCR credential error | `siliconflow-cn` provider disabled or missing API key | Model provider config, OCR health | Enable provider and key; confirm external call approval. |
| PaddleOCR missing token | No `PADDLEOCR_API_TOKEN` or saved token | Config option sensitive state | Configure Access Token; avoid printing it. |
| PaddleOCR job timeout/missing result | Cloud job slow, failed, or returned malformed response | Parser error code (`missing_result_url`, `timeout`, `job_failed`) | Retry smaller file; increase wait; inspect cloud account/quota. |
| Parsed Markdown image links broken | `HOST_IP`, MinIO, image bucket, or authenticated proxy issue | Fetch a proxied image URL as an authenticated user | Fix host/proxy/object storage config; verify image proxy path begins with `kb-images/`. |
| `ocr_parse_file` rejects path | Not under sandbox user-data, not workspace/uploads/outputs, missing file, or directory | Confirm virtual path prefix and namespace | Use attachment/workspace/output virtual paths only; never pass host checkout paths. |
| `read_file` rejects PDF/Office | Intended behavior | Read error text | Call `ocr_parse_file`, then `read_file` on generated Markdown. |
| Non-vision model cannot inspect image | Model rejected image input and no OCR fallback path was available | Check tool messages and model input middleware logs | Ensure image came from `read_file` with a readable path and default OCR engine works. |

## Graph failures

| Symptom | Likely cause | Minimal check | Correct action |
| --- | --- | --- | --- |
| Graph API says only Milvus supported | KB type is Dify/Notion | KB detail | Use Milvus KB for graph features. |
| Cannot start graph build: config not locked | Extractor not configured | Graph build status | Call graph-build config with `extractor_type="llm"` and a valid `model_spec`. |
| Config rejects `prompt` | Full custom prompt is intentionally disallowed | Request payload | Use `schema` to constrain extraction instead of replacing prompt. |
| Config already locked | Existing locked extractor type differs or user is trying incompatible change | Graph status config | Reset graph config if the extraction design must change; otherwise update model/schema options only. |
| Another graph task is running | Active `knowledge_graph_index` task for the KB | Graph build status/task center | Wait, cancel, or inspect current task; do not enqueue duplicates. |
| Build fails with extraction errors | LLM provider/JSON parse/schema/rate limit issue | Failed chunk samples and task logs | Lower concurrency, fix model credentials, simplify schema, or retry failed chunks. |
| Build fails with vector errors | Embedding provider/Milvus graph vector store problem | Vector status counts | Fix embedding/Milvus; use reconcile in `failed` or `all_vectors` mode as appropriate. |
| Build fails with Neo4j errors | Neo4j service unreachable or data write issue | Neo4j service health/logs | Fix Neo4j connectivity before retrying; reset only when data consistency requires it. |
| Graph retrieval has no effect | No graph-indexed chunks or query params disabled | Graph status, query params | Complete graph build and set `use_graph_retrieval=true`; tune `graph_*` params. |

## Evaluation failures

| Symptom | Likely cause | Minimal check | Correct action |
| --- | --- | --- | --- |
| JSONL upload rejected | File extension not `.jsonl`, invalid JSON, or missing `query` | Validate first few lines | Fix JSONL rows; keep `gold_chunk_ids`/`gold_answer` optional but well-typed. |
| Generated dataset says no chunks | Milvus KB empty or files not indexed | KB stats and file statuses | Upload/parse/index documents first. |
| Graph-enhanced generation rejected | No graph-indexed chunks | Graph status | Build graph before using `generation_mode="graph_enhanced"`. |
| Dataset remains pending/running | Background task still active or failed without metadata sync | Dataset list/detail and task center | Inspect task; resume generated datasets only when metadata has saved params. |
| Run has no answer metrics | No `gold_answer` or no judge/answer model | Dataset flags and retrieval config | Add `gold_answer` and configure judge/answer LLM if answer scoring is required. |
| Run failed mid-way | Retrieval/provider/task cancellation error | Run detail and task error | Fix underlying retrieval/model issue, then create a new run. |

## Service and credential gates

Before running service-required or external tests, confirm:

- API service is reachable and authenticated headers are available.
- Postgres, Redis/tasker, MinIO, and Milvus are healthy for Milvus workflows.
- Neo4j is healthy before graph build/query.
- Sandbox provisioner is healthy before `read_file`/`ocr_parse_file` E2E tests.
- Model providers are configured for embedding, reranker, judge/answer LLM, graph extraction LLM, or vision-model tests.
- External OCR/data connectors have explicit permission because documents may leave the deployment boundary.

Do not paste API keys, tokens, or signed URLs into logs, reports, or generated skill content.

## Native verification commands

Use these as verification candidates, not as mandatory checks for every edit:

```bash
# CPU-safe parser facade and OCR-selection coverage
pytest backend/test/unit/knowledge/test_parser_facade.py

# Service-required OCR configuration E2E
pytest backend/test/e2e/test_ocr_config_center_e2e.py

# Service/model-required multimodal read_file + OCR fallback E2E
pytest backend/test/e2e/test_read_file_multimodal_e2e.py
```

If the CPU-safe parser test fails, fix local parser/facade behavior before blaming Docker services. If E2E fails while unit passes, classify by service, sandbox, model, credential, or network dependency.

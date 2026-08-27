# Studio API and Routes

Studio is a FastAPI backend with a web frontend, first-party `/api/*` route groups, and OpenAI-compatible `/v1/*` endpoints. Most mutating or sensitive routes require Studio auth via bearer JWT or API key. Do not assume these endpoints are unauthenticated just because they are local.

## Top-Level Route Groups

| Prefix | Purpose | Typical Use |
| --- | --- | --- |
| `/api/health` | Health, service name, safe same-install discriminator | Check server is running; does not expose raw Studio root path. |
| `/api/studio/install-source` | Install source metadata | UI/support diagnostics. |
| `/api/studio/update-status` | Studio update status | UI/support diagnostics. |
| `/api/shutdown` | Graceful server shutdown | UI quit flow; cleans model/export/training/tunnel subprocesses. |
| `/api/system` | System, version, hardware summary | Runtime diagnostics after auth-sensitive filtering. |
| `/api/system/gpu-visibility` | Visible GPU state | Debug `CUDA_VISIBLE_DEVICES` or device selection. |
| `/api/system/hardware` | Hardware details | Debug GPU/MLX/ROCm/CPU detection. |
| `/api/auth/*` | Login, tokens, API keys, identity proof | Browser auth and coding-agent API keys. |
| `/api/models/*` and `/api/hub/*` | Model discovery, cache, GGUF variants, folder scans | Find/load local, HF-cache, LM Studio, GGUF, LoRA, and checkpoint candidates. |
| `/api/inference/*` | Load/unload/status/generate/audio/studio inference helpers | Studio UI model control and local inference. |
| `/v1/*` | OpenAI-compatible model, chat, responses, embeddings, Anthropic-compatible messages | Coding-agent and API client integration. |
| `/api/providers/*` | External provider registry, encrypted key test, model listing | Configure OpenAI/Anthropic/Gemini/custom/OAI-compatible providers. |
| `/api/settings/*` | Upload limits, helper pre-cache, personalization | User/runtime settings. |
| `/api/mcp/servers/*` | MCP server CRUD, import, test, tool refresh | Tool server configuration. |
| `/api/prompts/*` | Prompt entries/lists CRUD | Prompt library management. |
| `/api/datasets/*` | Dataset upload/list/check/mapping | Training/data recipe dataset preparation. |
| `/api/data-recipe/*` | Seed inspection, unstructured file ingestion, jobs, validation, MCP tools | Visual data recipe workflows and dataset generation. |
| `/api/rag/*` | Knowledge bases, document ingestion, search, signed previews | Retrieval-augmented chat and document citation workflows. |
| `/api/llama/*` | llama.cpp prebuilt freshness/update | Runtime llama.cpp maintenance. |
| `/api/export/*` | Export/merge/GGUF export operations | Route details to `../model-export/SKILL.md`. |
| `/api/train/*` | Studio training start/status/history/hardware | Route code-first training to `../core-training/SKILL.md`; Studio UI runtime status can remain here. |

## Auth and API Keys

Important routes:

| Method | Route | Notes |
| --- | --- | --- |
| `GET` | `/api/auth/identity?nonce=...` | Unauthenticated challenge-response proof for local same-user Studio identity. Used before auto-minting local coding-agent keys. |
| `GET` | `/api/auth/status` | Initialization state and default username for first-boot UI. |
| `POST` | `/api/auth/login` | Username/password login; per-account and per-IP rate-limited. |
| `POST` | `/api/auth/logout` | Revokes refresh tokens. |
| `POST` | `/api/auth/desktop-login` | Exchanges local desktop secret for normal tokens. |
| `POST` | `/api/auth/refresh` | Single-use refresh-token exchange. |
| `POST` | `/api/auth/change-password` | Replaces default password and revokes refresh tokens. |
| `POST` | `/api/auth/api-keys` | Creates an API key; raw key returned once only. |
| `GET` | `/api/auth/api-keys` | Lists key metadata and prefixes, never raw keys. |
| `DELETE` | `/api/auth/api-keys/{key_id}` | Revokes an API key. |

Coding-agent connection logic uses `/v1/models` to test keys. Local loopback auto-minting is only attempted after the identity proof succeeds. Remote/non-loopback Studio servers require an explicit API key from the user.

## Inference and OpenAI-Compatible Endpoints

Studio has both UI-oriented `/api/inference/*` routes and OpenAI-compatible `/v1/*` routes.

Key UI/runtime routes:

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/inference/validate` | Resolve a model identifier without loading weights; reports GGUF/LoRA/vision/security metadata. |
| `POST` | `/api/inference/load` | Load a model for inference. Handles GGUF, LoRA, local/HF identifiers, trust-remote-code gates, context/cache settings, tensor parallelism, and llama extras. |
| `POST` | `/api/inference/unload` | Unload active model. |
| `GET` | `/api/inference/status` | Active model, loading state, modality, GGUF variant, context, cache, reasoning/tools support, and other capability flags. |
| `GET` | `/api/inference/load-progress` | GGUF mmap/RSS progress during heavy loads. |
| `POST` | `/api/inference/generate/stream` | Legacy Studio streaming generation endpoint. |
| `POST` | `/api/inference/audio/generate` | Audio/TTS generation path. |
| `GET` | `/api/inference/sandbox/{session_id}/{filename}` | Serves sandboxed generated artifacts. |

`LoadRequest` supports `model_path`, optional HF token, `max_seq_length`, `load_in_4bit`, `is_lora`, `gguf_variant`, `trust_remote_code`, approved remote-code fingerprint, chat-template override, `cache_type_kv`, `gpu_ids` for non-GGUF loads, speculative decoding fields, `tensor_parallel`, and `llama_extra_args` for GGUF. Studio rejects unsafe or Studio-managed llama-server flags; allowed extras are appended after auto-set flags so llama.cpp last-wins behavior applies.

OpenAI-compatible routes:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/v1/models` | List loaded/available Studio model IDs for clients. |
| `GET` | `/v1/models/{model_id}` | Model detail lookup. |
| `POST` | `/v1/chat/completions` | OpenAI-style chat completion, streaming or non-streaming. |
| `POST` | `/v1/completions` | OpenAI-style completion. |
| `POST` | `/v1/embeddings` | Embedding route when supported. |
| `POST` | `/v1/responses` | OpenAI Responses API; needed by Codex integration. |
| `POST` | `/v1/messages/count_tokens` | Anthropic-compatible token counting. |
| `POST` | `/v1/messages` | Anthropic-compatible messages endpoint. |

If a coding agent needs streaming `/v1/responses`, prefer a GGUF model served through llama-server. The `unsloth connect codex` flow checks this and rejects transformer-backend models for Codex.

## Model Discovery and GGUF Routes

Useful model routes under `/api/models` and `/api/hub` include:

| Route | Purpose |
| --- | --- |
| `/api/models/local` or `/api/hub/local` | Local model discovery from Studio model dirs, HF cache, LM Studio dirs, and custom scan folders. |
| `/api/models/scan-folders` | List/add/remove custom model scan folders. |
| `/api/models/recommended-folders` | Suggested model directories. |
| `/api/models/browse-folders` | Folder browser with model-bearing hints. |
| `/api/models/list` | Model catalog/list endpoint. |
| `/api/models/config/{model_name}` | Model config metadata. |
| `/api/models/remote-code-scan` | Scan custom-code model repos before `trust_remote_code`. |
| `/api/models/discard-remote-code` | Discard remote-code approval/cache state. |
| `/api/models/loras` | LoRA adapter discovery. |
| `/api/models/loras/{lora_path}/base-model` | Infer LoRA base model. |
| `/api/models/check-vision/{model_name}` | Vision model detection. |
| `/api/models/check-embedding/{model_name}` | Embedding model detection. |
| `/api/models/kv-cache-estimate` | Estimate KV cache needs for context/cache/parallel settings. |
| `/api/models/gguf-variants` | List GGUF variants in an HF repo; reports `has_vision`, default variant, and context when known. |
| `/api/models/cached-gguf` | Cached GGUF files. |
| `/api/models/cached-models` | Cached model inventory. |
| `/api/models/delete-cached` | Delete cached model entries. |
| `/api/models/checkpoints` | Training-output checkpoint discovery. |
| `/api/models/export-size` | Estimate export size; route deep export details to `../model-export/SKILL.md`. |

GGUF-specific triage usually starts with `/api/models/gguf-variants`, `/api/models/kv-cache-estimate`, `/api/inference/validate`, `/api/inference/load`, `/api/inference/load-progress`, and `/api/inference/status`.

## Providers

`/api/providers` manages external provider configurations. API keys are encrypted in transit for tests/model listing and are not stored as raw provider secrets in provider metadata.

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/providers/public-key` | RSA public key PEM and fingerprint for client-side API key encryption. |
| `GET` | `/api/providers/registry` | Supported provider types and defaults. |
| `GET` | `/api/providers/pricing` | Per-MTok pricing snapshot for UI cost display. |
| `GET` | `/api/providers/` | Saved provider configurations. |
| `POST` | `/api/providers/` | Create provider config. |
| `PUT` | `/api/providers/{provider_id}` | Update display/base/enabled fields. |
| `DELETE` | `/api/providers/{provider_id}` | Delete provider config. |
| `POST` | `/api/providers/test` | Lightweight connection test. Custom providers require base URL and model ID. |
| `POST` | `/api/providers/models` | List provider models, using curated lists when appropriate. |

Provider troubleshooting starts with registry, public-key fingerprint mismatch, encrypted key refresh, base URL, model ID, credentials, and provider-specific model filters.

## RAG Routes

RAG is single-tenant behind auth. If `sqlite-vec` cannot load, routes mount but return `503` with a clear unavailable message.

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/rag/knowledge-bases` | List KBs and document counts. |
| `POST` | `/api/rag/knowledge-bases` | Create KB. |
| `PATCH` | `/api/rag/knowledge-bases/{kb_id}` | Rename/update KB metadata. |
| `DELETE` | `/api/rag/knowledge-bases/{kb_id}` | Delete KB and associated docs/indexes. |
| `POST` | `/api/rag/knowledge-bases/{kb_id}/documents` | Upload a document to a KB and start ingestion. |
| `GET` | `/api/rag/knowledge-bases/{kb_id}/documents` | List KB documents. |
| `POST` | `/api/rag/threads/{thread_id}/documents` | Attach document to a chat thread. |
| `GET` | `/api/rag/threads/{thread_id}/documents` | List thread documents. |
| `POST` | `/api/rag/projects/{project_id}/documents` | Attach document to a chat project. |
| `GET` | `/api/rag/projects/{project_id}/documents` | List project documents. |
| `DELETE` | `/api/rag/documents/{document_id}` | Delete doc and stored upload. |
| `GET` | `/api/rag/jobs/{job_id}` | Ingestion job status. |
| `GET` | `/api/rag/jobs/{job_id}/events` | SSE ingestion events; emits `[DONE]`. |
| `POST` | `/api/rag/search` | Search KB/thread/project scopes using `hybrid`, `lexical`, or `dense` mode. |
| `GET` | `/api/rag/documents/{document_id}/preview-target` | Resolve citation preview metadata. |
| `GET` | `/api/rag/documents/{document_id}/file-url` | Mint short-lived signed preview URL. |
| `GET` | `/api/rag/documents/{document_id}/file-signed` | Serve source file through HMAC token for PDF/text preview. |

Allowed upload extensions are controlled by RAG config. Stored filenames are sanitized, empty files are rejected, source-file preview URLs are short-lived and signed, and file serving is confined to the RAG uploads root.

## Data Recipe Routes

Data recipe endpoints power visual dataset creation and validation. Keep code-first training workflows in `../core-training/SKILL.md`, but use these routes for Studio runtime diagnosis.

Key groups:

- `/api/data-recipe/seed/inspect`: inspect Hugging Face dataset previews by repo/split/subset/token.
- `/api/data-recipe/seed/upload-unstructured-file`: upload `.txt`, `.md`, `.pdf`, or `.docx` source material for unstructured recipe seeds; extracts text to server-owned storage.
- `/api/data-recipe/seed/inspect-upload`: inspect uploaded unstructured files or generated chunks.
- `/api/data-recipe/jobs`: create visual recipe jobs. Jobs validate recipe columns, execution type (`preview` or `full`), run config, and may mint a temporary internal API key for local provider calls.
- `/api/data-recipe/jobs/{job_id}/status`: current status.
- `/api/data-recipe/jobs/current`: active job.
- `/api/data-recipe/jobs/{job_id}/cancel`: cancel job.
- `/api/data-recipe/jobs/{job_id}/analysis`: analysis once ready.
- `/api/data-recipe/jobs/{job_id}/dataset`: generated dataset rows with pagination.
- `/api/data-recipe/jobs/{job_id}/publish`: publish completed full-run artifacts to a dataset repo.
- `/api/data-recipe/jobs/{job_id}/events`: SSE job events.
- `/api/data-recipe/validate`: validate visual recipe structure.
- `/api/data-recipe/mcp/tools`: list MCP tools usable by data recipe flows.

## Settings and Llama Maintenance

Settings:

| Route | Purpose |
| --- | --- |
| `GET/PUT /api/settings/upload-limit` | Read/update upload size limit within configured min/max bounds. |
| `GET/PUT /api/settings/helper-precache` | Read/update Helper LLM GGUF pre-cache. Can be disabled by env. |
| `GET/PUT /api/settings/personalization` | UI profile/theme/language/avatar settings. |

llama.cpp maintenance:

| Route | Purpose |
| --- | --- |
| `GET /api/llama/update-status?force_refresh=false` | Check prebuilt support, installed/latest tag, age, staleness, update size, and job state. |
| `POST /api/llama/update` | Start download and atomic swap to the latest supported prebuilt. |

llama.cpp freshness checks run off the startup critical path and are cached; failure to check should not block Studio. Update routes can fetch network resources and mutate the installed llama.cpp tree, so ask before triggering them for a user.

## System and Frontend Behavior

Startup behavior relevant to agents:

- `/api/health` exposes `status`, `service`, and a `studio_root_id` discriminator, not the raw install path.
- Frontend static files are mounted when a built `frontend/dist/index.html` can be resolved. Use `--api-only` to skip UI serving.
- Startup seeds hardware state, auth defaults, llama.cpp capability/freshness probes, helper pre-cache if enabled, and cleanup of orphaned runs/compiled cache.
- If frontend assets are missing, fix setup or pass `--frontend <dist>` for a valid built frontend; do not point at source-only frontend files.

## API Debugging Checklist

1. `GET /api/health` first; verify intended port and install identity.
2. If using a coding agent, test the bearer key with `GET /v1/models`.
3. Use `/api/inference/status` to confirm backend type (`is_gguf`, loaded model, context, tools/reasoning support).
4. Use `/api/inference/validate` before load when diagnosing model identifier, GGUF variant, LoRA, vision, or remote-code issues.
5. Use `/api/models/gguf-variants` and `/api/models/kv-cache-estimate` for GGUF/context/cache problems.
6. Use `/api/providers/test` and `/api/providers/models` for external provider failures.
7. Use `/api/rag/jobs/{job_id}` and `/api/rag/jobs/{job_id}/events` for RAG ingestion failures.
8. Use `/api/system/hardware` and `/api/system/gpu-visibility` for device detection problems.

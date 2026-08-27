# Endpoint Reference

LiteLLM exposes many providers through OpenAI-format SDK helpers and proxy routes. Select the endpoint family first, then verify provider support and model naming.

## Normalized SDK Endpoints

| Workload | SDK entry points | Common proxy route | Notes |
| --- | --- | --- | --- |
| Chat completions | `litellm.completion`, `litellm.acompletion` | `POST /v1/chat/completions` | Accepts OpenAI-format `messages`; provider transforms live under chat provider modules. |
| Text completions | `litellm.text_completion` | `POST /v1/completions` | Prompt-style endpoint; many modern providers prefer chat or responses. |
| Embeddings | `litellm.embedding`, `litellm.aembedding` | `POST /v1/embeddings` | Provider must have embedding support; multimodal embeddings are provider-specific. |
| Responses | responses helpers / OpenAI-compatible client against proxy | `POST /v1/responses`, retrieve/update/delete/cancel routes when provider supports them | Supports OpenAI-compatible responses plus provider-specific implementations. Streaming iterator behavior is separately implemented. |
| Image generation/edit/variation | image helpers or OpenAI-compatible client against proxy | `POST /v1/images/generations`, `/v1/images/edits`, `/v1/images/variations` | Image edit commonly needs multipart files and correct MIME types. |
| Audio transcription/speech | transcription and speech helpers or proxy | `POST /v1/audio/transcriptions`, `/v1/audio/speech` | Audio files require supported MIME/type and provider-specific model support. |
| Files | file helpers or OpenAI-compatible client against proxy | `POST /v1/files`, `GET /v1/files`, `DELETE /v1/files/{file_id}`, content routes | Providers differ on purpose, upload shape, and returned IDs. |
| Batches | batch helpers or OpenAI-compatible client against proxy | `POST /v1/batches`, list/retrieve/cancel routes | Often depends on uploaded files; credential-backed native tests may be skipped. |
| Rerank | rerank helpers / proxy rerank route | `POST /rerank` or provider-compatible route | LiteLLM maps Cohere-style inputs to providers including Cohere, Jina, Vertex AI, Bedrock, DashScope, Together, Voyage, NVIDIA NIM, infinity, hosted vLLM, DeepInfra, and Watsonx where implemented. |
| OCR | OCR helper / proxy OCR route | `POST /v1/ocr` or provider-specific proxy route | Implementations include Mistral, Azure AI, Vertex AI, and Reducto-style flows. |
| Search | search helper / proxy search route | `POST /v1/search` or provider-specific route | Provider modules include Brave, Tavily, Exa, Firecrawl, Linkup, Perplexity, You.com, DataForSEO, searchapi, SearXNG, Tinyfish, and related search providers. |
| Vector stores | vector store helpers / proxy vector store routes | `/v1/vector_stores`, `/v1/vector_stores/{id}`, search/file routes | Providers include OpenAI/Azure, Vertex AI, Bedrock, Gemini, Milvus, PG Vector, S3 Vectors, RAGFlow, and related managed stores. |
| Containers | container helpers / proxy container routes | `/v1/containers` and item routes | Container ownership and cleanup semantics are provider-specific; OpenAI and Azure modules are present. |

## Provider Endpoint Modules To Expect

- `litellm/llms/<provider>/chat`, `completion`, `embed`, `responses`, `image_generation`, `image_edit`, `audio_transcription`, `text_to_speech`, `files`, `batches`, `rerank`, `ocr`, `search`, `vector_stores`, or `containers` indicate provider support for that family.
- Base endpoint contracts live under `litellm/llms/base_llm/*`; concrete providers override URL building, environment validation, request transforms, and response transforms.
- Proxy routes are grouped by endpoint family: response API, image, files, batches, rerank, OCR, search, vector store, vector store files, container, realtime, fine tuning, and provider-specific pass-through endpoints.

## Responses API

Use responses when the caller needs OpenAI Responses API semantics such as `input`, `instructions`, response IDs, tool output continuation, or response streaming. Provider implementations are not identical:

- OpenAI and Azure responses paths handle native response resources and related state.
- OpenRouter and xAI implement Responses API compatibility with known parameter differences; for example unsupported fields can be dropped by provider configs when `drop_params` behavior applies.
- LiteLLM-proxy and OpenAI-like providers can expose responses through OpenAI-compatible base URLs when configured.
- Streaming has dedicated iterator tests; when debugging stream failures, check event type, final usage chunks, and whether the provider supports native WebSocket or SSE for that endpoint.

## Files And Batches

For batch workflows, validate this sequence:

1. Upload a JSONL file with the provider-required `purpose` and content type.
2. Use the returned file ID in a batch create request for a supported endpoint, usually chat completions or embeddings.
3. Poll retrieve/list until terminal status.
4. Retrieve output/error files if the provider supports them.

File APIs are commonly where MIME, purpose, and provider ID formats diverge. Do not reuse an OpenAI file ID against Azure, Anthropic, Bedrock, Gemini, or Vertex APIs unless the route explicitly owns that translation.

## Images And Audio

Images and audio often require multipart requests. If a call works in an SDK but not through proxy, compare:

- `Content-Type` boundary and form field names.
- `model` prefix and endpoint family.
- File extension and MIME type.
- Whether the provider supports generation, edit, variation, transcription, or speech for that exact model.
- Whether `response_format`, `size`, `quality`, `voice`, `language`, or timestamp options are supported or should be dropped.

## Rerank, OCR, Search, Vector Stores, Containers

These are not universal OpenAI chat parameters. Use dedicated endpoint families:

- Rerank expects query/documents/top_n-like shape and provider-specific mapping.
- OCR expects document/image input, often file URL, uploaded file, or base64 content.
- Search expects query plus provider-specific filters, recency, domain, or result-count options.
- Vector stores require ownership checks and provider-managed IDs; search/retrieve/create/list/update/delete routes may have different permission requirements under the proxy.
- Containers can own execution or response resources; response streaming plus container ownership can create lifecycle edge cases.

## Validation Checklist

- Confirm the model prefix resolves to the intended provider.
- Confirm the provider has a module for the endpoint family.
- Use the normalized helper/route before pass-through unless native provider shape is required.
- Verify required env vars or explicit credentials are present at runtime.
- If a parameter is unsupported, decide whether to fail fast or use `drop_params=True` intentionally.
- For proxy requests, test with an OpenAI-compatible client or `curl` against the route the application will actually call.

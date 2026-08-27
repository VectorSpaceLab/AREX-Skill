---
name: providers-and-endpoints
description: "Use when mapping LiteLLM provider/model prefixes, selecting SDK or
  proxy endpoint families, translating OpenAI-format parameters across
  providers, or diagnosing pass-through endpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# LiteLLM Providers And Endpoints

Use this sub-skill when the work is about which provider prefix, model string, helper function, proxy route, or pass-through route should handle a request. Route basic SDK invocation patterns to `sdk-core`; route proxy deployment, auth, keys, and serving operations to `proxy-server`; route load balancing and fallback policy to `routing`; route MCP/A2A tool workflows to `agent-tools`.

## Fast Routing

- Chat completions: call `litellm.completion()` / `litellm.acompletion()` or proxy `POST /v1/chat/completions`; choose a model prefix such as `openai/`, `azure/`, `anthropic/`, `bedrock/`, `vertex_ai/`, `gemini/`, `openrouter/`, or an OpenAI-compatible provider prefix.
- Text completions: call `litellm.text_completion()` or proxy `POST /v1/completions`; only use models/providers that still support completion-style prompts.
- Embeddings: call `litellm.embedding()` / `litellm.aembedding()` or proxy `POST /v1/embeddings`; confirm the provider has an embedding transformer, not only chat.
- Responses API: use the responses helpers or proxy `POST /v1/responses`; check provider support because OpenAI, Azure, OpenRouter, xAI, Perplexity, hosted vLLM, Volcengine, Databricks, Manus, ChatGPT, and LiteLLM-proxy paths differ.
- Images, audio, files, batches, rerank, OCR, search, vector stores, and containers: use the endpoint catalog in `references/endpoint-reference.md` before choosing a model string or proxy route.
- Raw provider APIs: use pass-through only when LiteLLM’s normalized endpoint does not expose the provider feature or when provider-native request/response shape must be preserved; see `references/pass-through.md`.

## Operating Rules

1. Start from endpoint family, then provider support, then model prefix. Do not assume a chat-capable model supports embeddings, rerank, images, files, batches, responses, or vector stores.
2. Prefer OpenAI-compatible request shape at LiteLLM boundaries. Provider-specific controls can usually be passed as keyword arguments, request JSON fields, or `litellm_params`, but unsupported parameters may be rejected or dropped depending on `drop_params`.
3. Keep credentials outside code. Use provider environment variables or explicit `api_key`, `api_base`, `base_url`, and `api_version` only in local config or runtime calls.
4. For Azure, treat deployment name, API base, and API version as separate inputs. A working OpenAI model name is not enough.
5. For pass-through, validate target URL, forwarded headers, subpath inclusion, provider route shape, and auth separately from LiteLLM model routing.

## References

- `references/endpoint-reference.md`: endpoint families, SDK helpers, proxy routes, and provider caveats.
- `references/provider-routing.md`: model prefix selection, credentials, `api_base`/`base_url`, Azure, and parameter forwarding.
- `references/pass-through.md`: generic and provider pass-through setup, local mock target, and header debugging.
- `references/troubleshooting.md`: diagnosis playbooks for unsupported endpoint/model pairs, dropped params, MIME issues, streaming/container edge cases, and pass-through failures.
- `scripts/mock_passthrough_target.py`: safe local HTTP target for pass-through shape and header debugging.

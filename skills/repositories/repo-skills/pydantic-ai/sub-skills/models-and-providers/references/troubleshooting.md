# Models and Providers Troubleshooting

Start with the no-network helper:

```bash
python scripts/check_optional_provider.py openai:gpt-5.2 anthropic:claude-opus-4-6 google:gemini-3-pro-preview
```

It checks provider-prefix parsing, optional imports, and expected environment-variable names. It does not make network calls or validate credentials.

## Missing Provider Prefix

Symptoms:

- `ValueError` about needing a provider prefix;
- an agent/model string that works in another library but not in Pydantic AI;
- embedding construction fails before any network request.

Fix:

- Use `provider:model-name`, for example `openai:gpt-5.2`, `anthropic:claude-opus-4-6`, `google:gemini-3-pro-preview`, `openrouter:google/gemini-3-pro-preview`, or `openai:text-embedding-3-small` for embeddings.
- Use `known_model_names()` only as a known-name catalog, not as a complete provider availability guarantee.
- Instantiate a concrete model/provider class when using a custom base URL or provider not covered by string inference.

## Missing Optional SDK or Extra

Symptoms:

- `ImportError` or `ModuleNotFoundError` for `openai`, `anthropic`, `google.genai`, `boto3`, `groq`, `mistralai`, `cohere`, `xai_sdk`, `huggingface_hub`, `voyageai`, `sentence_transformers`, `ddgs`, `tavily`, `exa_py`, or `markdownify`;
- code works with `pydantic-ai` but fails with `pydantic-ai-slim`.

Fix:

- Install the smallest extra from `provider-installation.md`, such as `pydantic-ai-slim[openai]`, `[anthropic]`, `[google]`, `[bedrock]`, `[groq]`, `[mistral]`, `[cohere]`, `[xai]`, `[huggingface]`, `[voyageai]`, `[sentence-transformers]`, `[duckduckgo]`, `[tavily]`, `[exa]`, or `[web-fetch]`.
- For OpenAI-compatible providers, the missing SDK is often still `openai`; the provider-specific failure may instead be a missing env var such as `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`, or `TOGETHER_API_KEY`.
- Re-run the diagnostic helper after installing; do not assume installation proves credentials or live access.

## API Keys and Provider Configuration

Symptoms:

- provider constructor raises `UserError` requesting an environment variable;
- HTTP 401/403 after import succeeds;
- a custom endpoint gets a placeholder key or wrong base URL.

Checklist:

- OpenAI: `OPENAI_API_KEY`; optional `OPENAI_BASE_URL`.
- Azure OpenAI: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `OPENAI_API_VERSION`, or explicit `AzureProvider(...)` values.
- Anthropic: `ANTHROPIC_API_KEY` or explicit client/provider.
- Google Gemini API: `GOOGLE_API_KEY` preferred; `GEMINI_API_KEY` is accepted for compatibility.
- Google Cloud: `GOOGLE_API_KEY` or default credentials plus `GOOGLE_CLOUD_PROJECT`; optional `GOOGLE_CLOUD_LOCATION`.
- Bedrock: `AWS_BEARER_TOKEN_BEDROCK` or standard AWS credentials plus region such as `AWS_DEFAULT_REGION`.
- Groq: `GROQ_API_KEY`; optional `GROQ_BASE_URL`.
- xAI: `XAI_API_KEY`.
- Cohere: `CO_API_KEY`; optional `CO_BASE_URL`.
- Mistral: `MISTRAL_API_KEY`.
- Hugging Face: `HF_TOKEN`.
- Gateway: `PYDANTIC_AI_GATEWAY_API_KEY` or `PAIG_API_KEY`; optional gateway base URL.

If the application passes explicit SDK clients, inspect the client constructor instead of environment variables. Pydantic AI will not own cleanup for caller-owned clients.

## Google, Vertex, and Gateway Naming

Symptoms:

- deprecation warnings for `google-gla:`, `google-vertex:`, or `vertexai:`;
- a Google model works through one API but not the other;
- project/location errors appear with Google Cloud.

Fix:

- Use `google:` for Gemini API key usage.
- Use `google-cloud:` for Google Cloud / Vertex AI-style usage.
- Treat `google-gla:` as deprecated in favor of `google:`.
- Treat `google-vertex:` and `vertexai:` as deprecated aliases in favor of `google-cloud:`.
- Gateway-prefixed Google Cloud providers may normalize differently; check whether the model string starts with `gateway/` and whether gateway credentials are configured.

## Profile, Schema, and Output Compatibility

Symptoms:

- structured output fails for a model that accepts text;
- JSON schema is rejected by one provider but accepted by another;
- tool or output schemas break when routing through OpenRouter/Gateway/custom endpoints.

Fix:

- Remember the model class sends requests, the provider authenticates/routes, and the profile describes schema/output/tool quirks.
- Prefer provider-inferred profiles for known model names.
- Pass `profile=` only when a custom or proxy endpoint needs a different schema transformer or capability set.
- Route final-output mode choices to `outputs-and-messages`; use this sub-skill only to select the model/provider/profile that supports the chosen output mode.

## Fallback Timing and Retries

Symptoms:

- `FallbackModel` waits a long time before trying the next model;
- a fallback never happens after a semantically bad response;
- fallback loses custom auth/base URL settings.

Fix:

- Provider SDK retries occur before `FallbackModel` receives an exception. Set provider SDK retry counts such as `max_retries=0` on each custom SDK client when immediate fallback is required.
- Configure each child model separately; `FallbackModel` does not share provider auth, base URL, retries, or profiles across children.
- Use `fallback_on=(ModelAPIError,)` for default API-error fallback, add exception types for rate-limit/timeouts as needed, or add a `ModelResponse`-typed response handler for semantic rejection.
- Wrap individual child models with `ConcurrencyLimitedModel` when each provider has a separate quota; wrap the whole fallback only when limiting the whole sequence is desired.

## Native Tool Failures

Symptoms:

- `UserError` says a model does not support a requested native tool;
- native web search works on OpenAI Responses but not OpenAI Chat;
- Google native tools conflict with function tools or structured output;
- MCP server tool configuration is accepted by one provider and rejected by another.

Fix:

- Use `openai-responses:` for OpenAI native web search, file search, and image generation.
- Verify support in `native-tools-and-embeddings.md`; unsupported providers should use common tools or provider-adaptive capabilities.
- Native tools execute provider-side; do not expect local files, local Python packages, or local network routes to be visible.
- For `MCPServerTool`, route local MCP client/server setup to `mcp-and-integrations` and keep this sub-skill focused on provider-native remote server configuration.
- Credentialed file upload and cloud verification scripts were excluded from runtime instructions; require explicit user approval before running any live upload or provider-resource mutation.

## Embedding Failures

Symptoms:

- embedding string lacks a prefix;
- vector dimensions change after a model switch;
- local sentence-transformers install is slow or platform-sensitive;
- managed embedding requests fail with auth/region errors.

Fix:

- Use prefixed strings such as `openai:text-embedding-3-small`, `google:gemini-embedding-001`, `cohere:embed-v4.0`, `voyageai:voyage-4`, `bedrock:amazon.titan-embed-text-v2:0`, or `sentence-transformers:MODEL_ID`.
- Install the matching extra and verify imports first.
- Re-embed and re-index documents after changing embedding model, provider, or dimensions.
- Use `TestEmbeddingModel` for deterministic tests and `Embedder.override(model=...)` for temporary test overrides.

## HTTP Client Lifecycle

Symptoms:

- unclosed client warnings;
- requests fail after a provider was previously closed;
- long-running apps leak connections.

Fix:

- Use `async with Agent(...)` or `async with model/provider` when Pydantic AI creates the HTTP client.
- If passing an explicit `http_client` or SDK client, close it in application code.
- Avoid constructing fresh provider/model clients per request in hot paths; reuse configured models when possible.

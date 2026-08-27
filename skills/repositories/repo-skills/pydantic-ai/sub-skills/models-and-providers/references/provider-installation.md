# Provider Installation and Optional Dependencies

`pydantic-ai` installs the core package plus broad model-provider dependencies. Use `pydantic-ai-slim[...]` when you want the smallest dependency set. Optional cloud/provider extras were intentionally not installed during this skill extraction, so this reference describes what to install and how to diagnose locally without claiming live access.

## Smallest Extra by Task

| Task or prefix | Install extra | Main import checked | Typical configuration signals |
| --- | --- | --- | --- |
| `openai:`, `openai-chat:`, `openai-responses:` | `pydantic-ai-slim[openai]` | `openai` | `OPENAI_API_KEY`; optional `OPENAI_BASE_URL`; custom `AsyncOpenAI` for retries/base URL. |
| `azure:` | `pydantic-ai-slim[openai]` | `openai` | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `OPENAI_API_VERSION`, or explicit `AzureProvider(...)`. |
| `anthropic:` | `pydantic-ai-slim[anthropic]` | `anthropic` | `ANTHROPIC_API_KEY` or explicit `AnthropicProvider(api_key=...)`; Anthropic Foundry uses separate provider configuration. |
| `google:` | `pydantic-ai-slim[google]` | `google.genai` | `GOOGLE_API_KEY` preferred; `GEMINI_API_KEY` is accepted for compatibility. |
| `google-cloud:` | `pydantic-ai-slim[google]` | `google.genai` | `GOOGLE_API_KEY` or Google default credentials plus `GOOGLE_CLOUD_PROJECT`; optional `GOOGLE_CLOUD_LOCATION`. |
| `vertexai:` / `google-vertex:` legacy | `pydantic-ai-slim[vertexai]` for legacy `GoogleVertexProvider`; prefer `google-cloud:` with `pydantic-ai-slim[google]` for current `GoogleModel` paths | `google.auth`, `requests` or `google.genai` depending path | Expect deprecation warnings for old prefixes; verify whether the code uses legacy provider classes or current `GoogleCloudProvider`. |
| `bedrock:` | `pydantic-ai-slim[bedrock]` | `boto3` | `AWS_BEARER_TOKEN_BEDROCK` or standard AWS credentials such as `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_DEFAULT_REGION`. |
| `groq:` | `pydantic-ai-slim[groq]` | `groq` | `GROQ_API_KEY`; optional `GROQ_BASE_URL`. |
| `mistral:` | `pydantic-ai-slim[mistral]` | `mistralai` | `MISTRAL_API_KEY`. |
| `cohere:` | `pydantic-ai-slim[cohere]` | `cohere` | `CO_API_KEY`; optional `CO_BASE_URL`. |
| `xai:` | `pydantic-ai-slim[xai]` | `xai_sdk` | `XAI_API_KEY`; optional `XaiProvider(api_host=...)`. |
| `cerebras:` | `pydantic-ai-slim[openai]` plus provider-specific package needs from current metadata when required | `openai` | `CEREBRAS_API_KEY`. |
| `deepseek:` | `pydantic-ai-slim[openai]` | `openai` | `DEEPSEEK_API_KEY`. |
| `fireworks:` | `pydantic-ai-slim[openai]` | `openai` | `FIREWORKS_API_KEY`. |
| `github:` | `pydantic-ai-slim[openai]` | `openai` | `GITHUB_API_KEY`. |
| `heroku:` | `pydantic-ai-slim[openai]` | `openai` | `HEROKU_INFERENCE_KEY`; optional `HEROKU_INFERENCE_URL`. |
| `litellm:` | `pydantic-ai-slim[openai]` and any LiteLLM-side provider packages configured by the application | `openai` | LiteLLM reads provider-specific env vars; pass explicit provider config for deterministic behavior. |
| `moonshotai:` | `pydantic-ai-slim[openai]` | `openai` | `MOONSHOTAI_API_KEY`. |
| `nebius:` | `pydantic-ai-slim[openai]` | `openai` | `NEBIUS_API_KEY`. |
| `ollama:` | `pydantic-ai-slim[openai]` | `openai` | `OLLAMA_BASE_URL` required unless passed; `OLLAMA_API_KEY` for Ollama Cloud. |
| `openrouter:` | `pydantic-ai-slim[openrouter]` or `pydantic-ai-slim[openai]` depending package version | `openai` | `OPENROUTER_API_KEY`; optional `OPENROUTER_APP_URL`, `OPENROUTER_APP_TITLE`. |
| `ovhcloud:` | `pydantic-ai-slim[openai]` | `openai` | `OVHCLOUD_API_KEY`. |
| `sambanova:` | `pydantic-ai-slim[openai]` | `openai` | `SAMBANOVA_API_KEY`; optional `SAMBANOVA_BASE_URL`. |
| `together:` | `pydantic-ai-slim[openai]` | `openai` | `TOGETHER_API_KEY`. |
| `vercel:` | `pydantic-ai-slim[openai]` | `openai` | `VERCEL_AI_GATEWAY_API_KEY` or `VERCEL_OIDC_TOKEN`. |
| `huggingface:` | `pydantic-ai-slim[huggingface]` | `huggingface_hub` | `HF_TOKEN`; sometimes explicit provider name or base URL. |
| `outlines-*` local models | matching `pydantic-ai-slim[outlines-transformers]`, `[outlines-llamacpp]`, `[outlines-mlxlm]`, `[outlines-sglang]`, or `[outlines-vllm-offline]` | `outlines` and backend packages | Deprecated and platform-sensitive; avoid for new public examples unless specifically requested. |
| `gateway/...:` | extra for the upstream provider plus gateway package baseline | provider-dependent | `PYDANTIC_AI_GATEWAY_API_KEY` or `PAIG_API_KEY`; optional gateway base URL. |

Use the bundled diagnostic helper before broad installs:

```bash
python scripts/check_optional_provider.py openai:gpt-5.2 anthropic:claude-opus-4-6 google:gemini-3-pro-preview
```

The helper only imports modules and reports missing environment variables; it never sends network requests or validates credentials.

## Embedding Extras

| Embedding prefix | Install extra | Main import | Notes |
| --- | --- | --- | --- |
| `openai:` and OpenAI-compatible embedding providers | `pydantic-ai-slim[openai]` | `openai` | `OpenAIEmbeddingModel` can use OpenAI-compatible providers through the same provider system. |
| `google:` / `google-cloud:` | `pydantic-ai-slim[google]` | `google.genai` | Current Google embedding path. |
| `cohere:` | `pydantic-ai-slim[cohere]` | `cohere` | Uses `CO_API_KEY`. |
| `voyageai:` | `pydantic-ai-slim[voyageai]` | `voyageai` | Uses `VOYAGE_API_KEY`; package may be constrained by Python version. |
| `bedrock:` | `pydantic-ai-slim[bedrock]` | `boto3` | Uses AWS credentials/region. |
| `sentence-transformers:` | `pydantic-ai-slim[sentence-transformers]` | `sentence_transformers` | Local/private embeddings; can be large and platform-sensitive. |

## Common Tool Extras

Common tools are Python-executed function tools, not provider-native tools. Route tool schema design to `tools-and-toolsets`, but install/credential questions often start here.

| Common tool | Install extra | Import | Credential/config |
| --- | --- | --- | --- |
| DuckDuckGo search | `pydantic-ai-slim[duckduckgo]` | `ddgs` | No API key for typical usage, but network access is needed at runtime. |
| Web fetch | `pydantic-ai-slim[web-fetch]` | `markdownify` | Network access at runtime; SSRF protection is built into the helper. |
| Tavily search | `pydantic-ai-slim[tavily]` | `tavily` | `TAVILY_API_KEY` or explicit client/key. |
| Exa tools/toolset | `pydantic-ai-slim[exa]` | `exa_py` | `EXA_API_KEY` or explicit client/key. |

## Install Strategy

- Prefer one minimal extra: `pydantic-ai-slim[openai]`, `pydantic-ai-slim[anthropic]`, or `pydantic-ai-slim[google]` for simple apps.
- Combine only the providers actually used: `pydantic-ai-slim[openai,anthropic,google]`.
- Use full `pydantic-ai` when broad provider coverage is more important than dependency size.
- Add `logfire`, `mcp`, `fastmcp`, `ui`, `ag-ui`, `web`, `retries`, and durable-execution extras only when those integration surfaces are required; route details to `mcp-and-integrations` or `cli-and-apps`.
- Do not install `all`-style broad extras in a troubleshooting response unless the user explicitly prefers convenience over minimal dependencies.

## Source Scripts Excluded from Runtime Use

Credentialed source scripts for Bedrock access, Vertex/GCS verification, and uploaded test files were intentionally not bundled as runnable skill scripts. They require live cloud credentials, network access, cloud resources, or mutable uploads. Use this skill's troubleshooting checklist and no-network diagnostic helper first; run cloud verification only under a separate user-approved workflow with explicit credentials and target resources.

# LLM Troubleshooting

Use this matrix when CrewAI LLM setup, provider routing, credentials, streaming, tool calls, structured output, or multimodal compatibility fails.

## Fast Triage

1. Identify the model string exactly as CrewAI sees it: `provider/model` or unprefixed.
2. Run the offline checker: `python scripts/check_llm_config.py --model <model> --provider <provider-if-explicit> --base-url <url-if-any>`.
3. Confirm required environment variable names are set, without printing secret values.
4. Construct a minimal `LLM(...)` object before attaching it to agents or crews.
5. Test non-streaming, text-only behavior before adding tools, response models, files, or crew streaming.

## Symptom Matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `OPENAI_API_KEY is required` | OpenAI native provider was selected, often because the model was unprefixed or used `openai/...`. | Set `OPENAI_API_KEY`, pass `api_key`, or use the intended provider prefix/base URL. For local OpenAI-compatible endpoints, pass a placeholder key if the server requires one. |
| `API key required for deepseek/openrouter/cerebras/dashscope` | OpenAI-compatible provider requires its provider-specific key. | Set `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`, `CEREBRAS_API_KEY`, or `DASHSCOPE_API_KEY`, or choose `ollama`/`hosted_vllm` for local no-key-style providers. |
| Azure endpoint required | `model="azure/..."` was selected but no endpoint resolved. | Set `AZURE_ENDPOINT`, `AZURE_OPENAI_ENDPOINT`, or `AZURE_API_BASE`; pass `api_version` or rely on default `2024-06-01`. |
| Google/Gemini auth error | Gemini API key and Vertex/ADC settings are mixed or absent. | Use `GOOGLE_API_KEY`/`GEMINI_API_KEY` for Gemini API, or Vertex settings with project/location and ADC; do not assume API keys work for all Vertex paths. |
| Snowflake token/account URL error | Snowflake provider requires both a token and account URL/identifier. | Set one token env var (`SNOWFLAKE_PAT`, `SNOWFLAKE_TOKEN`, `SNOWFLAKE_JWT`) and one account env var (`SNOWFLAKE_ACCOUNT_URL`, `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_ACCOUNT_ID`, `SNOWFLAKE_ACCOUNT_IDENTIFIER`). |
| LiteLLM import error | Model prefix did not route to native provider and `crewai[litellm]` is not installed. | Prefer a native provider prefix or install `crewai[litellm]` intentionally. For local servers, use OpenAI-compatible native providers where possible. |
| Unprefixed custom model routes to OpenAI | Unknown unprefixed models default toward OpenAI inference. | Use `provider="ollama"`, `provider="hosted_vllm"`, `model="openai/<name>"` plus `base_url`, or another explicit provider prefix. |
| Wrong OpenAI-compatible base URL | Endpoint lacks `/v1`, points at a UI page, or includes `/chat/completions` when only root is expected. | Use the API root, usually ending in `/v1`. For Ollama, CrewAI normalizes `OLLAMA_HOST` to `/v1`; for Snowflake, pass account URL or Cortex root, not `/chat/completions`. |
| Tool calls ignored or malformed | Model/provider does not support function calling, tool schema is incompatible, or `function_calling_llm` is not configured for tools. | Choose a tool-capable model, simplify tool schemas, use safe names, and test `LLM.call(..., tools=..., available_functions=...)` without streaming first. |
| Streaming produces empty chunks or no final content | Provider sends usage-only/empty chunks, local server lacks streaming support, or consumer expects every chunk to contain text. | Test with `stream=False`; then enable streaming. Treat tool chunks and text chunks separately. For local servers, confirm streaming support. |
| Structured output validation fails | `response_format` is unsupported by the model/API, schema is too complex, or streaming partial JSON is being parsed. | Use a provider/model with schema support, simplify the Pydantic model, lower temperature, or use non-streaming structured calls. |
| Multimodal request fails | Selected model/provider does not support the file modality or cannot combine modality with tools. | Route file payload work to [../../files-and-multimodal/SKILL.md](../../files-and-multimodal/SKILL.md); switch to a multimodal-capable model or split file understanding and tool work across models. |
| Context-window exceeded | Prompt, memory, files, or task context exceed model limit. | Choose a larger-context model, reduce context, chunk documents, set realistic `max_tokens`, or override custom LLM context-window size only when true. |
| Rate-limit failures | Provider quota/RPM exceeded or multiple agents call concurrently. | Set `max_rpm` on agents/crews, reduce concurrency, choose a higher-limit model/provider, and add backoff outside public examples as needed. |
| LiteLLM migration broke Ollama | Old setup relied on LiteLLM `ollama/...` semantics. | Use CrewAI native OpenAI-compatible `ollama/<model>` or `openai/<model>` with `base_url="http://localhost:11434/v1"` and placeholder key. |
| `function_calling_llm` deprecation confusion | Older docs/changelogs mention changes while current signatures still include the field. | Treat it as available in CrewAI 1.14.8a2 but prefer clear, minimal use. Route placement decisions to [../../core-runtime/SKILL.md](../../core-runtime/SKILL.md). |

## Provider Prefix Checklist

- OpenAI native: `openai/<model>` or known unprefixed OpenAI model.
- Anthropic native: `anthropic/<model>` or `claude-...` patterns.
- Gemini native: `gemini/<model>` or `google/<model>`.
- Azure native: `azure/<deployment-or-model>`.
- Bedrock native: `bedrock/<provider.model-id>` or `aws/<provider.model-id>`.
- Snowflake native: `snowflake/<model>`.
- OpenAI-compatible native: `openrouter/...`, `deepseek/...`, `ollama/...`, `ollama_chat/...`, `hosted_vllm/...`, `cerebras/...`, `dashscope/...`.
- LiteLLM fallback: any remaining provider prefix when `crewai[litellm]` is intentionally installed.

## OpenAI-Compatible Local Endpoint Case

For a local endpoint such as Ollama, vLLM, LM Studio, or llama.cpp that exposes `/v1/chat/completions`, use one of these patterns:

```python
from crewai import LLM

llm = LLM(
    model="openai/local-model",
    base_url="http://localhost:8000/v1",
    api_key="dummy",
)
```

or, for CrewAI's built-in local providers:

```python
llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434/v1")
llm = LLM(model="hosted_vllm/meta-llama/Llama-3-8b", base_url="http://localhost:8000/v1")
```

Start with text-only non-streaming calls. Then add `stream=True`. Add tools only if the server implements OpenAI-compatible tool calls.

## Multimodal + Tool-Call Fallback

If a multimodal model can read images but fails tool calls, split responsibilities:

1. Use a multimodal model to summarize or extract facts from file inputs.
2. Pass the text summary to a tool-capable text model for function calling.
3. Use [../../files-and-multimodal/SKILL.md](../../files-and-multimodal/SKILL.md) for file input validation and provider file constraints.
4. Use [../../core-runtime/SKILL.md](../../core-runtime/SKILL.md) to assign the models to agents/tasks or `function_calling_llm`.

## No-Secrets Debugging

Safe diagnostics can print:

- Provider name and model string.
- Which environment variable names are required.
- Whether each required env var is set or missing.
- Base URL host/path category.
- Whether a provider is native, OpenAI-compatible, or LiteLLM fallback.

Unsafe diagnostics must not print:

- Actual API keys, tokens, JWTs, PATs, AWS secret values, or bearer headers.
- Local private filesystem or environment paths.
- Full request payloads containing user secrets or proprietary documents.

## Reference Notes

This troubleshooting reference bundles CrewAI provider behavior and failure cases into runtime guidance. Source tests and docs were reference-only evidence and are not required during future use.

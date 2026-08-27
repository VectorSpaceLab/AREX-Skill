# Model Routing and Provider Setup

## When to read

Read this when chat, search, RAG, image generation, or document workflows fail because GPT Academic cannot call the selected model/provider.

## Provider checklist

1. Pick the model string first, then match the key and endpoint to that provider.
2. Add the model string to `AVAIL_LLM_MODELS` and set `LLM_MODEL` only to one of the available strings.
3. Put secrets in `config_private.py` or environment variables.
4. Use `scripts/inspect_runtime.py --repo-root <checkout>` from the root skill to confirm the loaded model registry and visible plugin groups.

| Provider pattern | Config to verify | Common issue |
| --- | --- | --- |
| OpenAI or OpenAI-compatible | `API_KEY`, optional `API_URL_REDIRECT`, proxy | selected model not supported by endpoint |
| DashScope/Qwen | `DASHSCOPE_API_KEY`, `qwen-*` model | using OpenAI key for Qwen model |
| DeepSeek | `DEEPSEEK_API_KEY`, `deepseek-*` model | model name typo or provider quota |
| GLM/Zhipu | `ZHIPUAI_API_KEY`, `glm-*` model | vision/non-vision model mismatch |
| Claude | `ANTHROPIC_API_KEY`, Claude model name | proxy or regional access failure |
| Azure OpenAI | `AZURE_ENDPOINT`, `AZURE_API_KEY`, deployment/engine config | using public OpenAI model name instead of Azure deployment |
| Ollama | `ollama-*` model and local service | service not running or model not pulled |
| vLLM | `vllm-*` model string and OpenAI-compatible server redirect | external GPU server not running or wrong max-token suffix |
| Local native models | local model path, `LOCAL_MODEL_DEVICE`, quantization | weights missing or CPU too slow |

## Search and RAG model notes

- Search combines a search backend with an LLM. Debug search service failure separately from model failure.
- RAG uses embeddings plus an LLM. A valid chat model key is not always enough; embedding providers may need separate settings.
- Multi-model query can fail if only one of the selected providers is configured. Verify each model separately before comparing.

## Privacy

Never print API key values in logs, generated prompts, or skill artifacts. A no-secret diagnostic may print whether a key is present but must not reveal the value.

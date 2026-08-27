# Model and Retriever Options

## LiteLLM model setup

Use `knowledge_storm.lm.LitellmModel` for new STORM Wiki runs. It accepts LiteLLM model strings such as:

- `openai/gpt-4o-mini`
- `openai/gpt-4o`
- `anthropic/claude-3-5-sonnet-20240620`
- `gemini/gemini-1.5-pro`
- `groq/llama3-70b-8192`
- `ollama_chat/llama3`
- `azure/<deployment-name>` with Azure kwargs

The exact set depends on your installed LiteLLM version and provider configuration.

Basic OpenAI-compatible setup:

```python
import os
from knowledge_storm.lm import LitellmModel

shared_kwargs = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "temperature": 1.0,
    "top_p": 0.9,
}
cheap_lm = LitellmModel(model="openai/gpt-4o-mini", max_tokens=500, **shared_kwargs)
strong_lm = LitellmModel(model="openai/gpt-4o", max_tokens=700, **shared_kwargs)
```

Azure-style setup should pass the deployment model string and explicit endpoint/version kwargs used by your Azure OpenAI service:

```python
azure_kwargs = {
    "api_key": os.getenv("AZURE_API_KEY") or os.getenv("OPENAI_API_KEY"),
    "api_base": os.getenv("AZURE_API_BASE"),
    "api_version": os.getenv("AZURE_API_VERSION"),
    "temperature": 1.0,
    "top_p": 0.9,
}
lm = LitellmModel(model="azure/my-gpt-4o-deployment", max_tokens=700, **azure_kwargs)
```

Older code may show `OpenAIModel` or `AzureOpenAIModel`. Treat those wrappers as legacy compatibility examples, not the default path for new agents.

## Cheap/strong component mapping

STORM is a multi-LM system. Use cheaper/faster models for repetitive research-conversation work and stronger models for structure and article writing.

| STORM component | Config setter | Default helper mapping | Why |
| --- | --- | --- | --- |
| Conversation simulator | `set_conv_simulator_lm` | cheap model, `max_tokens=500` | Splits questions into queries and synthesizes grounded answers many times. |
| Question asker | `set_question_asker_lm` | cheap model, `max_tokens=500` | Generates perspective-guided questions; many short calls. |
| Outline generator | `set_outline_gen_lm` | strong model, `max_tokens=400` | Organizes broad evidence into a useful hierarchy. |
| Article generator | `set_article_gen_lm` | strong model, `max_tokens=700` | Writes citation-bearing sections; quality affects final article. |
| Article polish | `set_article_polish_lm` | strong model, `max_tokens=4000` | Generates a lead/summary and optionally removes duplicates across the full page. |

The bundled helper exposes:

```text
--cheap-model      model for conversation simulator and question asker
--strong-model     default model for outline, article, and polish
--conv-model       optional component override
--question-model   optional component override
--outline-model    optional component override
--article-model    optional component override
--polish-model     optional component override
```

## Common model environment variables

| Provider pattern | Typical env vars | Notes |
| --- | --- | --- |
| `openai/...` or no provider prefix | `OPENAI_API_KEY` | Default helper models use this. |
| `azure/...` | `AZURE_API_KEY` or `OPENAI_API_KEY`, plus `AZURE_API_BASE`, `AZURE_API_VERSION` | Deployment name must match your Azure deployment. You can also pass `--api-key-env`, `--api-base`, and `--api-version` to the helper. |
| `anthropic/...` | `ANTHROPIC_API_KEY` | Use provider-supported model IDs. |
| `gemini/...` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Environment convention depends on your LiteLLM/provider setup. |
| `groq/...` | `GROQ_API_KEY` | Good for low-latency open-weight model serving when quality is adequate. |
| `mistral/...` | `MISTRAL_API_KEY` | Hosted Mistral-compatible endpoint. |
| `deepseek/...` | `DEEPSEEK_API_KEY` | Use current DeepSeek LiteLLM model names. |
| `ollama...` / local endpoints | Usually no API key; may need `api_base` | Ensure the local server is running before actual calls. |

For mixed-provider Python code, configure each `LitellmModel` separately instead of passing one shared key to every component.

## Internet retriever matrix

| Retriever class | Helper `--retriever` | Credentials / args | Optional-package caveats | Notes |
| --- | --- | --- | --- | --- |
| `BingSearch` | `bing` | `BING_SEARCH_API_KEY` or `bing_search_api_key=...` | Base package dependencies only. | Uses Bing Web Search and fetches page snippets. Pass `k=engine_args.search_top_k`. |
| `YouRM` | `you` | `YDC_API_KEY` or `ydc_api_key=...` | Base package dependencies only. | Uses You.com search. Good baseline if you have You.com credentials. |
| `BraveRM` | `brave` | `BRAVE_API_KEY` or `brave_search_api_key=...` | Base package dependencies only. | Uses Brave Search API and returns title, URL, description, and extra snippets when available. |
| `SerperRM` | `serper` | `SERPER_API_KEY` or `serper_search_api_key=...` | Base package dependencies only. | Uses Serper.dev Google-style search. Query params can include `autocorrect`, `num`, and `page`. |
| `DuckDuckGoSearchRM` | `duckduckgo` | No API key. Optional `safe_search` and `region`. | Requires `duckduckgo_search`. | Useful for keyless experiments, but public rate limits and transient failures are common. |
| `TavilySearchRM` | `tavily` | `TAVILY_API_KEY` or `tavily_search_api_key=...` | Requires `tavily-python`. | `include_raw_content=True` can supply longer snippets but may increase response size. |
| `SearXNG` | `searxng` | `SEARXNG_API_URL` or `--searxng-api-url`; optional `SEARXNG_API_KEY`. | Base HTTP dependencies; you must operate or have access to a JSON-capable SearXNG endpoint. | Endpoint must return JSON for `format=json`. |
| `AzureAISearch` | `azure_ai_search` | `AZURE_AI_SEARCH_API_KEY`, `AZURE_AI_SEARCH_URL`, `AZURE_AI_SEARCH_INDEX_NAME` or matching constructor args. | Requires `azure-search-documents`. | Expected result fields include `metadata_storage_path`, `title`, and `chunk`. Current implementation retrieves one top document per query. |

## Retriever selection guidance

- Use `bing`, `you`, `brave`, `serper`, or `tavily` when you have stable paid/provider credentials.
- Use `duckduckgo` for low-stakes dry experiments only; it may be unreliable under load and can be rate-limited.
- Use `searxng` when you control a SearXNG endpoint and want provider independence.
- Use `azure_ai_search` when the organization already indexes web or document chunks in Azure AI Search. Verify the expected fields before running STORM.
- Do not use this sub-skill for `VectorRM` / Qdrant / CSV corpus grounding; route that to `vector-corpus`.

## Thread and rate-limit guidance

`max_thread_num` affects multiple concurrent operations:

- parallel persona conversations during research;
- retriever queries and page-fetching helpers;
- parallel article section generation.

Safe starting values:

| Situation | Suggested values |
| --- | --- |
| New keys or unknown quota | `max_thread_num=1`, `max_perspective=2`, `max_conv_turn=2`, `search_top_k=2` |
| Stable paid keys | `max_thread_num=2-4`, `max_perspective=3`, `max_conv_turn=3`, `search_top_k=3` |
| Frequent 429/rate-limit errors | Reduce `max_thread_num` first; then reduce perspectives, turns, and search queries. |
| Poor coverage / thin article | Increase `max_perspective`, `max_conv_turn`, or `search_top_k`, and inspect `raw_search_results.json`. |

Remember that article generation also scales with the number of first-level outline sections, because sections can be written in parallel.

## Optional package symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError: Duckduckgo requires pip install duckduckgo_search` | `DuckDuckGoSearchRM` optional dependency missing. | `pip install duckduckgo_search` in the active environment. |
| `ImportError: Tavily requires pip install tavily-python` | Tavily client missing. | `pip install tavily-python`. |
| `ImportError: AzureAISearch requires pip install azure-search-documents` | Azure Search client missing. | `pip install azure-search-documents`. |
| Search returns empty `raw_search_results.json` | Key invalid, endpoint unreachable, public search blocked, or topic too narrow. | Validate the key/endpoint with a one-query provider test, lower thread count, or switch retrievers. |

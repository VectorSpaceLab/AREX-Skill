# Provider contexts

A LaVague `Context` carries three model objects through the action-generation pipeline:

- `llm`: text LLM used by the ActionEngine/NavigationEngine to generate Python/Selenium actions.
- `mm_llm`: multimodal LLM used by the WorldModel to reason over page observations and screenshots.
- `embedding`: embedding model used by retrieval and Python-engine RAG steps.
- `extraction_llm`: optional extraction LLM; if omitted, the base `Context` uses `llm`.

Build engines from a context when the whole model stack should be consistent:

```python
from lavague.core import ActionEngine, WorldModel

action_engine = ActionEngine.from_context(context=context, driver=driver)
world_model = WorldModel.from_context(context)
```

Pass individual LlamaIndex objects only when intentionally mixing providers:

```python
from lavague.core import ActionEngine, WorldModel

world_model = WorldModel(mm_llm=my_multimodal_llm)
action_engine = ActionEngine(driver=driver, llm=my_text_llm, embedding=my_embedding)
```

## Context matrix

| Context | Import | Package | Required env vars | Installed constructor defaults and caveats |
| --- | --- | --- | --- | --- |
| `OpenaiContext` | `from lavague.contexts.openai import OpenaiContext` | `lavague-contexts-openai` | `OPENAI_API_KEY` | `llm="gpt-4o"`, `mm_llm="gpt-4o"`, `embedding="text-embedding-3-large"`. Some user docs mention `text-embedding-3-small`; the installed package signature uses `text-embedding-3-large`, so pass `embedding=` explicitly if cost or compatibility matters. |
| `AzureOpenaiContext` | `from lavague.contexts.openai import AzureOpenaiContext` | `lavague-contexts-openai` | `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`; optional `AZURE_API_VERSION` | Requires `embedding_deployment` as an argument. `embedding_endpoint` falls back to `endpoint`; `mm_llm_deployment` falls back to `deployment`; `mm_llm_endpoint` falls back to `endpoint`. The installed signature shows `llm="got-4o"` and `mm_llm="got-4o"`, so pass real model names explicitly. |
| `AnthropicContext` | `from lavague.contexts.anthropic import AnthropicContext` | `lavague-contexts-anthropic` | `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` | Uses Anthropic for `llm` and `mm_llm`; default embedding is OpenAI `text-embedding-3-small`, so non-OpenAI runs still need an OpenAI key unless you build a custom `Context` with a different embedding object. |
| `GeminiContext` | `from lavague.contexts.gemini import GeminiContext` | `lavague-contexts-gemini` | `GOOGLE_API_KEY` | Uses Gemini for `llm`, `mm_llm`, and `embedding`: `models/gemini-1.5-flash-latest`, `models/gemini-1.5-pro-latest`, `models/text-embedding-004`. |
| `FireworksContext` | `from lavague.contexts.fireworks import FireworksContext` | `lavague-contexts-fireworks` | `FIREWORKS_API_KEY` and `OPENAI_API_KEY` | Uses Fireworks for `llm` and `embedding`; default `mm_llm="gpt-4o"` is OpenAI because the Fireworks integration did not provide a LlamaIndex multimodal model. |
| `ContextCache` | `from lavague.contexts.cache import ContextCache` | `lavague-contexts-cache` | None for bare caches; fallback contexts may need their provider keys | Wraps cache LLM, multimodal LLM, and embedding stores. `ContextCache.default()` calls the default OpenAI context and therefore needs `OPENAI_API_KEY`; `ContextCache.from_context(context)` uses the provided context as fallback. |

## Credential handling

- Check that keys are present; do not print or serialize values.
- Prefer environment variables for local scripts and CI. Passing `api_key=` directly is supported by provider constructors but is easier to leak into code or logs.
- For non-OpenAI providers, read the whole stack: Anthropic still uses OpenAI embeddings by default, and Fireworks still uses an OpenAI multimodal LLM by default.
- For Azure, distinguish deployment names from model names. `deployment` and `embedding_deployment` are Azure deployment identifiers; `llm`, `mm_llm`, and `embedding` are model names.

## Provider snippets

OpenAI:

```python
from lavague.contexts.openai import OpenaiContext

context = OpenaiContext(
    llm="gpt-4o-mini",
    mm_llm="gpt-4o-mini",
    embedding="text-embedding-3-small",
)
```

Azure OpenAI:

```python
from lavague.contexts.openai import AzureOpenaiContext

context = AzureOpenaiContext(
    deployment="my-gpt4o-deployment",
    endpoint="<AZURE_OPENAI_ENDPOINT>",
    llm="gpt-4o",
    mm_llm="gpt-4o",
    embedding="text-embedding-3-small",
    embedding_deployment="my-embedding-deployment",
)
```

Anthropic with OpenAI embeddings:

```python
from lavague.contexts.anthropic import AnthropicContext

context = AnthropicContext(
    llm="claude-3-5-sonnet-20240620",
    mm_llm="claude-3-5-sonnet-20240620",
    embedding="text-embedding-3-small",
)
```

Gemini:

```python
from lavague.contexts.gemini import GeminiContext

context = GeminiContext(
    llm="models/gemini-1.5-flash-latest",
    mm_llm="models/gemini-1.5-pro-latest",
    embedding="models/text-embedding-004",
)
```

Fireworks with OpenAI multimodal fallback:

```python
from lavague.contexts.fireworks import FireworksContext

context = FireworksContext(
    llm="accounts/fireworks/models/llama-v3p1-70b-instruct",
    mm_llm="gpt-4o",
    embedding="nomic-ai/nomic-embed-text-v1.5",
)
```

Custom all-provider context:

```python
from lavague.core.context import Context

context = Context(
    llm=my_llama_index_llm,
    mm_llm=my_llama_index_multimodal_llm,
    embedding=my_llama_index_embedding,
)
```

## Cache context behavior

`ContextCache` is for controlled offline-ish replay or prompt capture, not a transparent provider accelerator.

- `LLMCache` stores prompt-to-text results in `llm_prompts.yml` by default.
- `MultiModalLLMCache` stores a key built from image hashes plus prompt text in `mm_llm_prompts.yml` by default.
- `EmbeddingCache` stores reduced vectors in `embeddings.yml` by default.
- If no fallback is configured and a prompt is missing, cache LLMs return placeholder text rather than calling a provider.
- If a fallback is configured and a prompt is missing, the fallback provider is called and the result is appended to the YAML store.
- Store files are normal working-directory files unless a custom store/path is supplied. Keep them out of runtime skill trees if they contain private prompts, page screenshots, or business data.

Example:

```python
from lavague.contexts.cache import ContextCache

# Pure cache objects; missing prompts return placeholders or mock embeddings.
context = ContextCache()

# Cache around an already-built provider context; missing prompts may call fallback providers.
context = ContextCache.from_context(provider_context)
```

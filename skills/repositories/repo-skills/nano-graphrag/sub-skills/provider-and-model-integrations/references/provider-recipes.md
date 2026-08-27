# Provider recipes for nano-graphrag

This reference gives self-contained provider patterns for nano-graphrag. The patterns are credential-free by default: put secrets in environment variables or a secret manager, never in source files or generated skills.

## GraphRAG provider control points

`GraphRAG` has three provider-facing callables:

```python
from nano_graphrag import GraphRAG

rag = GraphRAG(
    working_dir="./rag-workdir",
    best_model_func=my_best_llm,      # async prompt -> str, used for planning/report/query work
    cheap_model_func=my_cheap_llm,    # async prompt -> str, used for summaries/extraction support
    embedding_func=my_embedding,      # EmbeddingFunc-wrapped async texts -> np.ndarray
    best_model_max_token_size=32768,
    cheap_model_max_token_size=32768,
    best_model_max_async=16,
    cheap_model_max_async=16,
    embedding_batch_num=32,
    embedding_func_max_async=16,
)
```

A custom LLM function must accept this shape:

```python
async def my_llm_complete(prompt, system_prompt=None, history_messages=None, **kwargs) -> str:
    ...
```

Nano-graphrag wraps `best_model_func` and `cheap_model_func` with `hashing_kv=<cache or None>`, so custom functions must pop `hashing_kv` before calling a provider SDK. Remaining `kwargs` may include provider-facing options such as `max_tokens` and, for community-report JSON calls, `response_format={"type": "json_object"}`.

## Default OpenAI path

Default `GraphRAG()` uses these built-ins:

- `best_model_func`: `gpt_4o_complete`, calling OpenAI chat model `gpt-4o`.
- `cheap_model_func`: `gpt_4o_mini_complete`, calling OpenAI chat model `gpt-4o-mini`.
- `embedding_func`: `openai_embedding`, calling OpenAI embedding model `text-embedding-3-small` with `encoding_format="float"`.
- Default embedding wrapper attributes: `embedding_dim=1536`, `max_token_size=8192`.

The OpenAI client is created as `AsyncOpenAI()`, so the standard OpenAI SDK environment is expected, especially `OPENAI_API_KEY`. Use the default path only when the process environment has the right key and network access.

Minimal default setup:

```python
from nano_graphrag import GraphRAG

rag = GraphRAG(working_dir="./rag-workdir")
```

If a user wants a different OpenAI model or a different base URL, use a custom OpenAI-compatible function instead of mutating the module globals.

## Azure OpenAI built-in switch

Use Azure only when Azure OpenAI credentials and deployment names are configured for the running process:

```python
from nano_graphrag import GraphRAG

rag = GraphRAG(
    working_dir="./rag-workdir",
    using_azure_openai=True,
)
```

When `using_azure_openai=True`, nano-graphrag switches the default functions only if they have not already been replaced:

- `gpt_4o_complete` -> `azure_gpt_4o_complete`
- `gpt_4o_mini_complete` -> `azure_gpt_4o_mini_complete`
- `openai_embedding` -> `azure_openai_embedding`

The built-in Azure client is `AsyncAzureOpenAI()`. Set the standard Azure OpenAI SDK environment variables before constructing `GraphRAG`:

```bash
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export OPENAI_API_VERSION="2024-xx-xx"
```

The repository's Azure example also lists embedding-specific placeholders named `API_KEY_EMB`, `AZURE_ENDPOINT_EMB`, and `API_VERSION_EMB`. The current built-in `AsyncAzureOpenAI()` path is driven by the standard SDK names above; use a custom embedding function if embeddings require different credentials, endpoints, API versions, or deployment names.

Important Azure deployment-name pitfall: the built-ins pass `model="gpt-4o"`, `model="gpt-4o-mini"`, and `model="text-embedding-3-small"`. In Azure, the `model` argument is the deployment name. If the user's deployments are named differently, implement custom wrappers that pass the actual deployment names.

## Amazon Bedrock built-in switch

Use Bedrock only when AWS credentials, IAM permissions, region access, and model access are ready:

```python
from nano_graphrag import GraphRAG

rag = GraphRAG(
    working_dir="./rag-workdir",
    using_amazon_bedrock=True,
    best_model_id="us.anthropic.claude-3-sonnet-20240229-v1:0",
    cheap_model_id="us.anthropic.claude-3-haiku-20240307-v1:0",
)
```

When `using_amazon_bedrock=True`, nano-graphrag replaces both LLM callables with `create_amazon_bedrock_complete_function(model_id)` and replaces embeddings with the built-in Titan embedding function. Bedrock details:

- Chat uses an `aioboto3.Session()` client for `bedrock-runtime`.
- Region comes from `AWS_REGION`; if unset, nano-graphrag uses `us-east-1`.
- Chat calls Bedrock `converse` with message content shaped as `[{"text": prompt}]`.
- `max_tokens` is converted to Bedrock `inferenceConfig.maxTokens`; default is `4096`.
- Built-in embeddings call model `amazon.titan-embed-text-v2:0` with `dimensions=1024`.
- Built-in Bedrock embedding wrapper attributes are `embedding_dim=1024`, `max_token_size=8192`.

Bedrock failures are usually not nano-graphrag API errors: check AWS credential chain, selected region, enabled model access, IAM permissions for `bedrock:Converse` and `bedrock:InvokeModel`, and whether the `best_model_id`/`cheap_model_id` are valid in the target account and region.

## OpenAI-compatible hosted providers

Use this pattern for DeepSeek-style or custom OpenAI-compatible chat APIs. Do not hard-code keys.

```python
import os
from openai import AsyncOpenAI
from nano_graphrag.base import BaseKVStorage
from nano_graphrag._utils import compute_args_hash

MODEL = os.environ.get("NANO_GRAPHRAG_LLM_MODEL", "your-chat-model")
BASE_URL = os.environ["NANO_GRAPHRAG_LLM_BASE_URL"]
API_KEY = os.environ["NANO_GRAPHRAG_LLM_API_KEY"]

async def openai_compatible_model_if_cache(
    prompt, system_prompt=None, history_messages=None, **kwargs
) -> str:
    if history_messages is None:
        history_messages = []

    # Required: GraphRAG passes this kwarg even when cache is disabled.
    hashing_kv: BaseKVStorage | None = kwargs.pop("hashing_kv", None)

    # Optional: strip only for providers that reject these OpenAI-specific args.
    for name in os.environ.get("NANO_GRAPHRAG_STRIP_KWARGS", "").split(","):
        if name.strip():
            kwargs.pop(name.strip(), None)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})

    if hashing_kv is not None:
        args_hash = compute_args_hash(MODEL, messages)
        cached = await hashing_kv.get_by_id(args_hash)
        if cached is not None:
            return cached["return"]

    client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
    response = await client.chat.completions.create(
        model=MODEL,
        messages=messages,
        **kwargs,
    )
    result = response.choices[0].message.content

    if hashing_kv is not None:
        await hashing_kv.upsert({args_hash: {"return": result, "model": MODEL}})
        await hashing_kv.index_done_callback()
    return result
```

Attach it to both model roles if the provider has only one chat model:

```python
rag = GraphRAG(
    working_dir="./rag-workdir",
    best_model_func=openai_compatible_model_if_cache,
    cheap_model_func=openai_compatible_model_if_cache,
)
```

For DeepSeek-style APIs, the base URL pattern is `https://api.deepseek.com` and the model name is commonly `deepseek-chat`; still read the provider's current API documentation and put the real key in the environment.

## Providers that reject `response_format` or `max_tokens`

Nano-graphrag may call the LLM with these kwargs:

- `max_tokens`: used for summaries and some bounded generations.
- `response_format={"type": "json_object"}`: used for JSON community reports and global community map work.

Some providers and local services reject one or both. Strip only the unsupported values in the adapter, not at `GraphRAG` construction time:

```python
kwargs.pop("response_format", None)  # if the provider rejects JSON mode
kwargs.pop("max_tokens", None)       # if the provider uses a different limit field
```

If `response_format` is stripped or ignored, provider output may be malformed JSON. Keep `convert_response_to_json_func` at the default for simple repair, or route to the customization/troubleshooting sub-skill for stronger JSON repair and prompt changes.

## Ollama/local chat service pattern

Ollama requires a running local service and installed model. This recipe intentionally strips unsupported kwargs and lets the user control context size via Ollama options.

```python
import os
import ollama
from nano_graphrag.base import BaseKVStorage
from nano_graphrag._utils import compute_args_hash

MODEL = os.environ.get("OLLAMA_MODEL", "qwen2:ctx32k")

async def ollama_model_if_cache(
    prompt, system_prompt=None, history_messages=None, **kwargs
) -> str:
    if history_messages is None:
        history_messages = []

    kwargs.pop("max_tokens", None)
    kwargs.pop("response_format", None)
    hashing_kv: BaseKVStorage | None = kwargs.pop("hashing_kv", None)

    options = kwargs.pop("options", {}) or {}
    options.setdefault("num_ctx", int(os.environ.get("OLLAMA_NUM_CTX", "8192")))

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})

    if hashing_kv is not None:
        args_hash = compute_args_hash(MODEL, messages)
        cached = await hashing_kv.get_by_id(args_hash)
        if cached is not None:
            return cached["return"]

    client_kwargs = {}
    if os.environ.get("OLLAMA_HOST"):
        client_kwargs["host"] = os.environ["OLLAMA_HOST"]
    client = ollama.AsyncClient(**client_kwargs)
    response = await client.chat(
        model=MODEL,
        messages=messages,
        options=options,
        **kwargs,
    )
    result = response["message"]["content"]

    if hashing_kv is not None:
        await hashing_kv.upsert({args_hash: {"return": result, "model": MODEL}})
        await hashing_kv.index_done_callback()
    return result
```

Local LLMs often need a larger context window than their default. A too-small Ollama `num_ctx` can produce zero extracted entities/relations or empty graphs. Prefer a model variant configured with a larger `num_ctx` such as `qwen2:ctx32k`, or pass `options={"num_ctx": 32000}` when calling Ollama.

## Local sentence-transformer embeddings

Use local embeddings when the user has no embedding API key or wants embeddings to remain on the host. Model downloads and hardware requirements are outside the safe default path.

```python
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from nano_graphrag._utils import wrap_embedding_func_with_attrs

EMBED_MODEL_NAME = os.environ.get(
    "NANO_GRAPHRAG_EMBED_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBED_DEVICE = os.environ.get("NANO_GRAPHRAG_EMBED_DEVICE", "cpu")
EMBED_MODEL = SentenceTransformer(EMBED_MODEL_NAME, device=EMBED_DEVICE)

@wrap_embedding_func_with_attrs(
    embedding_dim=EMBED_MODEL.get_sentence_embedding_dimension(),
    max_token_size=EMBED_MODEL.max_seq_length,
)
async def local_embedding(texts: list[str]) -> np.ndarray:
    vectors = EMBED_MODEL.encode(texts, normalize_embeddings=True)
    return np.asarray(vectors, dtype=np.float32)
```

Attach it without changing the LLM provider:

```python
rag = GraphRAG(
    working_dir="./rag-workdir",
    embedding_func=local_embedding,
    embedding_batch_num=16,
    embedding_func_max_async=2,
)
```

## Hosted LLM plus local embedding

Combine the two adapter types when chat generation is hosted but embeddings should be local:

```python
rag = GraphRAG(
    working_dir="./rag-workdir",
    best_model_func=openai_compatible_model_if_cache,
    cheap_model_func=openai_compatible_model_if_cache,
    embedding_func=local_embedding,
    best_model_max_async=4,
    cheap_model_max_async=4,
    embedding_batch_num=16,
    embedding_func_max_async=2,
)
```

Do not reuse an existing `working_dir` if the embedding dimension changed. The vector index dimension is fixed when the vector store is created.

## Tuning concurrency and token sizes

- `best_model_max_async` and `cheap_model_max_async` limit concurrent calls through nano-graphrag's async-call limiter. Lower these for rate-limited hosted APIs and local services.
- `embedding_func_max_async` limits concurrent embedding calls. Lower it for CPU-bound local models, GPU memory pressure, or local service overload.
- `embedding_batch_num` controls how many texts vector stores send to `embedding_func` per batch.
- `best_model_max_token_size` and `cheap_model_max_token_size` tell nano-graphrag how much context it may pack into prompts. Set them no higher than the provider/model's real context window.
- Provider response-token controls still depend on the adapter. OpenAI-style providers use `max_tokens`; Bedrock maps to `maxTokens`; Ollama commonly uses model/options settings rather than `max_tokens`.

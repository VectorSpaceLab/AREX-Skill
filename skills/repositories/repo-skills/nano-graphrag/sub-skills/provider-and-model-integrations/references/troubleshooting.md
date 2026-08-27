# Provider and model troubleshooting

Use this reference when nano-graphrag provider configuration fails before, during, or after `GraphRAG.insert()` / `GraphRAG.query()`.

## Missing or wrong credentials

### Default OpenAI

Symptoms:

- OpenAI authentication errors.
- Provider SDK reports no API key.
- Default `GraphRAG()` fails before any custom function is used.

Checks:

1. Confirm the process has `OPENAI_API_KEY` set before constructing `GraphRAG`.
2. Confirm the environment can reach the OpenAI API.
3. Confirm the account has access to `gpt-4o`, `gpt-4o-mini`, and `text-embedding-3-small` or replace the built-ins with custom functions.

### Azure OpenAI

Symptoms:

- Azure client authentication or endpoint errors.
- 404 / deployment not found despite valid Azure credentials.
- Embedding calls fail while chat calls work, or vice versa.

Checks:

1. Set `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, and `OPENAI_API_VERSION` for the Azure OpenAI SDK.
2. Remember that nano-graphrag's built-ins pass Azure `model=` values as deployment names: `gpt-4o`, `gpt-4o-mini`, and `text-embedding-3-small`.
3. If the user's deployments have different names, implement custom Azure wrappers instead of relying on `using_azure_openai=True`.
4. If embeddings use a different Azure resource or API version than chat, use a custom `embedding_func`.

### Amazon Bedrock

Symptoms:

- `NoCredentialsError`, `AccessDenied`, model unavailable, or region errors.
- Chat works but Titan embeddings fail.
- Bedrock model IDs work in another region but not here.

Checks:

1. Confirm normal AWS credential chain works for the process (`AWS_PROFILE`, environment variables, instance role, or `aws configure`).
2. Set `AWS_REGION`; nano-graphrag defaults to `us-east-1` if unset.
3. Confirm Bedrock model access is enabled for both chat model IDs and `amazon.titan-embed-text-v2:0`.
4. Confirm IAM permissions include Bedrock runtime calls such as `bedrock:Converse` and `bedrock:InvokeModel`.
5. Confirm the model ID form is valid for the account and region, especially inference-profile IDs with prefixes such as `us.`.

## Unsupported provider kwargs

Symptoms:

- Provider says `response_format` is unknown or unsupported.
- Provider says `max_tokens` is unknown, wrong type, or ignored.
- Ollama adapter fails because OpenAI-style kwargs are forwarded.
- Custom LLM function forwards `hashing_kv` and provider SDK rejects it.

Fix the adapter, not the nano-graphrag caller:

```python
hashing_kv = kwargs.pop("hashing_kv", None)  # always remove before provider call
kwargs.pop("response_format", None)          # only if provider rejects JSON mode
kwargs.pop("max_tokens", None)               # only if provider rejects this field
```

For providers with a different response-token field, map the value rather than dropping it:

```python
max_tokens = kwargs.pop("max_tokens", None)
if max_tokens is not None:
    kwargs.setdefault("options", {})["num_predict"] = max_tokens  # example local-service style
```

Keep `response_format` when the provider supports JSON mode; it improves community-report JSON reliability.

## Cache-aware function errors

Symptoms:

- Cache is never used even with `enable_llm_cache=True`.
- Cache file stays empty after LLM calls.
- Provider receives an unexpected `hashing_kv` keyword.

Checklist for custom LLM functions:

1. Accept `**kwargs`.
2. Pop `hashing_kv` before building the provider request.
3. Build the exact `messages` list before computing the cache key.
4. Compute the key with `compute_args_hash(model_name, messages)` or equivalent stable model identity.
5. On cache hit, return `cached["return"]`.
6. On cache miss, store `{args_hash: {"return": result, "model": model_name}}`.
7. Call `await hashing_kv.index_done_callback()` after upsert when immediate persistence matters.

If a user disables LLM cache with `GraphRAG(enable_llm_cache=False)`, nano-graphrag still passes `hashing_kv=None`; adapters should handle that.

## Malformed JSON from provider output

Symptoms:

- Community reports fail to parse.
- Global query over communities fails or returns poor output.
- Logs show JSON decoding failures.
- Entity extraction or community report generation works with OpenAI but not with a local/OpenAI-compatible provider.

Causes:

- Provider rejected or ignored `response_format={"type": "json_object"}`.
- Local/open-source model did not follow required JSON or entity tuple format.
- Adapter stripped `response_format` without adding any repair or prompt constraints.
- Context was truncated by the provider before the JSON instructions.

Actions:

1. If the provider supports JSON mode, preserve `response_format`.
2. If the provider rejects JSON mode, strip `response_format` but add a stronger system prompt or use a custom `convert_response_to_json_func`.
3. Reduce packed context or set model token-size fields to the provider's real context.
4. Route prompt/JSON repair work to `../customization-and-troubleshooting/references/prompts-and-json.md` and empty-graph analysis to `../customization-and-troubleshooting/references/troubleshooting.md`.

## Ollama context too small / zero entities

Symptoms:

- Logs similar to `Processed ... 0 entities ... 0 relations`.
- `Leiden.EmptyNetworkError` because no graph was extracted.
- Local model returns incomplete extraction tuples or malformed JSON.

Common root cause: Ollama's default context can be too small for nano-graphrag entity extraction prompts. Increase the model context and use a sufficiently capable model.

Options:

- Create a model variant with a larger `num_ctx`, for example a `:ctx32k` variant.
- Pass Ollama `options={"num_ctx": 32000}` in the adapter when supported.
- Lower nano-graphrag chunk size or reduce extraction prompt burden if the model cannot handle large prompts.
- Use a larger/more instruction-following local model.

If the graph is already empty, do not focus first on vector storage. Fix provider output format/context, then rerun insertion into a clean or rebuilt `working_dir`.

## Model max token and concurrency tuning

Symptoms:

- Rate limits, 429s, service overloaded, local model timeouts, GPU/CPU memory spikes.
- Prompt too long errors.
- Poor extraction after context truncation.

Tuning fields:

- `best_model_max_async`: concurrent calls to `best_model_func`; lower for hosted API rate limits or local services.
- `cheap_model_max_async`: concurrent calls to `cheap_model_func`; lower similarly.
- `embedding_func_max_async`: concurrent embedding calls; lower for local models or API rate limits.
- `embedding_batch_num`: texts per embedding batch; reduce if embeddings time out or run out of memory.
- `best_model_max_token_size`: prompt packing limit for best-model tasks; set no higher than real context.
- `cheap_model_max_token_size`: prompt packing limit for cheap-model tasks; set no higher than real context.

The max-token-size fields guide nano-graphrag context packing. They do not magically expand provider context windows.

## Embedding shape or dimension failures

Symptoms:

- Vector store construction fails with dimension errors.
- Query path fails around `embedding[0]`.
- Upsert path fails during `np.concatenate`.
- Retrieval returns nonsense after changing embedding models.

Checks:

1. `embedding_func.embedding_dim` equals the real vector length.
2. `await embedding_func(["one", "two"])` returns a 2D `np.ndarray` with shape `(2, embedding_dim)`.
3. `await embedding_func(["query"])` returns shape `(1, embedding_dim)`.
4. The function returns finite numeric values.
5. A `working_dir` created with a different embedding dimension is rebuilt or replaced.

Read `embedding-functions.md` for the full contract.

## OpenAI-compatible provider checklist

When adapting a provider behind an OpenAI-compatible API:

- Instantiate `AsyncOpenAI(api_key=..., base_url=...)` for async chat completions.
- Use environment variables for key, base URL, and model name.
- Preserve the OpenAI message shape: optional system message, prior `history_messages`, final user prompt.
- Pop `hashing_kv` before SDK calls.
- Strip only unsupported kwargs.
- Cache by model identity plus messages.
- Return `response.choices[0].message.content` as a string.
- If the provider's SDK is only synchronous, isolate blocking calls carefully; do not block high-concurrency workflows without reducing `best_model_max_async` / `cheap_model_max_async`.

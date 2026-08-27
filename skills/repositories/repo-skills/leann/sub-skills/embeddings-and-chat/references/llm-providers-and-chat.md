# LLM Providers And Chat

## Core Signatures

```python
LeannChat(index_path, llm_config=None, enable_warmup=False, searcher=None, **kwargs)
LeannChat.ask(
    question,
    top_k=5,
    complexity=64,
    beam_width=1,
    prune_ratio=0.0,
    recompute_embeddings=True,
    pruning_strategy="global",
    llm_kwargs=None,
    expected_zmq_port=5557,
    metadata_filters=None,
    batch_size=0,
    use_grep=False,
    vector_weight=1.0,
    **search_kwargs,
)
LeannChat.start_interactive()
LeannChat.cleanup()
```

When `searcher` is omitted, `LeannChat` constructs and owns a `LeannSearcher`; `**kwargs` go to that constructor. When a searcher is supplied, chat reuses it and cleanup does not stop its resources. Prefer an explicit `cleanup()` or context manager for owned resources.

`llm_config=None` currently selects OpenAI with model `gpt-4o` and `OPENAI_API_KEY`; it is not simulation mode. Pass an explicit provider configuration rather than relying on that default.

## Provider Configuration

The stable provider set covered by this sub-skill is:

| `llm_config.type` | Fields | Environment/default precedence | Package and external dependency |
|---|---|---|---|
| `openai` | `model`, optional config field `api_key`, optional `base_url` | Key: explicit then `OPENAI_API_KEY`; a nonempty resolved key is required. URL: explicit, `LEANN_OPENAI_BASE_URL`, `OPENAI_BASE_URL`, `LOCAL_OPENAI_BASE_URL`, then `https://api.openai.com/v1`. | `openai`; network service. A custom URL makes this the OpenAI-compatible provider for LM Studio, vLLM, SGLang, and similar APIs. Even a keyless local service needs a nonempty placeholder value because LEANN validates the key before creating the client. |
| `ollama` | `model`, optional `host` | Host: explicit, `LEANN_LOCAL_LLM_HOST`, `LEANN_OLLAMA_HOST`, `OLLAMA_HOST`, `LOCAL_LLM_ENDPOINT`, then `http://localhost:11434`. | `requests`; a reachable Ollama-compatible server with the named model already installed. Initialization performs availability checks and may query Ollama's public model library when an installed-model name is invalid. |
| `hf` | `model`, optional `trust_remote_code` (default `false`) | Device: `LEANN_LLM_DEVICE`, otherwise CUDA, then MPS, then CPU. | `transformers`, `torch`, and Hugging Face Hub access during the current model-existence check and first load. Model files can be large. |
| `anthropic` | `model`, optional config field `api_key`, optional `base_url` | Key: explicit then `ANTHROPIC_API_KEY`; a nonempty resolved key is required. URL: explicit, `LEANN_ANTHROPIC_BASE_URL`, `ANTHROPIC_BASE_URL`, `LOCAL_ANTHROPIC_BASE_URL`, then `https://api.anthropic.com`. | `anthropic`; network service. Custom Anthropic-compatible endpoints are supported through `base_url`. |

Examples:

```python
from leann import LeannChat

chat = LeannChat(
    "indexes/notes",
    llm_config={
        "type": "openai",
        "model": "gpt-4o-mini",
        # Set OPENAI_API_KEY in the process environment.
    },
)
answer = chat.ask(
    "Summarize the indexing trade-offs.",
    top_k=8,
    llm_kwargs={"temperature": 0.2, "max_tokens": 800},
)
chat.cleanup()
```

```python
chat = LeannChat(
    "indexes/notes",
    llm_config={
        "type": "ollama",
        "model": "qwen3:8b",
        "host": "http://localhost:11434",
    },
)
```

The current `get_llm` factory also contains `gemini`, `minimax`, `novita`, `atlascloud` aliases, and `simulated`. They are outside this sub-skill's provider-validator scope; do not silently map one of them to `openai` because their key resolution and defaults differ.

## Retrieval Prompt And Argument Routing

`LeannChat.ask` performs one retrieval, joins result texts with blank lines, then sends this fixed structure to the LLM:

1. an introduction saying retrieved context may help;
2. the concatenated result text;
3. the original question;
4. a request for the best answer from context and model knowledge.

There is no `prompt_template` argument for replacing this final LLM prompt. Embedding build/query templates affect only text sent to the embedding model. For a custom answer prompt, call `LeannSearcher.search(...)`, format the returned context yourself, and call an `LLMInterface` returned by `get_llm(...)`.

Keep the two keyword channels separate:

- `llm_kwargs` goes to the provider's `ask` method: generation controls such as `temperature`, `max_tokens`, `top_p`, or `thinking_budget`.
- retrieval parameters and `**search_kwargs` go to `LeannSearcher.search` and the selected vector backend.

OpenAI reasoning models whose names contain `o1`, `o3`, or `o4` receive `max_completion_tokens` instead of `max_tokens`, force temperature to 1.0, and can receive `reasoning_effort`. Anthropic accepts `max_tokens`, optional `temperature`, and optional `top_p`. Hugging Face maps `max_tokens`/`max_new_tokens`, temperature, and top-p to local generation. Ollama places ordinary `llm_kwargs` in its `options` object.

Provider implementations catch many request-time service errors and return strings beginning with `Error:` rather than raising. Treat that prefix as a failed answer in automation.

## Thinking Budget

Pass one of `low`, `medium`, or `high` through `llm_kwargs`:

```python
answer = chat.ask(
    "Compare the alternatives and justify a recommendation.",
    llm_kwargs={"thinking_budget": "high"},
)
```

- OpenAI applies it as `reasoning_effort` only to recognized o-series names.
- Ollama applies a `reasoning` option only to recognized reasoning-model names, including `gpt-oss:20b`, `gpt-oss:120b`, `deepseek-r1`, and `deepseek-coder` patterns.
- Unsupported models log a warning and continue without the reasoning parameter.
- Anthropic and Hugging Face do not implement this LEANN-specific mapping in the current chat classes.

A larger budget can increase latency and hosted-provider cost. It does not change retrieval depth.

## Interactive Behavior

Two interactive paths differ:

- `LeannChat.start_interactive()` repeatedly calls `self.ask(user_input)` with the API defaults. It does not retain arbitrary per-query `top_k` or `llm_kwargs` configuration.
- `leann ask ... --interactive` captures the CLI's retrieval settings, metadata filters, and thinking budget in a callback and reuses them for every turn. If a positional query is supplied, it runs once before entering the loop. Without `--interactive`, an omitted query triggers a one-line prompt; blank input exits.

Neither path stores conversational message history in `LeannChat`; each question is an independent retrieval-and-answer operation. ReAct retains tool observations only for one `run` call, not across separate runs.

## Offline, Privacy, And Credentials

| Provider | Fully offline after preparation? | Data boundary |
|---|---|---|
| OpenAI-compatible | Only if the configured endpoint is local and already running. | Prompt and retrieved context are sent to that endpoint. |
| Ollama | Yes after server and model are locally installed, except model-validation logic may try public Ollama pages for an invalid installed name. | Prompt and context go to the configured Ollama host. |
| Hugging Face | Model generation can be local, but current initialization checks Hub model existence and first load may download. | Prompt remains local after successful local setup. `trust_remote_code=true` executes repository code. |
| Anthropic | No for the default service. | Prompt and retrieved context are sent to the configured endpoint. |

Never store production keys in indexable documents, shell history, examples, or committed JSON. Validate field names and environment availability without revealing values:

```bash
python scripts/validate_provider_config.py llm-config.json --kind llm --require-credentials
```

See [troubleshooting](troubleshooting.md) for provider-specific failures.

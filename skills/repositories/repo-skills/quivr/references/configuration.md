# Configuration

This reference summarizes the live configuration surface that matters most for Quivr.
Where docs or older examples use different wording, trust the source code and the bundled scripts.

## LLM configuration

### `LLMEndpointConfig`

Live fields:

- `supplier`: defaults to `OPENAI`
- `model`: defaults to `gpt-4o`
- `tokenizer_hub`: derived from the chosen model when possible
- `llm_base_url`: optional provider base URL
- `env_variable_name`: defaults to the provider-specific API key name
- `llm_api_key`: read from the matching environment variable when present
- `max_context_tokens`: default live value is `20000`
- `max_output_tokens`: default live value is `4096`
- `temperature`: default live value is `0.3`
- `streaming`: defaults to `True`
- `prompt`: optional custom prompt template

Important behavior:

- `set_llm_model_config()` may lower token limits to fit the model family.
- `set_api_key()` fills `llm_api_key` from the provider-specific environment variable when available.
- `LLMEndpointConfig()` warnings are normal when the provider key is absent; the object can still exist for fake or local testing.

## Provider keys

The code expects the provider-specific key name derived from the supplier name, for example:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `AZURE_API_KEY`
- `MISTRAL_API_KEY`
- `GEMINI_API_KEY`
- `GROQ_API_KEY`

Use the exact provider name that matches the selected supplier. If you are using a fake model for smoke tests, you can still set a placeholder key to avoid warnings.

## Reranker configuration

### `RerankerConfig`

- `supplier`: optional reranker family such as `cohere` or `jina`
- `model`: if omitted, defaults to the supplier default model
- `top_n`: default `5`
- `api_key`: filled from `COHERE_API_KEY` or `JINA_API_KEY` when a supplier is selected
- `relevance_score_threshold`: optional threshold used by the web-search workflow
- `relevance_score_key`: defaults to `relevance_score`

If you select a reranker supplier, the matching key must exist before construction succeeds.

## Retrieval configuration

### `RetrievalConfig`

- `reranker_config`: default reranker settings
- `llm_config`: default `LLMEndpointConfig()`
- `max_history`: default `10`
- `max_files`: default `20`
- `k`: default `40`
- `prompt`: optional custom instruction string
- `workflow_config`: default RAG graph with `START -> filter_history -> rewrite -> retrieve -> generate_rag -> END`

### `WorkflowConfig`

- Validates that the first node is `START`.
- Validates any declared tools against the known tool categories and tool lists.
- Supports the web-search route when `available_tools` includes `web search`.
- Supports node-level tools such as `cited_answer` on the answer node.

## Parser and splitter configuration

### `SplitterConfig`

- `chunk_size`: default `400`
- `chunk_overlap`: default `100`

### `MegaparseConfig`

- `method`: default `unstructured`
- `strategy`: default `fast`
- `check_table`: default `False`
- `parsing_instruction`: optional
- `model_name`: default `gpt-4o`

## Storage-related configuration

- `QUIVR_LOCAL_STORAGE` controls the default `LocalStorage` directory.
- `TIKA_SERVER_URL` controls the default Tika endpoint.
- `TAVILY_API_KEY` is required when the web-search tool is active.
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` activate Langfuse tracing if you want runtime traces.

## Compatibility note

Some older repository examples still use legacy wording such as `max_input_tokens`. When you write new guidance, use the live field names from the source code: `max_context_tokens` and `max_output_tokens`.

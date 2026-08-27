# Provider Package Patterns

## Package Layout

LangChain partner packages live under `libs/partners/<provider>`. Each package is independently versioned and usually contains:

- `pyproject.toml` with the distribution name, Python range, runtime provider SDK dependency, dependency groups, local editable sources, and package metadata.
- `uv.lock` for package-local dependency resolution.
- `langchain_<provider>/` source root with public exports in `__init__.py` and package-specific `_version.py`.
- `tests/unit_tests/` for deterministic tests that should not require network access.
- `tests/integration_tests/` for live-provider, local-service, VCR, or standard conformance checks.
- `scripts/check_imports.py`, `scripts/check_version.py`, and commonly `scripts/lint_imports.sh`.
- A package Makefile with package-local targets such as `test`, `integration_test`, `lint_package`, `lint_tests`, `type`, `check_imports`, and `check_version`.

Always work from the owning package directory for commands. The monorepo has package-local `pyproject.toml` and `uv.lock` files under `libs/*`; do not assume there is a root `pyproject.toml`.

## Representative Public Surfaces

Use public exports and adjacent unit tests to identify ownership before editing:

| Provider | Distribution | Import package | Main public surfaces |
| --- | --- | --- | --- |
| OpenAI | `langchain-openai` | `langchain_openai` | `ChatOpenAI`, `AzureChatOpenAI`, `OpenAI`, `AzureOpenAI`, `OpenAIEmbeddings`, `AzureOpenAIEmbeddings`, `custom_tool`, OpenAI middleware and output parsers |
| Anthropic | `langchain-anthropic` | `langchain_anthropic` | `ChatAnthropic`, `AnthropicLLM`, `convert_to_anthropic_tool`, Anthropic middleware and output parsers |
| Ollama | `langchain-ollama` | `langchain_ollama` | `ChatOllama`, `OllamaLLM`, `OllamaEmbeddings` |
| Qdrant | `langchain-qdrant` | `langchain_qdrant` | `QdrantVectorStore`, `Qdrant`, `RetrievalMode`, `SparseEmbeddings`, `SparseVector`, `FastEmbedSparse` |
| Chroma | `langchain-chroma` | `langchain_chroma` | `Chroma` vector store |
| DeepSeek | `langchain-deepseek` | `langchain_deepseek` | `ChatDeepSeek` built on OpenAI-compatible behavior |
| Fireworks | `langchain-fireworks` | `langchain_fireworks` | `ChatFireworks`, `Fireworks`, `FireworksEmbeddings` |
| Groq | `langchain-groq` | `langchain_groq` | `ChatGroq` |
| Hugging Face | `langchain-huggingface` | `langchain_huggingface` | `ChatHuggingFace`, `HuggingFaceEmbeddings`, `HuggingFaceEndpointEmbeddings`, `HuggingFaceEndpoint`, `HuggingFacePipeline` |
| MistralAI | `langchain-mistralai` | `langchain_mistralai` | `ChatMistralAI`, `MistralAIEmbeddings` |
| Nomic | `langchain-nomic` | `langchain_nomic` | `NomicEmbeddings` |
| Perplexity | `langchain-perplexity` | `langchain_perplexity` | `ChatPerplexity`, `PerplexityEmbeddings`, `PerplexitySearchRetriever`, `PerplexitySearchResults`, reasoning output parsers and typed web-search options |
| OpenRouter | `langchain-openrouter` | `langchain_openrouter` | `ChatOpenRouter` |
| xAI | `langchain-xai` | `langchain_xai` | `ChatXAI` built on OpenAI-compatible behavior |
| Exa | `langchain-exa` | `langchain_exa` | `ExaSearchRetriever`, `ExaSearchResults`, `ExaFindSimilarResults`, Exa content option exports |

For providers that subclass or wrap another provider style, preserve the adapter boundary. DeepSeek and xAI depend on `langchain-openai` patterns; do not duplicate OpenAI internals unless the provider package already owns an override.

## Dependency Patterns

Provider packages depend on `langchain-core` and their provider SDK or service client. Examples include `openai`, `anthropic`, `ollama`, `qdrant-client`, `chromadb`, `groq`, `huggingface-hub`, `tokenizers`, `httpx`, `nomic`, `perplexityai`, `openrouter`, `exa-py`, and OpenAI-compatible packages.

When dependency work is needed:

1. Read `pyproject.toml` first. Check `[project]`, dependency groups, `[tool.uv.sources]`, lint/type config, and pytest markers.
2. Keep runtime dependencies minimal and provider-specific.
3. Use optional groups only when the package already uses them or the feature truly needs them.
4. Update `uv.lock` through package-local `uv` when available. If `uv` is unavailable, do not claim the lock was refreshed.
5. Do not add dependencies to shared packages just to satisfy a partner package test.

## Edit Workflow for Provider Classes

1. Identify the affected public class and source file. Common locations are `chat_models.py`, `chat_models/base.py`, `llms.py`, `embeddings.py`, `vectorstores.py`, `retrievers.py`, `tools.py`, middleware modules, or output parser modules.
2. Check the public export in `langchain_<provider>/__init__.py` and any subpackage `__init__.py` before changing imports or names.
3. Search unit tests for constructor parameters, serialization fields, secrets handling, tool calls, streaming chunks, async variants, token usage, response metadata, and standard-test fixtures.
4. Preserve constructor and method signatures. If a new public option is needed, prefer a keyword-only parameter with a default and add tests for old and new call patterns.
5. Add or update no-network unit tests first. Use fakes, mocked clients, snapshot fixtures, or response objects rather than live provider calls.
6. Add integration coverage only when behavior cannot be verified locally. Gate it behind environment variables, pytest markers, service availability, or cassettes.

## Provider Response and Tool-Call Shapes

Chat integrations translate provider-native payloads into `AIMessage`, `AIMessageChunk`, `ToolCall`, `InvalidToolCall`, response metadata, usage metadata, and stream chunks. Many packages have helper functions named like `_lc_tool_call_to_*`, `convert_to_*_tool`, or provider-specific chunk parsers.

When changing response handling:

- Verify normal and streaming paths separately.
- Include tool call id, function name, arguments, invalid tool-call parsing, and provider-specific finish reason coverage.
- Assert both LangChain-normalized fields and provider-specific `response_metadata` where tests already expose them.
- Keep provider SDK raw response shape assumptions localized to the partner package.
- Do not weaken validation just to pass one provider response; capture the precise shape mismatch in tests.

## Vector Store and Retriever Packages

Qdrant and Chroma are vector-store integrations. Exa and Perplexity include retriever/tool surfaces. Vector store work often needs service-aware behavior:

- Unit tests should use fake embeddings, in-memory clients, temporary collections, or mocked service clients when possible.
- Integration tests may require a local service, Docker-backed database, hosted endpoint, or API key. Skip when unavailable unless the user explicitly asks to provision or run it.
- Check embedding dimensions, distance strategy, collection/index creation, metadata filtering, MMR behavior, deletion/upsert behavior, and async/sync variants.
- Preserve migration compatibility for legacy classes such as `Qdrant` while favoring current classes such as `QdrantVectorStore` when the package distinguishes them.

## Validation Signals

Good provider changes usually have:

- Updated unit tests under `tests/unit_tests/` that fail before the fix.
- Passing targeted package-local test commands when `uv` is available.
- Passing import checks for touched modules through `scripts/check_imports.py` or `make check_imports`.
- Passing version consistency through `scripts/check_version.py` or `make check_version` when metadata/version files changed.
- No live network calls during default unit tests unless a package intentionally has an exception documented in its Makefile.

## Common Commands

Run from `libs/partners/<provider>`:

```bash
uv run --group test pytest tests/unit_tests/test_imports.py
uv run --group test pytest tests/unit_tests/test_chat_models.py
uv run --group test pytest tests/unit_tests/test_embeddings.py
uv run --group test pytest tests/unit_tests/test_vectorstores.py
uv run --group lint python scripts/check_imports.py $(find langchain_* -name '*.py')
uv run python scripts/check_version.py
make test TEST_FILE=tests/unit_tests/test_chat_models.py
make lint_package
make type
```

Choose only commands that match existing files and Makefile targets. If `uv` is unavailable, record the skip and still run static checks that do not require package dependency installation, such as syntax compilation for bundled skill scripts.

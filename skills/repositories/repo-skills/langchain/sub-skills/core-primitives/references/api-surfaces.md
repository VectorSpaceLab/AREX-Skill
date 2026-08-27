# Core Primitive API Surfaces

This reference distills the `langchain-core` surfaces a future agent should rely on when changing stable primitives. It is intentionally self-contained and does not require reading the source checkout at runtime.

## Package Facts

- Distribution: `langchain-core`.
- Sampled version: `1.4.8`.
- Python range from package metadata: `>=3.10.0,<4.0.0`.
- Core dependencies include `pydantic>=2.7.4,<3.0.0`, `langsmith`, `tenacity`, `jsonpatch`, `PyYAML`, `typing-extensions`, `packaging`, `uuid-utils`, and `langchain-protocol`.
- Development is package-local in `libs/core`; the repository has package-level `pyproject.toml` and `uv.lock` files rather than a root `pyproject.toml`.
- Host inspection did not run `uv`; do not claim package commands succeeded unless they are run in the active environment.

## Public Import Pattern

Many core packages expose public symbols through lazy package-level imports. Prefer these stable module surfaces:

- `langchain_core.runnables` for `Runnable`, `RunnableLambda`, `RunnableGenerator`, `RunnableSequence`, `RunnableParallel`, `RunnableMap`, `RunnablePassthrough`, `RunnableAssign`, `RunnablePick`, `RunnableBranch`, `RunnableWithFallbacks`, `RunnableWithMessageHistory`, `RouterRunnable`, `RunnableConfig`, `ensure_config`, `patch_config`, `run_in_executor`, and configurable-field helpers.
- `langchain_core.messages` for `BaseMessage`, `HumanMessage`, `AIMessage`, `SystemMessage`, `ToolMessage`, message chunks, tool-call types, content-block typed dicts, `convert_to_messages`, `convert_to_openai_messages`, `message_to_dict`, `messages_to_dict`, `messages_from_dict`, `merge_content`, `merge_message_runs`, `filter_messages`, `trim_messages`, and OpenAI block translators.
- `langchain_core.tools` for `BaseTool`, `Tool`, `StructuredTool`, `tool`, `create_schema_from_function`, `convert_runnable_to_tool`, `create_retriever_tool`, rendering helpers, and tool schema errors.
- `langchain_core.language_models` for base chat/LLM interfaces, fake models used by unit tests, model profiles, and compatibility bridge behavior.
- `langchain_core.prompts` for prompt templates that are also `RunnableSerializable` objects.
- `langchain_core.documents` and `langchain_core.embeddings` for retrieval/data-processing primitives.
- `langchain_core.vectorstores` for `VectorStore` and `InMemoryVectorStore`.
- `langchain_core.output_parsers` for runnable output parsers.
- `langchain_core.load` and `langchain_core.load.serializable` for serialization contracts.
- `langchain_core._api` for deprecation decorators and warning helpers when maintaining public API transitions.

## Runnables and LCEL

`Runnable[Input, Output]` is the unit of work that supports `invoke`/`ainvoke`, `batch`/`abatch`, `stream`/`astream`, event/log streaming, config propagation, tracing tags/metadata, schema introspection, composition, retry, listeners, and configurability.

Practical constraints:

- `invoke` is the required sync implementation for custom runnable classes. Async methods default to running sync behavior in an executor unless overridden.
- `batch` defaults to parallel `invoke`; override only when the underlying primitive has a true batch API.
- LCEL composition uses `|` for `RunnableSequence` and dict literals or `RunnableParallel` for concurrent branches.
- Every runnable method accepts optional `RunnableConfig`; pass it through with `ensure_config`, `patch_config`, or `run_in_executor` when implementing custom behavior.
- Preserve input/output schema behavior (`input_schema`, `output_schema`, `config_schema`) because tools, prompts, routers, and tests depend on it.
- Deprecated paths such as old event/log methods can be intentionally covered for compatibility; do not remove warnings or tests without checking the deprecation schedule.

## Messages and Content Blocks

Messages are Pydantic models for prompt/chat I/O. Standard message classes include human, AI, system, chat, function, tool, and remove messages plus chunk variants.

Content blocks provide provider-agnostic multimodal structures:

- Standard blocks include text, image, audio, video, file, reasoning, citations/annotations, server tool calls/results, and related chunk forms.
- `NonStandardContentBlock` and `extras` preserve provider-specific data when a standardized field does not exist.
- Translators adapt provider-specific data, such as OpenAI image/data block formats, without making all core messages provider-specific.
- Utilities such as `convert_to_messages`, `convert_to_openai_messages`, `message_to_dict`, `messages_to_dict`, `messages_from_dict`, `merge_message_runs`, `filter_messages`, `trim_messages`, and `message_chunk_to_message` are important compatibility points.
- Message utilities should avoid mutating caller-provided message objects; representative unit tests assert original messages remain unchanged after filtering and merging.

## Tools

Tools are `RunnableSerializable` primitives used by agents and model tool binding, but app-level agent construction belongs in the agents/middleware sub-skill.

Key behavior:

- Use `@tool` for function-to-tool conversion and `convert_runnable_to_tool` for runnable-backed tools.
- Tool functions should have type hints for schema inference.
- Description precedence is explicit `description`, then function docstring, then `args_schema` description.
- `parse_docstring=True` expects Google-style docstrings and can raise `ValueError` when docstring arguments do not match annotations.
- `args_schema` must be correctly typed as a Pydantic schema or compatible schema object; bad annotations raise schema errors.
- Tool outputs can use `response_format="content"` or `"content_and_artifact"`; the latter expects a two-tuple for `ToolMessage` content and artifact.
- Provider-specific tool metadata belongs in `extras` when it does not fit standard fields.

## Prompts and Parsers

`BasePromptTemplate` is a `RunnableSerializable[dict[str, Any], PromptValue]` with `input_variables`, optional variables, input types, partial variables, tracing metadata/tags, and optional output parser.

Watch for:

- The reserved prompt variable name `stop`.
- Overlap between `input_variables` and `partial_variables`.
- Missing input variables and literal braces that should be escaped as doubled braces.
- Prompt serialization via `dumpd` and `is_lc_serializable`.

`BaseOutputParser` and related generation parsers are runnable serializable parsers over `str` or message model outputs. Async parse methods default through executor-backed sync parsing unless overridden.

## Documents, Embeddings, and Vector Stores

`Document` and `Blob` are data-processing/retrieval primitives, not chat multimodal message primitives. Use message content blocks for LLM I/O multimodality.

`Embeddings` defines:

- `embed_documents(texts: list[str]) -> list[list[float]]`.
- `embed_query(text: str) -> list[float]`.
- Async defaults `aembed_documents` and `aembed_query` that call sync methods in an executor.

`VectorStore` defines text/document add, delete, get-by-id, similarity search, async wrappers, and retriever conversion. Important compatibility expectations include:

- `add_texts` may delegate to subclass `add_documents` and validates metadata/id counts.
- `get_by_ids` may return fewer documents than requested, should not require output order to match input order, and should not raise merely because some IDs are missing.
- Async methods often default to executor-backed sync behavior unless the subclass provides native async implementations.
- `InMemoryVectorStore` is a safe local vector store for unit tests and smoke cases.

## Language Models and Callbacks

`BaseChatModel` and `BaseLLM` are core provider interfaces. They normalize input, produce generations/results, support callbacks/tracing, integrate with runnables, bind tools/structured output in chat-model paths, and carry model-profile metadata.

Use fakes for unit tests and smoke checks when network access is not required. Representative fake classes are exposed through `langchain_core.language_models` and `langchain_core.language_models.fake_chat_models`.

Callbacks and tracers are central to config propagation. When changing primitive execution paths, validate tags, metadata, run IDs, parent/child runs, and callback manager propagation where relevant.

## Serialization and Deprecation Utilities

`Serializable` is Pydantic-based and is not serializable by default. Serializable classes opt in with `is_lc_serializable`, expose stable namespaces with `get_lc_namespace`, and can define `lc_secrets` and `lc_attributes`.

Compatibility cautions:

- Do not serialize secrets directly; use secret IDs through `lc_secrets`.
- Avoid deprecated `lc_namespace` and `lc_serializable` attributes; use the class methods.
- Maintain deserialization compatibility when moving or renaming public classes.
- Use `deprecated`, `warn_deprecated`, and suppression helpers from `langchain_core._api` for public API transitions.
- Tests intentionally cover some deprecated methods to ensure warnings and compatibility behavior remain stable until removal.

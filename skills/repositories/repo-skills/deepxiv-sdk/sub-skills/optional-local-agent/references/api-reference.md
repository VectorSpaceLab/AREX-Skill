# Local Agent API reference

This route describes the source implementation in `deepxiv_sdk/agent/agent.py`, `graph.py`, `tools.py`, `state.py`, package exports, and the bundled usage examples. It is separate from the hosted `Reader.agent_search*` API.

## Installation and import boundary

The base `setup.py` install requires only the Reader/CLI dependencies. The `agent` extra declares:

- `openai>=1.0.0`
- `langgraph>=0.0.20`
- `langchain-core>=0.1.0`

The `all` extra repeats the base requirements and those three Agent requirements. Neither extra declares `tiktoken`, even though `deepxiv_sdk.agent.agent` executes `tiktoken.get_encoding("o200k_base")` at import time. The optional Agent therefore needs four importable components: `openai`, `langgraph`, `langchain_core`, and `tiktoken`.

`deepxiv_sdk.__init__` always exports `Reader` and the Reader exception classes. It tries to import `Agent`; if an `ImportError` occurs while loading the Agent module, it leaves `Agent` out of `__all__` rather than breaking the base import. Use the dependency probe before concluding that Agent functionality is installed.

## Constructor

Source signature:

```python
Agent(
    api_key: str,
    reader: Reader,
    model: str = "gpt-4",
    base_url: str | None = None,
    max_llm_calls: int = 20,
    max_time_seconds: int = 600,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    print_process: bool = False,
    stream: bool = False,
    max_consecutive_failures: int = 3,
    extra_body: dict | None = None,
    enable_thinking: bool | None = None,
)
```

- `api_key` is passed to `openai.OpenAI`; it may be a runtime provider credential or a provider-specific dummy value when the endpoint does not authenticate that way. Do not place a real value in instructions.
- `reader` is required and supplies paper search/head/section/raw/preview/brief operations to `ToolExecutor`.
- `model` is forwarded as `model` on every chat completion request.
- If `base_url` is truthy, the client is constructed with both `api_key` and `base_url`; otherwise only `api_key` is passed.
- `max_llm_calls` is the per-query graph call budget; `max_time_seconds` is the per-query wall-clock guard checked by the planning node.
- `max_tokens`, `temperature`, `stream`, and `print_process` are forwarded to the graph. `stream=True` uses the OpenAI-compatible streaming response shape and only works when the provider supports it.
- `max_consecutive_failures=0` disables the service circuit breaker. The default is 3 consecutive all-service-failure tool rounds.
- `extra_body` is copied into a new dictionary. If `enable_thinking` is not `None`, it overwrites/sets `extra_body["enable_thinking"]`.

A minimal valid construction is:

```python
from deepxiv_sdk import Agent, Reader

reader = Reader(token="runtime-token")
agent = Agent(api_key="runtime-llm-key", reader=reader, model="gpt-4")
answer = agent.query("Find and compare recent work on agent memory.")
```

The `reader` argument is intentionally shown here even though an older basic snippet in the usage document omitted it; the implementation requires it.

## Methods and persistence

### `query(question: str, reset_papers: bool = False) -> str`

Each invocation:

1. Optionally replaces `persistent_papers` with `{}` when `reset_papers=True`.
2. Creates a fresh graph state seeded with a shallow copy of the current persistent papers.
3. Sets the question, available-call counter, and start time.
4. Invokes a compiled LangGraph ReAct workflow.
5. Merges the final state's `papers` into `persistent_papers` and returns the extracted `prediction` (or a fallback answer).

Loaded papers persist across calls, but the message history does not: each query starts with a fresh question and a system prompt containing the persisted paper metadata. Use `reset_papers=True` for a single query or `reset_papers()` before a new topic. The graph's section/full-paper/search caches are initialized per query and are not the Agent's cross-query persistence store.

On `print_process=True`, the Agent prints question, round/termination, paper count, token estimate, and errors. The token estimate uses the `o200k_base` tiktoken encoding over final state messages; it is reporting only, not a separate stopping budget.

### `get_loaded_papers() -> dict`

Returns the live `persistent_papers` dictionary. A loaded entry contains `arxiv_id`, `title`, `abstract`, `authors`, `sections`, `token_count`, `categories`, `publish_at`, and `loaded_sections`. Treat the returned structure as read-only unless deliberately managing Agent state.

### `reset_papers() -> None`

Sets `persistent_papers` to an empty dictionary. With verbose process printing it emits a reset message.

### `add_paper(arxiv_id: str) -> bool`

- Returns `True` immediately if the ID is already persistent.
- Calls `reader.head()` and stores normalized metadata plus an empty `loaded_sections` map on success.
- Returns `False` for `NotFoundError`, `BadRequestError`, an empty head result, or an ID that is not indexed yet. The source calls out very recent papers (often under 1–3 days) as a common reason.
- Propagates other API failures such as server-side failures, authentication failures, or rate limits. Catch those at the caller boundary.

The ReAct `load_paper` tool has a related but not identical contract: it catches expected Reader exceptions inside `ToolExecutor` and returns an explanatory result string for the model.

## Provider request behavior

The graph's `call_llm()` sends OpenAI-compatible `chat.completions.create` parameters:

- `model`, `messages`, `max_tokens`, `temperature`, `stream`
- `tools` and `tool_choice="auto"` when tools are supplied
- `extra_body` only when the merged dictionary is non-empty

It retries an unsuccessful/empty/error call up to three attempts by default, with bounded exponential sleeps. Reasoning content is printed in verbose non-streaming mode but is deliberately not added to the message history. For a reasoning model that rejects multi-round tool histories, configure `enable_thinking=False`; this becomes `extra_body={"enable_thinking": False}` and is also used on the forced final-answer request.

A provider/model's exact accepted `extra_body` fields are not validated by DeepXiv; the OpenAI-compatible endpoint decides. `enable_thinking` is only a convenience merge, not a universal OpenAI parameter.

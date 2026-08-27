# Logic Adapter API Reference

## When to read

Read this before configuring ChatterBot logic adapters, changing response selection, or implementing a custom adapter.

## Verified signatures

Installed-package inspection for ChatterBot 1.2.14 confirmed:

```python
LogicAdapter(chatbot, **kwargs)
BestMatch(chatbot, **kwargs)
MathematicalEvaluation(chatbot, **kwargs)
TimeLogicAdapter(chatbot, **kwargs)
SpecificResponseAdapter(chatbot, **kwargs)
UnitConversion(chatbot, **kwargs)
LLMLogicAdapter(chatbot, **kwargs)
OllamaLogicAdapter(chatbot, **kwargs)
OpenAILogicAdapter(chatbot, **kwargs)
```

A logic adapter implements:

```python
can_process(statement) -> bool
process(statement, additional_response_selection_parameters=None) -> Statement
```

`process` must return a `Statement` whose `confidence` is between `0` and `1`.

## Base `LogicAdapter` kwargs

| Keyword | Effect |
| --- | --- |
| `search_algorithm_name` | chooses a search algorithm from the bot, default `indexed_text_search` |
| `maximum_similarity_threshold` | stops search when a match reaches the threshold; default `0.95` |
| `response_selection_method` | callable or import path; default `get_first_response` |
| `default_response` | string or list of fallback response strings |

If no default response is configured, `get_default_response` tries storage `get_random()`, and if storage is empty it returns the input statement with confidence `0`.

## `BestMatch`

`BestMatch` searches storage for statements close to the input and selects a response to the closest match.

Extra kwarg:

- `excluded_words`: list of words that should prevent returned statements containing those words.

Search behavior depends on the storage/search algorithm:

- SQL-style indexed search finds a matching `in_response_to` and then selects a response from matching rows.
- Redis semantic vector search can return the vector result directly because vector similarity already represents the match.

## `SpecificResponseAdapter`

Required kwargs:

- `input_text`: exact input string, or a spaCy matcher pattern when `matcher` is supplied.
- `output_text`: response string or callable returning a string.

Optional kwargs:

- `matcher`: a spaCy matcher class such as `spacy.matcher.Matcher`.
- `language`: ChatterBot language class for spaCy model selection when matcher mode is used.

## Deterministic tool-capable adapters

These adapters are normal logic adapters and also implement `MCPToolAdapter` methods:

| Adapter | Tool name | Dependency |
| --- | --- | --- |
| `MathematicalEvaluation` | `calculate` | `mathparse` base dependency |
| `TimeLogicAdapter` | `get_current_time` | spaCy model for normal phrase matching |
| `UnitConversion` | `convert_units` | optional `pint` |

`MCPToolAdapter` exposes:

```python
get_tool_schema() -> dict
execute_as_tool(**kwargs) -> Any
validate_tool_parameters(**kwargs) -> bool
```

The helper functions `convert_to_openai_tool_format` and `convert_to_ollama_tool_format` convert a tool schema to provider formats used by the LLM adapters.

## Experimental LLM adapters

`LLMLogicAdapter` requires `model`. Optional kwargs include:

- `host`: provider endpoint override.
- `logic_adapters_as_tools`: list of adapter import paths or configs exposed as tools.
- `force_native_tools`: override auto-detection of native tool support.
- `min_confidence` / `max_confidence`: confidence range for LLM responses.
- `conversation_context_count`: prior statements to include.
- `system_message`: custom system prompt.

`OllamaLogicAdapter` defaults `host` to `http://localhost:11434` and uses the `ollama` client. It detects native tool support by known model names and template inspection, otherwise falls back to prompt-based tool calls.

`OpenAILogicAdapter` uses the `openai` client and assumes current OpenAI models support native tool calling. It can accept a custom `host` as a base URL.

## Response selection functions

- `get_first_response(input_statement, response_list, storage=None)` returns the first option.
- `get_random_response(...)` returns a random option.
- `get_most_frequent_response(...)` uses storage to count common responses to the input.

Use these as functions or import paths in adapter configuration.

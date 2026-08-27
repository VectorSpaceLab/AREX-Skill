# OptiLLM API Surface

Read this when you need the package-level exports, dispatch helpers, or response-shape semantics behind OptiLLM tasks. Details here are distilled from installed-package inspection and source evidence.

## Public package exports

Importing `optillm` exposes:

- `main`, `app`, and `server_config` for the Flask server entry point.
- `known_approaches` and `plugin_approaches` for dispatch state.
- `parse_combined_approach(model, known_approaches, plugin_approaches)` for splitting a model string into operation, approach list, and base model.
- `parse_conversation(messages)` and `extract_optillm_approach(content)` for request-message parsing.
- `load_plugins()` for plugin discovery.
- `count_reasoning_tokens(text, tokenizer=None)` for `<think>...</think>` accounting.
- `execute_single_approach`, `execute_combined_approaches`, `execute_parallel_approaches`, and `generate_streaming_response` for server dispatch internals.

## Verified signatures

```python
parse_combined_approach(model: str, known_approaches: list, plugin_approaches: dict)
parse_conversation(messages)
extract_optillm_approach(content)
execute_single_approach(approach, system_prompt, initial_query, client, model, request_config: dict = None, request_id: str = None)
execute_n_times(n: int, approaches, operation: str, system_prompt: str, initial_query: str, client, model: str, request_config: dict = None, request_id: str = None)
none_approach(client, model, original_messages, request_id=None, **kwargs)
generate_streaming_response(final_response, model)
```

## Parsing examples

```python
from optillm import known_approaches, parse_combined_approach

parse_combined_approach("moa-gpt-4o-mini", known_approaches, {})
# ("SINGLE", ["moa"], "gpt-4o-mini")

parse_combined_approach("bon|moa|mcts-gpt-4o-mini", known_approaches, {})
# ("OR", ["bon", "moa", "mcts"], "gpt-4o-mini")

parse_combined_approach("cot_reflection&moa-gpt-4o-mini", known_approaches, {})
# ("AND", ["cot_reflection", "moa"], "gpt-4o-mini")
```

`parse_conversation` converts a list of chat messages into a system prompt plus a joined user/assistant transcript. If a system or user message contains `<optillm_approach>slug</optillm_approach>`, that tag is removed from content and returned as the selected approach.

## Response behavior

- `none` approach returns the upstream provider response dictionary directly when possible.
- Non-`none` approaches normally return `(response_text, completion_tokens)`, then the server wraps the text in an OpenAI-compatible response object.
- Parallel `|` composition returns multiple responses as a list. With `n > 1`, results may be flattened into multiple choices.
- Streaming responses are converted into server-sent events with one content chunk per response and a final `data: [DONE]`.
- Reasoning tokens are estimated from text inside `<think>...</think>` tags and added under `usage.completion_tokens_details.reasoning_tokens`.

## Known approach list

`known_approaches` contains:

```text
none, mcts, bon, moa, rto, z3, self_consistency, pvg, rstar, cot_reflection, plansearch, leap, re2, cepo, mars
```

Read [../sub-skills/optimization-approaches/references/approach-catalog.md](../sub-skills/optimization-approaches/references/approach-catalog.md) for task-fit guidance and signatures.

## Plugin discovery

`load_plugins()` scans package plugins and, when configured, local plugins. A plugin is loaded when its module has both a `SLUG` attribute and a `run` function. Loaded plugin slugs are available in `plugin_approaches` and can participate in the same model-prefix parser as approaches. Read [../sub-skills/plugins-and-tools/references/plugin-catalog.md](../sub-skills/plugins-and-tools/references/plugin-catalog.md) for plugin details.

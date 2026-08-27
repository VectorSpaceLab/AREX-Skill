# Optional local Agent troubleshooting

## `Agent` is missing from `deepxiv_sdk`

**Likely cause:** an import in the optional Agent stack failed. The package root intentionally catches `ImportError` around the Agent import, so the base `Reader` import can still succeed while `Agent` is absent.

**Check:** run [`../scripts/agent_dependency_probe.py`](../scripts/agent_dependency_probe.py) from any working directory. It checks package/module availability without network access or an LLM call.

**Fix:** install the declared optional set:

```bash
python -m pip install "deepxiv-sdk[agent]"
```

If the probe reports `tiktoken` missing, install it explicitly:

```bash
python -m pip install tiktoken
```

This extra install is necessary because the 1.0.0 `agent` and `all` metadata omit `tiktoken`, while `deepxiv_sdk.agent.agent` imports and initializes it at module import. If an import still fails, inspect the probe's reported module and use the same Python interpreter for installation and execution.

## Agent construction fails before the first query

The source constructor requires both `api_key` and `reader`. Use:

```python
from deepxiv_sdk import Agent, Reader
agent = Agent(api_key="runtime-llm-key", reader=Reader(token="runtime-data-token"))
```

An older usage snippet shows an Agent without `reader`; that snippet does not match the current constructor and should not be copied unchanged.

## Reasoning-content provider error

**Symptom:** a provider rejects a later tool round with wording like “Reasoning content is only supported as the last assistant message.”

**Cause:** reasoning content from an intermediate assistant response is incompatible with the provider's multi-round tool history.

**Fix:** configure the provider option through the Agent:

```python
agent = Agent(
    api_key="runtime-provider-key",
    reader=reader,
    model="reasoning-model",
    enable_thinking=False,
)
```

The flag is merged into `extra_body` and forwarded on normal and forced-answer calls. If a provider needs additional fields, pass `extra_body={...}`; when both supply `enable_thinking`, the explicit constructor flag wins. DeepXiv does not validate provider-specific fields.

## Provider endpoint or model failures

Use `base_url` only for the LLM's OpenAI-compatible endpoint. It does not change the Reader's data-service endpoint. Confirm the model supports chat completions, function/tool calls, and—when enabled—streaming. Keep credentials in runtime configuration, not in skill files.

`call_llm()` makes up to three attempts per completion call. This retry behavior is separate from `max_llm_calls`; a retry does not constitute a new graph planning round in state. Use a small `max_llm_calls` and `max_time_seconds` for safe experiments.

## A new paper cannot be loaded

For `agent.add_paper(id)`:

- `False` means `NotFoundError`, `BadRequestError`, an empty head response, or a not-yet-indexed paper. Recent papers may take roughly 1–3 days to appear.
- A successful load returns `True` and creates the persistent metadata entry.
- A server, authentication, or rate-limit API exception propagates. Catch it and decide whether to stop/back off; do not rewrite it as a missing paper.

For the ReAct `load_paper` tool, `NotFoundError` and `BadRequestError` become model-visible recoverable strings. The model should try another candidate, broaden the search, or correct the ID—not repeat the same unavailable ID.

## “Paper is not loaded” or “section not found”

These are protocol errors, not service outages:

1. Call `load_paper` first.
2. Copy the exact section name from the metadata list; section matching is exact and case-sensitive.
3. Check section token counts and use a smaller section/preview before requesting full text.

These results are not classified as service failures and should not increment the breaker.

## The Agent stops after repeated failures

This is usually the intended circuit breaker. A round counts as a failure only when **every** tool result contains one of the service-failure markers. The default threshold is three consecutive all-failure rounds. The next LLM request is forced to be tools-less and must answer from gathered context, clearly acknowledging insufficient evidence or temporary service unavailability.

A single successful/non-service result resets the consecutive counter. Set `max_consecutive_failures=0` to disable the breaker, but retain a finite call/time budget; disabling it can allow repeated failing tool rounds until another limit stops the graph.

## The Agent stops near the call or time budget

The planning node checks elapsed time and available calls. The graph requests a final answer when it is within two rounds of `max_llm_calls`; if the available count is exhausted, it returns an exceeded-call termination. A timeout answer is returned when `max_time_seconds` is exceeded. Lower paper-reading scope and increase the budgets deliberately rather than assuming a tool is broken.

## Context unexpectedly disappears

`persistent_papers` survives between `query()` calls, but message history and section/full-paper/search caches are query-local. `reset_papers=True`, `reset_papers()`, or a new Agent clears paper context. The next query's prompt includes only each paper's ID, title, and a short abstract prefix; it does not include previously read section bodies.

## Dependency probe cannot find the package

The helper can run from any current directory and does not modify the environment. If it reports that `deepxiv_sdk` itself is unavailable, install the base package in the interpreter being used. If only optional modules are absent, install the optional requirements and the explicit `tiktoken` workaround. The helper never tests credentials, network connectivity, server availability, or model behavior.

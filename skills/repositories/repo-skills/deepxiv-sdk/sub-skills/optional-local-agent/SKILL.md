---
name: optional-local-agent
description: "Operate DeepXiv's optional OpenAI-compatible LangGraph ReAct Agent
  for local paper search, reading, and multi-turn analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Optional local Agent

Use this route when the task needs DeepXiv's **local** ReAct loop with a caller-selected OpenAI-compatible chat model. It owns the `deepxiv_sdk.Agent` class, its optional dependency boundary, provider request options, paper-context persistence, tool orchestration, budgets, and failure recovery.

Do **not** use this route for hosted `Reader.agent_search*` calls or `deepxiv agent ...` CLI configuration/query syntax; route those to the Reader/CLI sibling skills.

## Fast route

1. Run [`scripts/agent_dependency_probe.py`](scripts/agent_dependency_probe.py) before diagnosing an optional-install problem. It performs local import/spec checks only; it never calls an LLM or the paper service.
2. Install the optional set with `python -m pip install "deepxiv-sdk[agent]"` (or `[all]`). The published 1.0.0 extras declare `openai`, `langgraph`, and `langchain-core`, but **do not declare `tiktoken`**, although `deepxiv_sdk.agent.agent` imports it at module load. Install `tiktoken` explicitly when the probe reports it missing.
3. Construct `Reader` and pass it explicitly to `Agent`; `reader` is a required constructor argument in source. Supply the model API key to `api_key`, and use `base_url` for an OpenAI-compatible provider.
4. For reasoning models used across tool rounds, set `enable_thinking=False` (or pass an equivalent provider field through `extra_body`) when the provider rejects reasoning content in non-final assistant messages.
5. Keep `max_llm_calls` and `max_time_seconds` bounded. Preserve context across follow-up `query` calls unless `reset_papers=True` or `reset_papers()` is intentional.
6. Follow the load-first and progressive-reading protocol in [`references/tool-protocol.md`](references/tool-protocol.md); consult [`references/troubleshooting.md`](references/troubleshooting.md) for missing papers versus service failures.

## Operating rules

- The base package can expose `Reader` without the Agent. `deepxiv_sdk.__init__` attempts the Agent import and silently omits `Agent` when an optional import raises `ImportError`; check dependencies rather than assuming the symbol exists.
- Never put a key, token, private endpoint, checkout path, or environment name in a public skill or example. Pass secrets at runtime.
- Treat `add_paper()` returning `False` as a recoverable missing/not-yet-indexed result. Do not treat it as proof that the ID is invalid forever; try a different ID or broader search. Genuine server/auth/rate-limit failures propagate from `add_paper()`.
- A tool result describing a malformed argument, an unloaded paper, or a missing section is recoverable and must not by itself trip the service circuit breaker. Repeated service-side result markers do trip it and force a tools-less final-answer call.
- `query()` returns the graph's extracted answer, but catches graph exceptions and returns an `Error: ...` string. `add_paper()` has different behavior: expected not-found/bad-request cases return `False`, while genuine API failures propagate.

## References

- [`references/api-reference.md`](references/api-reference.md) — constructor, methods, provider fields, state and return contracts.
- [`references/workflows.md`](references/workflows.md) — bounded first query, persistent follow-up, manual preload, and reasoning-provider recipes.
- [`references/tool-protocol.md`](references/tool-protocol.md) — exact tool order, load/read rules, caches, budgets, and breaker classification.
- [`references/troubleshooting.md`](references/troubleshooting.md) — optional-import, provider, paper availability, and termination diagnostics.

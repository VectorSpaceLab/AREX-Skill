---
name: rollout-and-tools
description: "Use when modifying verl rollout engines, multi-turn agent loops,
  function tools, tool schemas, rollout traces, or generation-server flows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Rollout And Tools

Use this sub-skill when the task touches verl rollout behavior rather than trainer optimizer policy: rollout backend config, async generation servers, multi-turn agent loops, tool calling, function-tool schema authoring, tokenization sanity checks, trace output, or rollout visualization.

## Route The Task

- For rollout backend choices and config fields, read [Rollout workflows](references/rollout-workflows.md).
- For `@function_tool`, `BaseTool`, schema loading, and tool dispatch, read [Tooling API](references/tooling-api.md).
- For tokenization warnings, tool parser issues, trace volume, and viewer pitfalls, read [Troubleshooting](references/troubleshooting.md).
- To preflight a Python file used by `actor_rollout_ref.rollout.multi_turn.function_tool_path`, run [validate_function_tool.py](scripts/validate_function_tool.py).

## Safe Defaults

- Prefer `actor_rollout_ref.rollout.mode=async`; sync rollout mode is removed.
- Use `actor_rollout_ref.rollout.multi_turn.enable=True` plus `actor_rollout_ref.rollout.agent.default_agent_loop=tool_agent` for built-in tool-calling loops.
- Use function tools for stateless `fn(**parameters)` calls; use native `BaseTool` tools for lifecycle, per-trajectory state, sandbox resources, or `tools_kwargs`.
- Keep `tokenization_sanity_check_mode=strict` until the model chat template has been validated; use `ignore_strippable` only for whitespace-only template drift.
- Treat rollout viewer as an interactive diagnostic over generated JSONL rollout data, not as a required runtime dependency.

## Verification Targets

- CPU-safe candidates: function-tool registration/return tests, `ToolAgentLoop._call_tool` error-handling tests, Qwen3 parser safety tests, and vLLM CLI argument parsing tests.
- When changing multi-turn or tool parsing behavior, include a case where a malformed tool call returns a readable `ToolResponse` instead of crashing the loop.

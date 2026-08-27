# Troubleshooting Rollout And Tools

## Function Tool Registration Fails

Symptoms: errors mention no docstring, missing type hint, no description for an argument, variadic parameters, or duplicate registration.

Checks:

1. Every decorated function has a Google-style docstring with `Args:`.
2. Every parameter has a type annotation and a matching `Args:` entry.
3. No function uses `*args` or `**kwargs`.
4. Tool names are unique in the file and do not collide with native YAML tools.
5. The file path exists from the worker process current directory or is configured as an absolute/expanded path by the launcher.

Use `scripts/validate_function_tool.py path/to/tools.py --pretty` for a JSON report.

## Tool Calls Do Not Execute

- If the model emits an unknown name, compare generated name with loaded schema names and any per-sample `extra_info.tool_selection`.
- If arguments fail JSON parsing, inspect the model's tool-call format and `multi_turn.format` (`hermes`, `qwen3_coder`, `gpt-oss`, `gemma4`, or the parser supported by the current checkout).
- If a function needs trajectory state or cleanup, it should be a native `BaseTool`, not a function tool.
- If tool responses are truncated unexpectedly, check `max_tool_response_length` and `tool_response_truncate_side`.

## Tokenization Sanity Warning

Warning text: `Inconsistent training and inference tokenization detected`.

Meaning: delta-based assistant/tool token accounting does not match full chat-template tokenization. This matters for RL because PPO should train on tokens produced by the policy, not on a later decoded/re-encoded transcript.

Triage:

1. Keep `tokenization_sanity_check_mode=strict` while debugging.
2. Compare the logged mismatch substring with the model chat template.
3. For Qwen3-style tool calls, inspect whether XML/function-call extraction changes assistant content.
4. Use `ignore_strippable` only if the mismatch is whitespace-only and expected.
5. Avoid `disable` until a small rollout proves response masks and token IDs are stable.

## Qwen3 Tool Parser Safety

The Qwen3 XML parser handles typed parameters from model output. Array-like values should be parsed as literals, not executed as code. If changing parser code, keep a CPU regression case where an array parameter contains a malicious-looking Python expression and verify it is returned as data, not executed.

## Rollout Trace Is Too Large

Trace backends can store one trace per trajectory and can become expensive. Set `actor_rollout_ref.rollout.trace.max_samples_per_step_per_worker` to a small number. With GRPO `n > 1`, total traces scale as workers times selected samples times `n`.

For readable traces, enable `token2text=True`; for lower overhead, keep it false and inspect token IDs or sampled JSONL rollout data.

## Viewer Or Rollout Data Problems

The interactive rollout viewer expects rollout JSONL files grouped by step and UI dependencies. If it fails:

- Confirm `trainer.rollout_data_dir` is enabled and contains `.jsonl` files.
- Check JSONL records for string fields that should be masked before sharing.
- Prefer a simple JSONL inspection script in CI; reserve the interactive viewer for local debugging.
- Do not make production rollout depend on viewer packages.

## Backend Argument Drift

If vLLM/SGLang CLI or engine kwargs tests fail after changing rollout config:

- Verify whether the flag belongs in generic `RolloutConfig.engine_kwargs` or a backend-specific worker path.
- Keep unknown backend args from leaking into another backend.
- Re-run CPU-safe rollout CLI argument tests before GPU integration tests.

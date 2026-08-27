# Troubleshooting Experimental And Environment Training

Start with the warning or failure class, then check version gates, optional extras, service assumptions, and environment contract shape. Do not debug by launching full training before validating imports and the environment factory contract.

## Warning And Version Gates

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `TRLExperimentalWarning` on import | A `trl.experimental` module was imported. | Keep the warning for user-facing caution, or set `TRL_EXPERIMENTAL_SILENCE=1` only for noisy CI/logs. |
| Warning that `environment_factory` or `rollout_func` is experimental | GRPO agent API is explicitly unstable. | Acknowledge risk; pin versions for reproducible projects. |
| `environment_factory` import/version error | `transformers<5.2.0`. | Upgrade to a version that includes `environment_factory` tool support. |
| `tools=` version error | `transformers<5.0.0`. | Upgrade transformers before tool-calling GRPO. |
| `jmespath` missing | Tool response parsing dependency is absent. | Install `jmespath` in the training environment. |
| Chat template does not support tool calling | Tokenizer/template cannot render user → assistant tool call → tool response. | Use a model/template with tool calling support or provide a compatible chat template. |

## Optional Extras

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `trl.experimental.openreward` import fails | `openreward` SDK is not installed. | Install the OpenReward extra in the environment used for training. |
| OpenReward catalog auth fails | Missing or invalid `OPENREWARD_API_KEY`. | Provide the key via environment or spec argument; confirm secrets expected by the ORS environment. |
| Self-hosted OpenReward URL cannot create sessions | SDK expects separate API/session subdomains. | Set the API and session URL overrides to the same single-host URL before constructing the spec. |
| `trl.experimental.harbor` import or construction fails | Harbor extra or compatible Python dependencies missing. | Install the Harbor extra and confirm the Python version satisfies Harbor. |
| Harbor training complains about vLLM/transformers | Documented Harbor flow uses vLLM and `environment_factory`. | Install a compatible vLLM and `transformers>=5.2.0`; route backend sizing to scaling/backends. |
| Sandbox backend fails | Docker daemon, E2B credentials, or cloud backend unavailable. | Validate the backend independently; set credentials such as `E2B_API_KEY` when using cloud sandboxes. |

## Environment Contract Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `reset` missing | Factory returns an object without callable `reset`. | Add `reset(self, **kwargs) -> str | None`; dataset row columns are passed as kwargs. |
| No tools discovered | Methods are private, static/non-methods, or only generic `step` exists. | Expose typed public instance methods for model actions and keep helpers underscore-prefixed. |
| Tool schema generation fails | Missing type hints or docstring argument descriptions. | Add typed parameters/return annotations and docstrings with `Args:` entries. |
| Tool called in wrong state | Multi-environment class exposes all tools simultaneously. | Raise `ValueError` with a concise message; TRL returns it as a tool response. |
| Reward always zero | Reward function is not reading env state, or state resets before scoring. | Store `env.reward` during tool calls and return `[env.reward for env in environments]`. |
| Episodes truncate early | `max_completion_length` is too low for multi-turn text plus tool outputs. | Increase it and consider limiting tool output length. |
| Infinite tool loop | Model keeps calling tools. | Set `max_tool_calling_iterations` and make terminal tool responses clear. |

## Service And Concurrency Failures

- OpenEnv training opens one environment connection per rollout slot; shared Spaces or default single-session servers commonly fail under training load.
- Match OpenEnv server `max_concurrent_envs` to at least the generation batch size.
- Harbor sandbox provisioning can be sequential or slow; prefer cloud backends only when credentials, cost, and cluster network policy are already handled.
- Tool outputs can dominate token budgets; truncate long shell/server output in the harness and return actionable summaries.
- Credentials for environment services are runtime configuration, not code constants. Do not write keys into datasets, skills, or examples.

## `rollout_func` Mismatch

Use `rollout_func` only when a typed tool environment is not enough. If a custom rollout fails:

- Ensure it returns `prompt_ids`, `completion_ids`, and `logprobs` with the expected per-prompt/per-generation shape.
- Preserve chat/multimodal prompt structure until the backend boundary.
- Forward reward fields explicitly if reward functions need them.
- Do not combine `rollout_func` and `environment_factory` unless the trainer version explicitly supports the intended interaction; normally choose one agent loop owner.

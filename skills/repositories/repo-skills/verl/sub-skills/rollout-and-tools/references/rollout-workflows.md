# Rollout Workflows

## Main Rollout Shape

verl rollout is configured under `actor_rollout_ref.rollout` and is expected to run in async mode. `RolloutConfig` rejects `mode=sync`; unknown modes warn and only async is supported. Core rollout knobs include backend `name`, sampling fields (`temperature`, `top_k`, `top_p`, `n`), sequence limits (`prompt_length`, `response_length`, `max_model_len`, `max_num_seqs`), parallelism (`tensor_model_parallel_size`, `data_parallel_size`, `expert_parallel_size`), and backend-specific `engine_kwargs`.

Do not decide optimizer, actor, critic, or reward-model policy from this sub-skill. Only cross into training config when rollout settings must remain aligned with the trainer, such as weight wake/sleep, logprob availability, or tokenization-compatible response masks.

## Backend Routing

- `name: sglang` is the documented multi-turn route and supports SGLang async server flows.
- vLLM and SGLang both implement async LLM server APIs used by Agent Loop: OpenAI-style chat completion and token-in/token-out generation.
- HF/TGI-style generation routes are handled by generation server entrypoints and worker/model-engine integrations; inspect the active worker backend before adding backend-only flags.
- Installation of vLLM, SGLang, or serving backends belongs to setup guidance, not this sub-skill.

## Agent Loop Architecture

`AgentLoopBase.run(sampling_params, **kwargs)` returns an `AgentLoopOutput` with `prompt_ids`, `response_ids`, and `response_mask`. In training, `response_mask` marks model-generated tokens as `1` and tool/environment response tokens as `0`, so preserving exact token boundaries matters.

The async rollout flow is:

1. The trainer samples a batch and calls `AgentLoopManager.generate_sequences`.
2. The manager wakes async LLM servers and synchronizes weights from the training engine.
3. The manager splits the batch across `AgentLoopWorker` instances.
4. Each worker creates an agent loop for a prompt, runs it concurrently, and gathers `AgentLoopOutput`.
5. `LLMServerClient.generate` uses sticky `request_id` routing so later turns in the same trajectory hit the same server instance.
6. After rollout, servers sleep/free cache/offload according to backend support.

## Multi-Turn Tool Agent

A typical tool-calling config is:

```yaml
actor_rollout_ref:
  rollout:
    mode: async
    name: sglang
    multi_turn:
      enable: true
      format: hermes
      function_tool_path: path/to/tools.py
      max_parallel_calls: 1
      max_tool_response_length: 256
      tokenization_sanity_check_mode: strict
    agent:
      default_agent_loop: tool_agent
```

`ToolAgentLoop` maintains a state machine: prepare prompt, generate, parse tool calls, execute tools, append tool responses, and continue until response length or turn limits are reached. It can filter available tools per sample through `extra_info.tool_selection` when the dataset provides it.

## Tokenization Sanity

Multi-turn rollout uses delta-based tokenization to preserve generated assistant token IDs instead of re-tokenizing the final chat history. This guards against tool parsers or chat templates changing content after generation. The sanity modes are:

- `strict`: default; warn on any mismatch between delta and full tokenization.
- `ignore_strippable`: ignore whitespace-only differences while warning on meaningful drift.
- `disable`: use only after validating the model/template combination separately.

Qwen3/Qwen3-style XML tool parser work should keep this warning in mind: parser normalization, decoded/re-encoded message history, or template-specific stop tokens can all create real training drift.

## Traces And Visualization

Rollout tracing is configured at `actor_rollout_ref.rollout.trace`:

```yaml
actor_rollout_ref:
  rollout:
    trace:
      backend: weave  # or mlflow or trackio
      token2text: false
      max_samples_per_step_per_worker: 5
```

`rollout_trace_op` marks traced functions and `rollout_trace_attr` identifies trajectory metadata such as step, sample index, rollout index, validation mode, and experiment name. Set `max_samples_per_step_per_worker` to avoid tracing every trajectory in large GRPO jobs.

The rollout viewer is an interactive JSONL viewer for `trainer.rollout_data_dir` output. It depends on UI packages and a specific Textual version in the source implementation, so treat it as reference behavior: inspect JSONL records, mask sensitive strings before display, and avoid making generated runtime docs depend on the original viewer script.

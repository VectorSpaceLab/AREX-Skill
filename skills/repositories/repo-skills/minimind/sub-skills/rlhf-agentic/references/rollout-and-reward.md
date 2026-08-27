# Rollout, Reward, Tool Use, and Context Packing

## Purpose

Read this when planning PPO, GRPO/CISPO, or Agentic RL reward/rollout behavior. This reference distills the rollout-engine, reward-model, tool-call, and response-mask behavior needed to debug post-training without reopening source evidence.

## Rollout engine abstraction

MiniMind post-training separates policy optimization from trajectory sampling through a rollout engine. A rollout returns:

| Field | Meaning | Used by |
|---|---|---|
| `output_ids` | Prompt plus generated completion token ids | New policy/ref log-prob computation |
| `completion_ids` | Generated completion token ids only | Decoding, EOS masking, response length |
| `per_token_logps` | Old policy log-probs from rollout time | PPO/GRPO/CISPO ratio computation |
| `completions` | Decoded completion text | Reward functions and debug logs |
| `prompt_lens` | Prompt length for each sampled row | Completion position indexing |
| `completion_mask` | Valid generated-token mask | Loss masking and length metrics |

### Torch rollout

Torch is the default and safest engine. It repeats prompts by `num_generations`, calls model `generate`, decodes completions, and computes per-token log-probs from the current policy. `update_policy(model)` simply swaps the in-process policy model reference.

Use torch when:

- debugging data, rewards, or short runs;
- the user has not launched a SGLang service;
- CPU or single-GPU correctness matters more than throughput;
- sequence length, generation count, and batch size are still being tuned.

### Optional SGLang rollout

SGLang is optional and service-based. The rollout client expects a local HTTP service that can:

- answer a health check;
- accept `/generate` requests with `input_ids`, sampling parameters, and `return_logprob: true`;
- return output token ids and per-token log-probs;
- accept `/update_weights_from_disk` with a model path when policy weights are synchronized;
- optionally accept `/flush_cache`.

SGLang `update_policy` behavior distilled from evidence:

1. unwrap the policy model from DDP/compile wrappers when needed;
2. save current policy weights and tokenizer to a dedicated shared checkpoint path;
3. POST that path to `/update_weights_from_disk`;
4. broadcast success/failure across DDP ranks;
5. raise an error if the update failed.

Planning implications:

- The shared checkpoint path must be dedicated to this run and safe to overwrite.
- SGLang is not a substitute for missing model artifacts; it requires a compatible model/tokenizer directory and CUDA-capable service environment.
- If `/generate` does not return usable log-probs, GRPO/PPO ratios are invalid. Fall back to torch.
- If `/update_weights_from_disk` fails, continuing with stale rollout weights corrupts the on-policy assumption. Stop or switch to torch.
- Use the smoke helper's dry SGLang check first; enable its local health probe only when the user confirms a local service is running.

```bash
python scripts/reward_toolcall_smoke.py \
  --rollout-engine sglang --sglang-base-url http://localhost:8998
```

The command above does not contact the service unless `--probe-sglang` is added.

## Reward Model route

The default PPO/GRPO/CISPO reward route uses an external Reward Model. The distilled interface is:

- load tokenizer and model from a local reward-model directory with remote-code trust enabled by the underlying model loader;
- build a short evaluation conversation from prior messages and the candidate response;
- call the reward model's `get_score(tokenizer, eval_messages)` method;
- clamp returned score to `[-3.0, 3.0]`.

Required planning checks:

- The reward-model directory exists and contains model/config/tokenizer files for the selected framework.
- The reward model exposes the expected scoring method.
- The selected device and dtype can load the reward model and policy together.
- The user understands that model-based reward can be gamed and may not reflect final task quality.

If a task has precise correctness criteria, prefer adding rule or `gt` verification to the reward plan rather than relying only on the Reward Model score.

## RLAIF reward components for PPO/GRPO/CISPO

For plain RLAIF responses, the evidence reward includes:

| Component | Effect |
|---|---|
| Response length window | Adds reward when response text length is in a moderate range and penalty when too short/long. |
| Thinking tag handling | If `</think>` appears, rewards reasonable thinking length and a single closing tag; penalizes malformed/overlong thinking. |
| Repetition penalty | Penalizes repeated n-grams in the answer region. |
| Reward Model score | Adds dense scalar quality feedback from the external Reward Model. |

PPO places the scalar reward at the last valid response token, then computes token advantages with GAE. GRPO/CISPO groups scalar rewards by prompt and generation.

## GRPO/CISPO grouping

For each prompt:

1. sample `num_generations` completions;
2. compute a scalar reward for each completion;
3. form a group of rewards `[r_1, ..., r_N]`;
4. compute `advantage = (reward - group_mean) / (group_std + 1e-4)`;
5. apply token-level KL against the frozen reference model;
6. apply either classic GRPO ratio clipping or CISPO's clipped importance weight times log-prob.

Watch `group_reward_std` or equivalent debug metrics. When group standard deviation is near zero, all generations are receiving nearly the same reward and learning signal disappears.

## Agentic RL multi-turn flow

Agentic RL adds a delayed environment-style loop:

1. Format the current messages and tools through the chat template.
2. Generate assistant text for one turn.
3. Parse all `<tool_call>...</tool_call>` JSON objects in the answer region.
4. For each valid call, execute a deterministic mock tool and append a `tool` observation message.
5. If at least one tool was called and max turns is not reached, format the expanded context and continue.
6. Pack prompt, generated assistant tokens, and tool observation tokens into one training sequence.
7. Score the whole trajectory once with tool, format, `gt`, repetition, unfinished, and optional Reward Model components.

The evidence implementation uses up to three turns per generation. If the task needs longer tool chains, treat that as an architectural change rather than merely a data change.

## Agentic mock tools

The training evidence includes these deterministic tool families:

| Tool | Required args | Reward validation use |
|---|---|---|
| `calculate_math` | `expression` | Compute arithmetic and check numeric `gt`. |
| `unit_converter` | `value`, `from_unit`, `to_unit` | Unit conversion tasks. |
| `get_current_weather` | `location` | Weather lookup tasks with fixed mock data. |
| `get_current_time` | optional `timezone` | Time lookup tasks with fixed mock values. |
| `get_exchange_rate` | `from_currency`, `to_currency` | Currency lookup tasks with fixed rates. |
| `translate_text` | `text`, `target_language` | Translation lookup tasks with fixed pairs. |

The final tool-call evaluation evidence also uses `random_number` and `text_length`. Keep tool-set differences explicit when moving from Agentic training to inference evaluation.

## Tool-call parsing and validation

Generated tool-call text must be valid JSON inside complete tags:

```text
<tool_call>{"name":"calculate_math","arguments":{"expression":"71**2"}}</tool_call>
```

Validation logic distilled from evidence:

- Ignore malformed JSON calls for execution, but penalize mismatched tag counts.
- Accept `arguments` as either an object or a JSON string that parses to an object.
- Reject tool names that are not in the current sample's tool list.
- Run a tool-specific argument check before counting a call as valid.
- Clip very large tool observations before they inflate context length.

Use the smoke helper to exercise this behavior without a model:

```bash
python scripts/reward_toolcall_smoke.py \
  --text '<tool_call>{"name":"calculate_math","arguments":{"expression":"71**2"}}</tool_call> The answer is 5041.' \
  --gt '["5041"]'
```

## Ground-truth validation

Agentic `gt` matching checks whether each scalar target appears in the final text, either by case-insensitive string inclusion or numeric comparison after removing commas. Numeric tolerance is about exact float equality at `1e-6` scale.

Good `gt` examples:

```json
["9472"]
[5041]
["Hello World"]
```

Avoid ambiguous `gt` entries:

```json
[{"answer": 9472}]
["9"]
```

The first is nested and not directly matched. The second can be too broad if many numbers appear in the final answer.

## Response masks and context packing

Agentic RL needs to train only on generated assistant tokens while preserving tool observations in context:

- Initial prompt tokens have mask `0`.
- Generated assistant tokens have mask `1`.
- Tool observation tokens appended to context have mask `0`.
- If the packed sequence exceeds `max_total_len`, the evidence keeps the tail of `ids`, masks, and old log-probs.
- The first `1` in the mask becomes the prompt/completion boundary for logging.
- EOS-aware completion masks stop loss after the first EOS token.

Failure signal: if response masks are all zeros after packing, the policy receives no gradient for that sample. This can happen with very short generations, malformed tokenizer output, over-aggressive truncation, or context packing bugs.

## Debug signals to monitor

| Route | Signals | Meaning |
|---|---|---|
| PPO | reward, KL_ref, approximate KL, clip fraction, Critic loss, average response length | High KL or clip fraction means updates are too aggressive; Critic loss instability slows learning. |
| GRPO/CISPO | reward, KL_ref, advantage mean/std, group reward std, average response length | Low group std means degenerate groups; rising KL means stronger drift from reference. |
| Agentic RL | context/completion debug prints, `gt`, reward, prompt length, packed sequence length, average length | Use to catch context misalignment, invalid tools, `gt` mismatch, or response-mask bugs. |
| Distillation | CE, distill KL, aux loss, learning rate | Balance `alpha`, temperature, and MoE aux behavior. |
| DPO | DPO loss, aux loss, learning rate | Exploding loss can indicate schema, beta, or pair-quality problems. |

## Capability trade-off note

Agentic and RLAIF routes optimize a narrow reward definition. MiniMind evidence showed Agentic weights can improve lightweight tool-use tasks while degrading factual/general Q&A stability. Always state which reward target is being optimized and route broad quality evaluation to `inference-serving` after training.

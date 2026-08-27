# RLHF And GRPO

This reference covers public `torchtune.rlhf` utilities, loss wiring caveats, and the boundary around experimental GRPO/async RL code. Use it with [data-and-datasets](../../data-and-datasets/SKILL.md) for preference row schemas and [post-training-recipes](../../post-training-recipes/SKILL.md) for DPO/PPO/GRPO recipe selection.

## Public RLHF Utilities

The stable public import surface is `torchtune.rlhf`. It exports sequence/log-prob utilities, reward/advantage helpers, and dataclasses used by recipe code.

Public sequence helpers:

```python
truncate_sequence_at_first_stop_token(sequences, stop_tokens, fill_value=0)
truncate_sequence_for_logprobs(query_response_logits, context_length)
logits_to_logprobs(logits, sequences, temperature=1.0)
batched_logits_to_logprobs(logits, sequences, temperature=1.0, chunk_size=4)
get_batch_log_probs(logits, labels, label_pad_token_id=-100, return_average_logprobs=False)
```

Public reward and statistics helpers:

```python
get_reward_penalty_mask(padding_masks, seq_lens, penalise_no_eos=True, min_response_length=None)
get_rewards_ppo(scores, logprobs, ref_logprobs, kl_coeff, valid_score_idxs=None)
masked_mean(x, mask, dim=None)
masked_sum(x, mask, dim=None)
masked_var(centered_values, mask, unbiased=True)
whiten(x, mask=None, shift_mean=True)
estimate_advantages(values, rewards, gamma, lmbda, masks=None)
```

Public dataclasses and types currently exported:

```python
PPOStats
Trajectory
ChosenRejectedOutputs
```

Use these through `import torchtune.rlhf as rlhf` or direct imports from `torchtune.rlhf`; avoid relying on private module paths unless source debugging requires it.

## Sequence And Log-Probability Utilities

`truncate_sequence_at_first_stop_token` accepts a tensor shaped `[batch, sequence]` and a tensor of stop token ids. It returns `(padding_mask, sequences)`, where the mask is `True` for positions truncated after the first stop token and the sequence has those positions replaced by `fill_value`. The implementation mutates the passed `sequences` tensor, so clone the input first if the original tokens are needed later.

`truncate_sequence_for_logprobs(query_response_logits, context_length)` slices logits for response-token log-prob estimation in a concatenated query+response sequence. It returns `query_response_logits[:, context_length - 1 : -1]`, matching next-token prediction alignment for response tokens.

`logits_to_logprobs` gathers log probabilities for a batch of target token ids from logits of shape `[batch, response_length, vocab_size]`. `batched_logits_to_logprobs` computes the same result in chunks over the batch dimension to reduce peak memory. Use `chunk_size` when vocabulary logits are large.

`get_batch_log_probs` expects `logits.shape[:-1] == labels.shape`, shifts logits/labels for next-token scoring, ignores labels equal to `label_pad_token_id`, and returns one scalar per batch item. Set `return_average_logprobs=True` for sequence-length-normalized preference scores; keep the default for summed log probabilities.

## PPO Reward Utilities

`get_reward_penalty_mask` identifies sequences whose reward score should be penalized. It assumes sequences have already been truncated and padded. With `penalise_no_eos=True`, sequences with no padding after an EOS are penalized. With `min_response_length`, responses shorter than that length are also penalized.

`get_rewards_ppo` combines reward-model scores with per-token KL penalties:

```python
total_reward, kl, kl_reward = get_rewards_ppo(
    scores,
    logprobs,
    ref_logprobs,
    kl_coeff,
    valid_score_idxs=None,
)
```

If `valid_score_idxs` is omitted, the reward model score is added to the last response position. When response padding is present, pass the index of the last valid score token per batch item.

`estimate_advantages(values, rewards, gamma, lmbda, masks=None)` implements generalized advantage estimation and returns `(advantages, returns)`. With a mask, advantages are whitened over valid positions and invalid positions are set to zero.

## DPO And PPO Losses

The source defines these losses:

```python
DPOLoss(beta=0.1, label_smoothing=0.0)
RSOLoss(gamma=0.1)
PPOLoss(epsilon=0.1, value_clip_range=0.2, value_coeff=0.1)
```

In current source, `torchtune.rlhf.loss.dpo` references `TypeVar`, `dataclass`, `Optional`, and `Tuple` without importing them. In an environment where top-level torchtune imports otherwise succeed, importing `torchtune.rlhf.loss` or `torchtune.rlhf.loss.dpo` can fail with `NameError` at import time. Treat this as a current-code gap to report during verification or refresh. Until fixed, route agents to the public `torchtune.rlhf` utility functions and existing recipe/config behavior instead of asking them to instantiate `DPOLoss` interactively from the broken loss module.

If a config references `torchtune.rlhf.loss.DPOLoss`, use `tune validate` or a controlled recipe smoke only after checking the current environment with `scripts/check_training_runtime.py`. Do not patch installed package code inside a user's environment unless the user explicitly asks for a local repair.

## DPO Workflow Boundaries

DPO requires paired preference data and a policy/reference relationship:

- Dataset rows must produce chosen/rejected conversations; route schema work to `data-and-datasets`.
- The policy checkpointer and reference checkpointer must intentionally point to the desired models.
- `get_batch_log_probs` is the utility pattern for chosen/rejected log probability aggregation.
- `DPOLoss` compares chosen-vs-rejected policy log ratios against chosen-vs-rejected reference log ratios.

Do not use SFT/chat-only data with DPO recipes unless it has been transformed into paired chosen/rejected rows.

## PPO Workflow Boundaries

PPO uses policy, value, reward, and reference components. The utility flow is:

1. Generate or collect query+response sequences.
2. Truncate at stop tokens and build valid-token masks.
3. Compute policy and reference log probabilities.
4. Compute reward-model scores and optional no-EOS/short-response penalties.
5. Combine scores and KL penalties with `get_rewards_ppo`.
6. Estimate advantages/returns with `estimate_advantages`.
7. Feed tensors to `PPOLoss` through the recipe code path.

PPO checkpoint configs often include multiple checkpointers. Debug all of them, not just the primary `checkpointer` field.

## Experimental GRPO

Current source includes experimental GRPO modules under `torchtune.dev.grpo` and newer async RL code under `torchtune.dev.rl`. The repository explicitly states `torchtune/dev` houses bleeding-edge APIs with less stringent testing/documentation/stability, and these APIs are not public or backward-compatible.

Useful current source signatures:

```python
# torchtune.dev.grpo.loss
GRPOLoss(epsilon=0.1, kl_coeff=0.1)
GRPOCompletionLoss(epsilon=0.1, kl_coeff=0.1)
GRPOSimpleLoss(epsilon=0.1, kl_coeff=0.1)
GRPOWithChunkedOutputLoss(num_output_chunks=8, epsilon=0.1, kl_coeff=0.1)

# torchtune.dev.grpo.rewards
extract_tags(text)
shaped_correctness_reward(answer, completion)
batch_shaped_correctness_reward(tokenizer, completions, answers)

# torchtune.dev.rl.linear_grpo_loss
LinearGRPOLoss(num_output_chunks=8, epsilon=0.1, kl_coeff=0.1, ignore_index=-100, mask_pre_projection=True)
```

Treat these as source-evidence aids for debugging or explaining current dev recipes, not as stable public APIs to build long-lived integrations on.

## Async GRPO Boundary

The async GRPO recipe is a prototype that overlaps generation and training. The architecture uses Ray workers, vLLM generation, a replay buffer, a parameter server for weight sync, post-processing workers, metric logging, and trainer workers. The docs describe it as early-stage and subject to breaking changes.

Operational constraints to surface before any execution:

- Requires installing async RL extras and packages such as Ray, vLLM, TorchRL/TensorDict family dependencies, W&B for the documented logging path, and a compatible torch/torchao stack.
- The documented example targets Qwen 2.5 3B and reports successful use on multi-H100 hardware; smaller or different hardware may need batch-size and memory reductions.
- vLLM parameter-server support is currently limited in the source comments and should be treated as a constraint when scaling.
- The recipe may start Ray processes, allocate GPUs, use network resources, and log externally; do not run it without explicit approval.
- Registry recipes under `dev/` should still be launched through `tune run` and inspected with `tune ls`/`tune cat`; do not import `recipes` as a package.

## Troubleshooting Example: DPOLoss Import Failure

If a future agent sees a failure while validating DPO configs or importing losses:

1. Run `python scripts/check_training_runtime.py` from this sub-skill directory.
2. Check whether `torchtune` and `torchtune.rlhf` import but `torchtune.rlhf.loss` fails.
3. If the loss error mentions missing `TypeVar`, `dataclass`, `Optional`, or `Tuple`, record it as the current source gap in `torchtune.rlhf.loss.dpo`.
4. Continue analysis with public `torchtune.rlhf` helpers, recipe configs, and tests rather than claiming all RLHF is unavailable.
5. Ask the user before editing package source or installing a patched wheel.

## Synthetic Hard Cases

- A DPO config validation fails because importing `torchtune.rlhf.loss` raises a `NameError` from `dpo.py`; the agent must identify the current-code import bug, avoid blaming dataset schema, and route to public RLHF utilities/source evidence until the repo is refreshed.
- A user asks to run async GRPO on a single workstation without Ray/vLLM/async extras; the agent should inspect the registry/config, run the safe preflight, summarize missing optional packages/hardware constraints, and refuse to start Ray/vLLM without approval.

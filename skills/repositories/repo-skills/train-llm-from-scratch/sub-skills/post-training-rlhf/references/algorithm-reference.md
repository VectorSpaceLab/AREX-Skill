# Post-Training Algorithm Reference

This reference captures the repo-specific alignment algorithms without requiring source-code lookup. Function names below identify the repo APIs that implement each idea.

## Shared model and checkpoint assumptions

- All stages reuse the same decoder-only `Transformer` backbone dimensions: `vocab_size`, `context_length`, `n_embed`, `n_head`, and `n_blocks` must match the checkpoint being loaded.
- Post-training heads wrap the backbone rather than replacing it:
  - `RewardModel(transformer)` adds a scalar reward head and reads a sequence reward from the last real token.
  - `TransformerWithValueHead(transformer)` adds a per-token value head and returns `(logits, values)` for PPO.
- Stage checkpoints use `model_state_dict` plus stage metadata. DDP prefixes may appear as `module.` and are stripped by loading helpers.
- Auxiliary reward/value head weights should not be loaded into a bare Transformer unless the stage specifically expects that wrapper.

## SFT: masked next-token cross-entropy

Core API:

```python
sft_loss(logits, tokens, loss_mask) -> Tensor
```

Mechanics:

1. Shift logits and targets exactly like base pretraining: `logits[:, :-1]` predicts `tokens[:, 1:]`.
2. Shift `loss_mask` the same way and multiply token cross-entropy by that mask.
3. Average only over masked assistant tokens: `loss = masked_ce.sum() / mask.sum().clamp(min=1)`.
4. Compute cross-entropy with `logits.float()` so bf16 training does not degrade the loss calculation.

Inputs:

- Base/pretrained checkpoint.
- Packed SFT HDF5 with `tokens` and `loss_mask` arrays of the same shape.
- The mask must be `1` on assistant response tokens, including the assistant end-of-turn token, and `0` on prompt/user/system tokens and padding.

Outputs and metrics:

- Output checkpoint: SFT policy checkpoint.
- `train_loss`, `ppl`, `dev_loss`, `dev_ppl` are masked assistant-token CE/perplexity.
- A falling train loss with flat or rising dev loss usually means overfit or data split mismatch; an unchanged loss often means an empty or shifted mask.

## Reward model: Bradley-Terry preference scoring

Core APIs:

```python
RewardModel(transformer)
bradley_terry_loss(chosen_rewards, rejected_rewards) -> Tensor
preference_accuracy(chosen_rewards, rejected_rewards) -> Tensor
reward_margin(chosen_rewards, rejected_rewards) -> Tensor
```

Mechanics:

1. Load the SFT backbone and attach a bias-free linear scalar reward head initialized near zero.
2. Concatenate chosen and rejected rows into one forward pass for efficiency.
3. Read reward at each row's last real token using `seq_lengths`; right padding is safe because attention is causal.
4. Optimize `-logsigmoid(r_chosen - r_rejected)`.

Inputs:

- SFT checkpoint.
- Preference JSONL rows containing `prompt`, `chosen`, and `rejected` strings.

Outputs and metrics:

- Output checkpoint: reward model checkpoint containing backbone plus reward head.
- `loss` starts near `0.693` at chance.
- `train_acc`/`test_acc` are preference accuracy; noisy human preference data may plateau well below perfect accuracy.
- `margin = mean(r_chosen - r_rejected)` should become positive and remain finite.

## DPO / ORPO / KTO: preference objectives

Core APIs:

```python
sequence_logprobs(model, sequences, response_mask, temperature=1.0, requires_grad=True) -> (sum_logp, n_tokens)
dpo_loss(policy_chosen_logps, policy_rejected_logps, ref_chosen_logps, ref_rejected_logps, beta=0.1)
orpo_loss(policy_chosen_logps, policy_rejected_logps, chosen_n_tokens, rejected_n_tokens, orpo_lambda=1.0)
kto_loss(policy_chosen_logps, policy_rejected_logps, ref_chosen_logps, ref_rejected_logps, beta=0.1, desirable_weight=1.0, undesirable_weight=1.0)
implicit_accuracy(chosen_reward, rejected_reward) -> Tensor
```

DPO mechanics:

- Policy and frozen reference both start from SFT.
- Compare the chosen-vs-rejected log-ratio under the trainable policy against the same log-ratio under the frozen reference.
- `beta` scales how aggressively the policy is pushed away from the reference. This repo defaults to a gentle value because over-pushing can degrade behavior.

ORPO mechanics:

- Reference-free mode selected with `loss_type=orpo`.
- Uses per-token mean log-probs, an SFT-like NLL term on the chosen response, and an odds-ratio preference term weighted by `orpo_lambda`.
- Useful when you want a single reference-free preference stage or want to fold instruction retention into the preference update.

KTO mechanics:

- Uses chosen examples as desirable and rejected examples as undesirable with a detached reference-KL baseline estimated from the batch.
- Useful for desirable/undesirable signals; this repo trains it from paired rows by assigning chosen/rejected labels.

Inputs/outputs/metrics:

- Input: SFT checkpoint and preference JSONL.
- Output: aligned policy checkpoint, usually named by the loss path.
- Metrics: `loss`, implicit preference `acc`, `r_chosen`, `r_rejected`, test margin, and downstream GSM8K when evaluated.
- A healthy run raises implicit accuracy above chance without large reward/log-prob magnitudes or downstream collapse.

## PPO: value-head RLHF with GAE, clipping, and KL control

Core APIs:

```python
TransformerWithValueHead(transformer)
generate_with_logprobs(model, prompt_ids, max_new_tokens, temperature=1.0, top_k=None, top_p=None, ...)
compute_logprobs(model, sequences, response_mask, temperature=1.0, requires_grad=True) -> (logp, mask)
compute_gae(rewards, values, values_next, resp_mask, gamma=1.0, lam=0.95) -> (advantages, returns)
whiten(advantages, mask) -> Tensor
ppo_policy_loss(new_logp, old_logp, advantages, mask, clip=0.2) -> (loss, clip_fraction)
ppo_value_loss(new_values, old_values, returns, mask, vf_clip=0.2) -> Tensor
approx_kl(new_logp, old_logp, mask) -> Tensor
```

Loop:

1. Load SFT into the actor backbone and make a frozen SFT reference.
2. Wrap the actor with `TransformerWithValueHead` for per-token values.
3. Roll out responses to prompt rows with `rollout_prompts`/`generate_with_logprobs`.
4. Score each response with either:
   - a programmatic verifier reward, typically GSM8K correctness plus bounded format bonus; or
   - the trained reward model when `reward_source=rm`.
5. Recompute old-policy and reference log-probs in teacher-forced mode.
6. Build per-token rewards: KL penalty on every response token plus the scalar task reward on the final response token.
7. Compute GAE in the action frame, whiten advantages over response tokens, then run clipped PPO epochs.

Metrics:

- `reward`: task reward per iteration; should trend upward over many iterations.
- `KL_ref`: policy drift from the frozen SFT reference; must stay bounded.
- `clipfrac`: fraction of response tokens clipped by PPO; sustained very high values mean updates are too large.
- `value_loss`: critic regression error; high or exploding values indicate poor returns, too-large LR, or reward scale issues.
- `resp_len`: generated response length; sudden cap-hitting or collapse indicates context/reward problems.

## GRPO / RLVR: group-relative verifier optimization

Core APIs:

```python
group_advantages(rewards, group_size, eps=1e-4) -> Tensor
k3_kl(new_logp, ref_logp) -> Tensor
grpo_loss(new_logp, old_logp, ref_logp, advantages, resp_mask, clip=0.2, kl_coef=0.04) -> (loss, stats)
```

Mechanics:

1. Load the SFT policy and make a frozen reference.
2. For each prompt, sample a group of `G` responses laid out contiguously.
3. Score each response with a verifiable reward.
4. Compute each response advantage as `(reward - group_mean) / (group_std + eps)` within that prompt's group.
5. Apply a token-level clipped surrogate and subtract a non-negative k3 KL penalty to the reference.
6. No critic/value head is used; groups with identical rewards produce near-zero advantages and therefore little or no gradient.

Metrics:

- `reward`: mean verifier reward across sampled completions.
- `informative` or `informative_groups`: fraction of groups with non-zero reward spread.
- `KL`: k3 KL to the reference; keep bounded.
- `clipfrac`: GRPO update size health metric.
- `resp_len`: response length.

## Rollout, masks, and log-prob invariants

- `response_mask` marks generated response tokens only; prompt tokens are never trained by RL losses.
- `compute_logprobs` returns tensors in the shifted action frame `(B, T-1)` and aligns the shifted response mask to targets `tokens[:, 1:]`.
- `sequence_logprobs` sums only response-token log-probs and also returns token counts for per-token means.
- Sampling records log-probs under the full distribution at the sampling temperature; top-k/top-p filtering affects sampling, not the recomputed full-distribution policy ratio.
- Log-probs are computed in fp32 even under bf16 autocast because DPO/PPO/GRPO subtract log-probs.
- Learned absolute positions cap `prompt_len + max_new_tokens <= context_length`; rollout utilities clamp or fail when no generation room remains.

## Verifier reward and answer parsing

- The GSM8K/verifier reward is correctness-dominant: exact numeric match within tolerance earns the main reward; a small bounded format bonus rewards exactly one well-formed `<answer>...</answer>` block.
- Parsing prefers a number inside `<answer>`, then a `#### number` pattern, then the last number in free text.
- Reward hacking risk increases when format bonus dominates correctness, when generation length is unconstrained, or when prompts do not match the SFT chat format.

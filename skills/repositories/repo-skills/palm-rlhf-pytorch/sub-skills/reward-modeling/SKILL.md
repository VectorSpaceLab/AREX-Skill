---
name: reward-modeling
description: "Work with RewardModel and ImplicitPRM workflows in
  palm-rlhf-pytorch, including masks, labels, and tiny reward smoke tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Reward Modeling

Use this sub-skill when a task is about scoring sequences, training rewards, or deriving implicit process rewards from a PaLM backbone.

## Route Here For

- Building or inspecting `RewardModel` for scalar or binned rewards.
- Using `prompt_mask` or `prompt_lengths` correctly, with the reminder that they are mutually exclusive.
- Training a reward model with labels and checking the inference path that returns either logits or sampled bin ids.
- Using `ImplicitPRM` for dense token-level rewards that compare a model against a frozen reference model.
- Running the tiny smoke checks in `scripts/tiny_reward_smoke.py` and `scripts/tiny_implicit_prm_smoke.py`.

## Do Not Use This For

- Base transformer sizing, generation, or LoRA scope mechanics that belong to `palm-modeling`.
- PPO, GRPO, TPO, or FlowRL trainer selection and training loops that belong to `policy-optimization`.
- Full-scale reward datasets or benchmark training. This sub-skill covers the package mechanics and safe smoke checks, not long runs.

## Start Here

1. Read [`references/api-reference.md`](references/api-reference.md) for the verified constructor and forward signatures.
2. Read [`references/workflows.md`](references/workflows.md) for the scalar reward and implicit process reward recipes.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) for mask conflicts, binned-vs-logit inference, and shape issues.
4. Run the tiny helper that matches your need:

```bash
python sub-skills/reward-modeling/scripts/tiny_reward_smoke.py --device auto
python sub-skills/reward-modeling/scripts/tiny_implicit_prm_smoke.py --device auto
```

If you are already in this sub-skill directory, use the local `scripts/` path instead.

## Operating Notes

- `RewardModel` deep-copies the supplied `PaLM` and can add a named reward LoRA scope.
- For inference, remember that a binned reward model samples bin ids by default unless `sample_from_bins=False` is passed.
- Use labels shaped to the pooled reward output: floats for scalar MSE and integer class ids for binned cross entropy.
- `ImplicitPRM` predicts token-level rewards from the log-prob gap between a trainable model and a frozen reference model.
- Prompt and response embeddings are injected before the copied backbone; the pooling mask is separate from the prompt indicator.

## Common Prompt Patterns

- "Train a scalar reward model" → use `RewardModel(..., num_binned_output=0)`.
- "Need reward logits instead of sampled bins" → set `sample_from_bins=False`.
- "Use prompt lengths or a mask" → pick exactly one prompt indicator style and keep the labels compatible.
- "Need step-by-step dense rewards" → use `ImplicitPRM` and expect the shifted output length.
- "Why is the output one token shorter?" → because the process reward compares source and target tokens after shifting.

## Quick Decision Points

- If the task is about a single score per sequence, start with scalar `RewardModel`.
- If the task is about bins or ratings, use binned `RewardModel` and choose whether you want logits or sampled ids.
- If the task is about dense process signals, use `ImplicitPRM`.
- If the task is about prompt/response semantics, inspect the prompt mask and pooled mask separately.
- If the task is about a downstream trainer, route there after the reward model is settled.

## Tiny Verification Checklist

A correct tiny check should:

- construct a tiny PaLM backbone;
- run scalar reward training with `labels` and a prompt indicator;
- run binned reward training or logits inference;
- confirm whether binned inference returns logits or sampled class ids;
- run an ImplicitPRM backward pass;
- confirm the dense reward output shape is `(batch, seq_len - 1)`.

## Related Files

- `references/api-reference.md` for verified signatures and output shapes.
- `references/workflows.md` for scalar, binned, and implicit-process workflows.
- `references/troubleshooting.md` for prompt-mask, shape, and inference issues.
- `scripts/tiny_reward_smoke.py` and `scripts/tiny_implicit_prm_smoke.py` for safe runnable smoke checks.

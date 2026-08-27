---
name: policy-optimization
description: "Guide PPO, GRPO, TPO, and FlowRL post-training loops for
  palm-rlhf-pytorch, including bounded RLHF smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Policy Optimization

Use this sub-skill when a task is about post-training a PaLM policy with the package trainers: PPO `RLHFTrainer`, `ActorCritic`, GRPO, TPO, or FlowRL.

## Route Here For

- Default PPO RLHF workflows that use the root exports `RLHFTrainer` and `ActorCritic`.
- Trainer selection questions: PPO vs GRPO vs TPO vs FlowRL.
- Bounded tiny smoke checks that verify trainer construction, prompt token id handling, and a single short training or generation step.
- Side-effect awareness for replay buffers, partition functions, and Accelerate-wrapped modules.

## Do Not Use This For

- Base PaLM construction, generation, or LoRA scope wiring; route those to `palm-modeling`.
- Reward training or implicit process reward workflows; route those to `reward-modeling`.
- Long training, benchmarks, or full RLHF scaling runs. This sub-skill covers mechanics and smoke checks, not expensive experiments.

## Start Here

1. For API facts, read [`references/api-reference.md`](references/api-reference.md).
2. For trainer choice, read [`references/trainer-selection.md`](references/trainer-selection.md).
3. For bounded recipes and the tiny smoke workflow, read [`references/workflows.md`](references/workflows.md).
4. For known failures and source footguns, read [`references/troubleshooting.md`](references/troubleshooting.md).
5. To verify the installed package, run the bundled helper instead of the source example script:

```bash
python sub-skills/policy-optimization/scripts/tiny_rlhf_smoke.py --device auto --train-smoke
```

If you only want a construction check first, add `--construct-only`.

## Operating Notes

- The root export `from palm_rlhf_pytorch import RLHFTrainer, ActorCritic` is the PPO path.
- GRPO, TPO, and FlowRL are module-qualified trainers and should be selected intentionally.
- Every trainer expects exactly one prompt input style: `prompts`, `prompts_path`, or `prompt_token_ids`.
- Raw text prompts require a tokenizer that returns padded token-id tensors.
- Keep smoke runs tiny. The source defaults are much larger than a verification check needs.
- `examples.py` is useful evidence, but it is not the preferred runtime path for this sub-skill because it depends on an undeclared `lion_pytorch` extra and uses expensive defaults.
- PPO updates actor and critic/value parameters; the newer trainer variants change the training state and storage pattern in different ways.

## Common Prompt Patterns

- "Which trainer should I use?" → start with `trainer-selection.md`.
- "Need a tiny RLHF smoke test" → use `scripts/tiny_rlhf_smoke.py` with `--construct-only` or `--train-smoke`.
- "Using raw prompts" → provide a tokenizer and confirm padding.
- "Need prompt-token-id wiring" → use the root PPO path first because it matches the README example shape.
- "Need a critic-free variant" → compare GRPO with TPO and FlowRL before choosing.

## Quick Decision Points

- If the request says "RLHF" without extra qualifiers, use the root PPO path first.
- If the request says "group-relative" or "critic-free", compare GRPO next.
- If the request says "target policy optimization" or mentions replay buffers, compare TPO.
- If the request says "flow balance" or "reward distribution matching", compare FlowRL.
- If the request only needs importability or a minimal construction check, use the bundled smoke helper with `--construct-only`.

## Tiny Verification Checklist

A correct tiny check should:

- build a tiny PaLM and scalar RewardModel;
- create `prompt_token_ids` as a padded integer tensor;
- instantiate the PPO trainer with tiny hyperparameters;
- optionally run one bounded update and one generate call;
- keep `max_norm=None` for the smoke path;
- avoid the source example's large defaults and extra dependency.

## Related Files

- `references/api-reference.md` for constructor signatures and method shapes.
- `references/trainer-selection.md` for PPO vs GRPO vs TPO vs FlowRL choice guidance.
- `references/workflows.md` for bounded recipes and smoke-script usage.
- `references/troubleshooting.md` for prompt assertions, replay-buffer side effects, and known source footguns.
- `scripts/tiny_rlhf_smoke.py` for the safe runnable PPO smoke check.

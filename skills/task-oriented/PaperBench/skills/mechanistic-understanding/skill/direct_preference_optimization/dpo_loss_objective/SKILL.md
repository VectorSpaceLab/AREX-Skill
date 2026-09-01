---
name: dpo_loss_objective
description: Compute Direct Preference Optimization logistic losses, implicit rewards, and log-ratio diagnostics from policy and reference log probabilities.
---

# DPO Loss Objective

Use this skill when implementing or checking the core DPO objective. It consumes chosen/rejected sequence log probabilities from a policy and a fixed reference model. Do not use this skill for data extraction, tokenization, or optimizer-loop bookkeeping.

## Inputs

- Policy log probabilities for chosen and rejected responses.
- Reference log probabilities for the same chosen and rejected responses.
- Positive `beta` temperature.
- Optional `label_smoothing`, `reference_free`, or `ipo` settings.

## Outputs

- Per-example DPO losses.
- Chosen and rejected implicit rewards.
- Policy log-ratios, reference log-ratios, and DPO logits.

## Workflow

1. Compute `policy_logratio = policy_chosen - policy_rejected`.
2. Compute `reference_logratio = reference_chosen - reference_rejected`, unless using reference-free mode.
3. Compute `logit = policy_logratio - reference_logratio`.
4. For standard DPO, return `-log sigmoid(beta * logit)`, optionally mixed with the flipped term for conservative label smoothing.
5. Return implicit rewards `beta * (policy_logp - reference_logp)` for diagnostics.

## Validation

Run:

```bash
python scripts/dpo_loss.py --self-test
python tests/test_dpo_loss.py
```

## Limitations

This standard-library implementation is intended for deterministic skill use and reduced recovery. Full tensor implementations should match these scalar formulas exactly.
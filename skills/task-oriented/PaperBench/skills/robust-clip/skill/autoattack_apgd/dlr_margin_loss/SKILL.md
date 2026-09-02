---
name: dlr_margin_loss
description: Compute DLR-style logit margin losses for APGD-DLR adversarial optimization checks.
---

# DLR Margin Loss

Use this skill when an adversarial attack needs the AutoAttack DLR loss or when validating that a proxy attack preserves APGD-DLR semantics. Do not use it for binary classifiers or tasks without ordered class logits.

## Inputs
- A logit vector with at least three classes.
- The true class index.

## Outputs
- Scalar untargeted DLR loss.
- Ranking diagnostics from the helper script.

## Workflow
1. Sort logits while retaining the true-class position.
2. Identify the strongest non-true competitor.
3. Normalize the true-versus-competitor margin by the spread between top and third logits.
4. Maximize this loss during untargeted APGD.

## Validation
Run `python tests/test_dlr.py` or the generated skill validator.

## Limitations
This pure-Python helper is intended for deterministic small examples and mirrors the untargeted loss needed by the recovery harness.

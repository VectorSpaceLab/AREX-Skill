---
name: adaptive_apgd_loop
description: Run a deterministic APGD-style projected attack with loss-history step adaptation and auditable traces.
---

# Adaptive APGD Loop

Use this skill to recover or test the APGD mechanism from AutoAttack when a bounded, deterministic implementation is needed. Do not treat this pure-Python finite-difference implementation as a high-throughput replacement for framework autograd attacks.

## Inputs
- Logit function accepting one vector.
- Examples and labels.
- Projection and loss helpers.
- Norm, epsilon, iterations, initial step size, and adaptation window.

## Outputs
- Adversarial examples and predictions.
- Per-example success flags.
- Loss trace and step-size adaptation events.

## Workflow
1. Start from the clean example or a deterministic offset inside the threat ball.
2. Estimate the loss gradient with finite differences.
3. Take an ascent step and project back to the threat model.
4. Track the best loss and adversarial point.
5. On non-improving windows, halve step size and continue from the best point.

## Validation
Run `python tests/test_apgd.py` or the skill-tree validator.

## Limitations
Finite differences are only for compact recovery evidence. Production use should substitute exact gradients while preserving the same adaptation and projection contracts.

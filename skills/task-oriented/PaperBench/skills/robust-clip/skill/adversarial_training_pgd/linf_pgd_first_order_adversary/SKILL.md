---
name: linf_pgd_first_order_adversary
description: Generate random-start l-infinity PGD adversarial examples with projection diagnostics for first-order robust optimization experiments.
---

# L-infinity PGD First-Order Adversary

## When To Use
Use this skill to implement or verify the inner maximization step in Madry-style adversarial training and evaluation. It is appropriate when the threat model is an l-infinity ball and the model exposes an input-loss gradient.

Do not use it for l2 attacks, decision-only attacks, or natural-only evaluation.

## Inputs
- Model object or callable that provides loss and input gradients.
- Examples and labels.
- `epsilon`, `step_size`, `steps`, `restarts`, input clip range, and random seed.

## Outputs
- Adversarial examples selected by highest final loss.
- Loss trajectory for each restart.
- Diagnostics showing maximum l-infinity perturbation and clip-range compliance.

## Workflow
1. Randomly initialize each restart inside the epsilon ball around each natural input.
2. Ascend the input loss by `step_size * sign(gradient)`.
3. Project to the intersection of the epsilon ball and the valid input range.
4. Keep the restart with the highest loss for each example.
5. Save trajectories and projection diagnostics when used in recovery.

## Validation
Run:

```bash
python scripts/linf_pgd.py --self-test
python tests/test_linf_pgd.py
```

## Limitations
This skill supplies the attack mechanism, not the outer training loop. It assumes gradients are available or analytically supplied by the model wrapper.

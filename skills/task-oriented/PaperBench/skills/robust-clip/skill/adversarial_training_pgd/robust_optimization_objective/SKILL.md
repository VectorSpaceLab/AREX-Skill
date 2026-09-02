---
name: robust_optimization_objective
description: Specify and validate the robust min-max objective used for PGD adversarial training from Madry et al. 2017.
---

# Robust Optimization Objective

## When To Use
Use this skill when a recovery or implementation needs to state whether an experiment matches the paper's robust optimization formulation: minimize model parameters against the worst-case loss in an allowed perturbation set.

Do not use it to label natural-only training, detector-only defenses, or attacks outside the declared threat set as robust training.

## Inputs
- Dataset identity and split.
- Loss name and task type.
- Threat model fields: `norm`, `epsilon`, and optional input clipping range.
- Inner maximization method, usually random-start PGD.
- Outer minimization method and optimizer evidence.
- Recovery scope: `full`, `reduced`, or `proxy`.

## Outputs
- Objective metadata JSON.
- Mechanism checks for inner maximization, l-infinity projection, adversarial loss measurement, and optimizer execution.

## Workflow
1. Write the robust objective as `min_theta E[max_delta L(theta, x + delta, y)]`.
2. Confirm that `delta` is constrained by the stated perturbation set.
3. Confirm that the experiment measures adversarial loss or adversarial accuracy.
4. For proxy recovery, explicitly state why it is reduced and which paper mechanisms it preserves.
5. Save the objective and mechanism checks alongside recovery artifacts.

## Validation
Run:

```bash
python scripts/objective_contract.py --self-test
python tests/test_objective_contract.py
```

## Limitations
This skill validates the objective contract. It does not implement PGD or train a model; pair it with the PGD adversary and training-loop skills.

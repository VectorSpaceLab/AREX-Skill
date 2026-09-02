---
name: axiom_recovery_evaluation
description: Evaluate Integrated Gradients experiments against completeness, sensitivity, implementation invariance, and symmetry axioms.
---

# Axiom Recovery Evaluation

Use this skill after attributions have been computed and a recovery run needs auditable metrics. Do not use it to compute attributions; it evaluates whether computed attributions preserve the paper's axiomatic mechanism.

## Inputs
- Attribution vector and `output_difference`.
- Completeness tolerance, using absolute error for small deterministic examples.
- Optional paired attribution vectors from equivalent implementations.
- Optional symmetric feature index groups.
- Optional sensitivity attribution for a single changed feature.

## Outputs
- Numeric completeness error.
- Boolean checks for completeness, sensitivity, implementation invariance, and symmetry.
- Overall `proxy_accepted` boolean when all supplied mechanism checks pass.

## Workflow
1. Compare attribution sum with the model output difference.
2. Mark Sensitivity(a) passed when a one-feature output change has nonzero attribution with the expected sign or magnitude.
3. Compare equivalent-implementation attributions within tolerance.
4. Check equal attributions for symmetric features with equal values.
5. Return a compact metric and mechanism-check dictionary for recovery artifacts.

## Validation
Run `python tests/test_axiom_evaluation.py` or the Distiller validator.

## Limitations
This skill validates the recovery mechanism. It does not prove visual saliency quality on ImageNet or replace a full benchmark when that runtime is available.

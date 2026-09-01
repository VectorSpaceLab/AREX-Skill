---
name: proxy_recovery_evaluator
description: Evaluate whether an SR3 soft-mode proxy recovery exercised conditioning, diffusion loss, optimizer update, and iterative refinement evidence.
---

# Proxy Recovery Evaluator

Use this skill at the end of an SR3 reduced recovery to assemble metrics and mechanism checks. Do not use it to override failing training traces or missing source-boundary evidence.

## Inputs
- Pair metadata from the conditional protocol.
- Training trace from the diffusion objective.
- Sampler trajectory from iterative refinement.
- Runtime blocker information.

## Outputs
- Numeric metrics such as loss decrease and final distance improvement.
- Mechanism booleans required for soft-mode proxy acceptance.

## Workflow
1. Confirm that the pair is explicitly marked proxy when no full dataset exists.
2. Confirm loss decreased and parameters changed.
3. Confirm the reverse trajectory has multiple refinement steps.
4. Keep full-runtime booleans false when full packages/models are unavailable.
5. Emit mechanism checks for recovery validation and analysis.

## Validation
Run `python tests/test_evaluator.py` or validate the skill tree with `--run-tests`.

## Limitations
Passing proxy checks supports mechanism-faithful reduced recovery only; it is not a claim of paper-level image metrics.

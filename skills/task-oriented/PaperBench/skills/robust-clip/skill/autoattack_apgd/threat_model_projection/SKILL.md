---
name: threat_model_projection
description: Project adversarial candidates into declared norm balls and valid input boxes for robustness evaluation.
---

# Threat Model Projection

Use this skill when implementing or auditing adversarial attacks that must stay within an `Linf` or `L2` perturbation budget. Do not use it to choose epsilon values or to evaluate model accuracy by itself.

## Inputs
- Clean vector or batch of vectors.
- Candidate adversarial vector or batch.
- Norm name: `Linf` or `L2`.
- Epsilon and input bounds.

## Outputs
- Projected adversarial vector.
- Diagnostics containing perturbation norms and clipping status.

## Workflow
1. Subtract clean inputs from candidates to obtain perturbations.
2. Project perturbations to the requested norm ball.
3. Add projected perturbations to clean inputs.
4. Clip to the valid input box.
5. Recompute diagnostics and assert invariants before using the result.

## Validation
Run `python tests/test_projection.py` or validate through the bundled skill-tree validator.

## Limitations
The script is pure Python for small deterministic recovery tests. Large tensor workloads should use a vectorized framework while preserving the same contracts.

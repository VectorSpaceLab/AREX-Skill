---
name: variational_objectives
description: Compute stable mass-covering variational objective diagnostics for SNVI-style posterior optimization.
---

# variational_objectives

Use this skill when a recovery or implementation needs the paper mechanism from *Variational Methods for Simulation-Based Inference* without reading the original repository. Do not use it as a full replacement for large-scale `sbi` or `sbibm` benchmark training when those runtimes are available.

## Inputs
- Numeric simulator, posterior, likelihood, or validity data matching the module contract.
- A bounded runtime where deterministic scripts can be executed.
- Optional random seed for reproducible proxy checks.

## Outputs
- JSON-serializable diagnostics from the module script.
- Numeric values that can be cross-checked by a recovery harness.
- Clear flags when the behavior is reduced or proxy-only.

## Workflow
1. Read the caller-provided data and keep source boundaries explicit.
2. Run the deterministic script in `scripts/` for the relevant SNVI component.
3. Check numeric invariants such as normalized weights, data accumulation, posterior movement, or validity correction.
4. Return diagnostics and preserve logs for downstream recovery validation.

## Validation
Run `python scripts/` only through the documented tests, or run `python -m pytest tests` when pytest is available. The Distiller validator command is `python <distiller>/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests`.

## Limitations
This skill captures reusable SNVI mechanisms. It does not claim to reproduce the paper's full C2ST benchmark curves or pyloric-network experiment unless paired with the required packages, simulators, and compute budget.

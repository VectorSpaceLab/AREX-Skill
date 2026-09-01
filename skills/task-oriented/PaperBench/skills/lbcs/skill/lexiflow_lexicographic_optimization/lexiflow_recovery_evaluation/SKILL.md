---
name: lexiflow_recovery_evaluation
description: Evaluate whether a recovery run exercised LexiFlow mechanisms and achieved a declared proxy or benchmark target with auditable metrics.
---

# LexiFlow Recovery Evaluation

Use this skill when implementing or auditing the LexiFlow paper mechanism for bounded recovery or reusable optimization tooling. Do not use it as a generic scalarized multi-objective optimizer; it assumes priority-ordered minimization objectives, optional goals, and non-negative tolerances.

## Inputs
- LexiFlow run trace
- Baseline run trace
- Module invocation records
- Declared paper or proxy target

## Outputs
- Numeric metrics including lexi_success_rate and second-objective gain
- Mechanism-check booleans
- Validation-ready recovery summary

## Workflow
1. Confirm objective values are ordered by priority and are minimization values.
2. Preserve the paper mechanism described in the module document rather than replacing it with weighted scalarization.
3. Run the companion script or import its pure functions for deterministic behavior.
4. Save command outputs, trace files, and metrics when the skill is used in a recovery experiment.

## Validation
Run `python scripts/lexiflow_recovery_evaluation.py --self-test` when available, then run the bundled test command through the Distiller skill-tree validator.

## Limitations
This generated skill is source-repository independent and derived from the paper text. Full HPO benchmark reproduction still requires real model training stacks and datasets; the included scripts are intended for deterministic mechanism validation and bounded proxy recovery.

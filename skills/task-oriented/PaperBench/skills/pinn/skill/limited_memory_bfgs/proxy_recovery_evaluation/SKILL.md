---
name: proxy_recovery_evaluation
description: Build validator-compatible soft-mode recovery metrics and mechanism checks for L-BFGS proxy experiments.
---

# Proxy Recovery Evaluation

Use this skill when full historical benchmark tables are unavailable but a reduced L-BFGS mechanism test is permitted. Do not use it to mask missing executable evidence, source-boundary violations, or target drift.

## Inputs
- L-BFGS trace and baseline trace from executable commands.
- `module_plan.json.fast_recovery_target`.
- Runtime handoff and source manifest.

## Outputs
- Ratio metric comparing final L-BFGS gradient norm with baseline gradient norm.
- Mechanism checks for bounded memory, two-loop direction use, scalar scaling, optimizer step, and baseline comparison.
- Recovery result fields compatible with the Paper2Skills validator.

## Workflow
1. Read the target metric and target threshold from the module plan.
2. Compute `lbfgs_final_gradient_norm / baseline_final_gradient_norm`.
3. Verify every claimed mechanism was logged by the recovery command.
4. Emit numeric metrics and explicit proxy notes.

## Validation
Run `python tests/test_proxy_recovery_evaluation.py`; the test verifies metric ratio and mechanism check completeness.

## Limitations
This skill evaluates a declared proxy only. It cannot claim reproduction of inaccessible historical benchmark tables.

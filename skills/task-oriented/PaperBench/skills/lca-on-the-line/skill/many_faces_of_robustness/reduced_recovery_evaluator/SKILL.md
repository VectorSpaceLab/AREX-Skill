---
name: reduced_recovery_evaluator
description: Assemble executable soft-mode proxy recovery results with metrics, traces, and mechanism checks.
---

# Reduced Recovery Evaluator

Use this skill after a bounded proxy experiment has run and needs to emit Distiller-compatible evidence. It is designed for soft-mode recovery where full paper reproduction is blocked by data or compute limits.

## Inputs
- Paper target metadata from `module_plan.json`.
- Numeric proxy metrics and command strings.
- Mechanism-check booleans, generated skill invocations, and training trace paths.

## Outputs
- A recovery result dictionary with `is_proxy`, numeric metrics, target metadata, commands, artifacts, and mechanism checks.
- Consistency checks for reduced training traces.

## Workflow
1. Copy the paper target from the module plan rather than inventing a new target.
2. Record proxy status and sample count explicitly.
3. Include mechanism checks for protocol validation, augmentation, comparison, loss reduction, and optimizer updates.
4. Verify that reduced optimizer claims are backed by changed parameters and loss values.

## Validation
Run `python tests/test_evaluator.py` or the Distiller skill validator.

## Limitations
This skill formats and checks recovery evidence. It does not by itself run the training experiment.

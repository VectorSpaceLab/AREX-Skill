---
name: reduced_recovery_harness
description: Execute a bounded soft-mode proxy experiment that validates P3O mechanisms with generated skills and numeric training evidence.
---

# Reduced Recovery Harness

Use this skill when full Atari or MuJoCo P3O training is blocked by runtime cost or missing benchmark packages, and soft mode permits a declared proxy. Do not report this proxy as a full paper reproduction.

## Inputs
- Attempt directory with `module_plan.json` and runtime handoff.
- Generated skill root containing ESS, surrogate-loss, and replay-protocol scripts.
- A tiny constructed on-policy and replay batch.

## Outputs
- `recovery/recovery_result.json` with numeric `loss_reduction`.
- `recovery/logs/generated_data_item.json` and `training_trace.json`.
- Command and generated-skill invocation logs.

## Workflow
1. Load the module-plan target so recovery metadata cannot drift.
2. Invoke the generated ESS scheduler on replay policy probabilities.
3. Invoke the generated replay protocol to preserve Algorithm 1 ordering.
4. Invoke the generated P3O loss component calculator before and after one optimizer step.
5. Record mechanism checks and validation-ready artifacts.

## Source Boundary
Use this skill with the paper, module documents, generated artifacts, and ordinary package documentation. Do not read or depend on the original P3O repository.

## Validation
Run `python scripts/<script>.py --self-test` or `python -m pytest tests` from the skill directory. The bundled tests use only the Python standard library.


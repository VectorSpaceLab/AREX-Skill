---
name: gedi_recovery_evaluation
description: Run and validate a bounded GeDi proxy recovery that invokes generated GeDi modules and records mechanism-faithful evidence.
---

# GeDi Recovery Evaluation

## When to use
Use this skill during recovery for the GeDi paper when full GPT2-XL/GeDi checkpoint experiments are blocked or too expensive and soft-mode proxy recovery is allowed.

## Inputs
- Attempt directory with `module_plan.json` and runtime handoff.
- Generated skill root containing posterior, decoding, training, and multi-class skills.
- Synthetic or real candidate set.

## Outputs
- Recovery result JSON with a numeric metric.
- Source manifest excluding the original repository.
- Generated skill invocation log.
- Mechanism checks for posterior, decoding, filtering, hybrid training, and multi-class control.

## Workflow
1. Read the module-plan target and runtime handoff.
2. Construct a small candidate set where base LM preference conflicts with desired class evidence.
3. Invoke the posterior skill for each candidate.
4. Invoke the decoding skill to reweight/filter/select a token.
5. Invoke the multi-class skill for a seen and zero-shot topic label.
6. Invoke the training skill to run a tiny optimizer step.
7. Compute mechanism pass rate and save artifacts.
8. Run the Distiller recovery validator.

## Validation
Run the recovery harness from the attempt directory, then run `validate_recovery_experiment.py`.

## Limitations
This is a reduced/proxy evaluation. It does not claim to reproduce human ratings or full GPT2-XL throughput.

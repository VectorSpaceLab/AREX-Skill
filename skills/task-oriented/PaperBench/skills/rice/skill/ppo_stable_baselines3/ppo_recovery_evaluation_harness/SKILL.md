---
name: ppo_recovery_evaluation_harness
description: Validate reduced PPO recovery evidence with mechanism checks, source-boundary checks, and pass-rate metrics.
---

# PPO Recovery Evaluation Harness

Use this skill when deciding whether a reduced PPO recovery run is mechanism-faithful enough for soft-mode acceptance. It should be called after the rollout, clipped surrogate, and update-loop skills have produced executable artifacts.

## Inputs

- A training trace containing loss values, parameter values, and mechanism booleans.
- A generated data item describing the rollout source.
- A module-plan fast recovery target.
- A source manifest and generated skill invocation records.

## Outputs

- `mechanism_pass_rate`: fraction of required PPO mechanism checks that pass.
- `passed`: boolean acceptance for the reduced proxy checks.
- `missing`: list of absent mechanism checks.

## Workflow

1. Require GAE execution, clipped surrogate execution, value loss execution, optimizer execution, and parameter change evidence.
2. Require the reduced run to be explicitly declared as proxy evidence.
3. Check that source manifests do not report forbidden original-repo sources.
4. Convert the check set into a numeric pass rate.
5. Return fields that can be embedded in `recovery_result.json`.

## Validation

Run `python tests/test_evaluation.py` from this skill directory. Tests include a complete positive case and a negative case with a missing optimizer step.

## Limitations

This skill evaluates recovery evidence; it does not run the PPO update itself and cannot turn a non-executable artifact into valid evidence.

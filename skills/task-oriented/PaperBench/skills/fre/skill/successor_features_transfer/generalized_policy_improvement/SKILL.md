---
name: generalized_policy_improvement
description: Build a transferred greedy policy by maximizing action values over a library of prior policies or successor-feature heads.
---

# Generalized Policy Improvement

Use this skill when several source policies or value heads are available and a new task should reuse them without retraining. It is especially useful with successor features, where each source policy can be reweighted for the new reward vector.

## Inputs

- Value tables shaped as `source_policy -> state -> action -> value`, or successor-feature tables plus reward weights converted to those values.
- Ordered states and actions.
- Optional deterministic tie-break rule.

## Outputs

- GPI action per state.
- Winning source policy per state/action decision.
- Diagnostics including value margins and number of source policies used.

## Workflow

1. Compute or load action values for each source policy under the current task.
2. For every state-action pair, take the maximum value across source policies.
3. Choose the action with the largest max-over-sources value.
4. Record which source supplied the winning value for the chosen action.
5. Keep the operation purely evaluative: do not update source policies or reward weights.

## Validation

Run:

```bash
python scripts/gpi.py --self-test
python tests/test_gpi.py
```

## Limitations

This utility assumes finite action sets and explicit value tables. For neural approximators, use it as a reference policy-selection contract around model outputs.

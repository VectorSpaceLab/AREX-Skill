---
name: gpi_action_selection
description: Select USFA transfer actions by generalized policy improvement over candidate policy encodings.
---

# GPI Action Selection

Use this skill when selecting actions for a new task `w` from conditioned successor features `psi(s,a,z)`. It preserves the candidate set `C` and reports the winning candidate for mechanism evidence.

## Inputs

- Target task weight `w`.
- Candidate encodings `C`.
- Action list.
- Successor-feature table for `(state, action, z)`.

## Outputs

- Selected action.
- Winning candidate encoding.
- Per-action and per-candidate score table.

## Workflow

1. For every action and candidate `z`, compute `psi(s,a,z)^T w`.
2. Keep the best candidate for each action.
3. Choose the action with the largest candidate-backed score.
4. Log the full score table so recovery can prove candidate search occurred.

## Validation

Run:

```bash
python tests/test_gpi.py
```

## Limitations

This skill does not estimate successor features. It requires a table or approximator supplied by upstream USFA components.

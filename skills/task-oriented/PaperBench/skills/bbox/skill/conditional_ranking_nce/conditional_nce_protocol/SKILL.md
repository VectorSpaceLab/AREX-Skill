---
name: conditional_nce_protocol
description: Build finite conditional NCE protocols with noise distributions, adjusted scores, and paper counterexample fixtures.
---

# Conditional NCE Protocol

Use this skill when a recovery or experiment needs the conditional NCE data protocol from Ma and Collins (2018): finite inputs, finite labels, a true conditional distribution, a strictly positive noise distribution, and candidate sets containing one observed label plus `K` independently sampled noise labels.

Do not use this skill to optimize the ranking or binary objectives; use it to construct and validate the inputs consumed by those estimators.

## Inputs

- A finite list of input ids.
- A finite list of label ids.
- `p_x`, a probability table over inputs.
- `p_y_given_x`, a nested probability table over labels for each input.
- `p_noise`, a strictly positive probability table over labels.
- `K >= 1`.
- Optional score parameters for the paper's two-by-two counterexample.

## Outputs

- A `ConditionalNCEProtocol` object.
- Population event enumerators for positive and negative labels.
- `bar_score(score, label) = score - log p_noise(label)`.
- A built-in Section 4.3 counterexample protocol with true conditional ratios and partition values.

## Workflow

1. Validate all probability tables before computing objectives.
2. Keep positive labels and sampled negative labels explicit. Repeated negatives are allowed because the paper samples them independently.
3. Use adjusted scores for both ranking and binary NCE:

```text
bar_s(x, y; theta) = s(x, y; theta) - log p_N(y)
```

4. For deterministic recovery, enumerate the exact population over `x`, the observed label, and all negative-label tuples rather than relying on Monte Carlo.

## Validation

Run:

```bash
python -m pytest tests
```

or validate through the Distiller skill tree checker:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py . --run-tests
```

The tests construct the paper's Section 4.3 counterexample and check normalizers, true ratios, adjusted scores, and population-event mass.

## Limitations

This skill intentionally handles finite, small protocols suitable for recovery and tests. It does not implement neural language-model data loading or full Penn Treebank preprocessing.

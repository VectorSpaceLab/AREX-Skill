---
name: autoattack_evaluation_protocol
description: Evaluate robust accuracy with a fixed sequential AutoAttack-style attack protocol and per-attack accounting.
---

# AutoAttack Evaluation Protocol

Use this skill when converting attack outputs into robust accuracy under a fixed attack sequence. Do not use it to tune attacks based on model-specific failures; the order and attack definitions should be declared before evaluation.

## Inputs
- Examples and labels.
- A logit function.
- Ordered attack callables that return adversarial examples for a subset.

## Outputs
- Robust accuracy.
- Remaining robust mask.
- Per-attack success counts and evaluated counts.

## Workflow
1. Mark examples that are clean-correct.
2. For each attack, pass only examples still robust.
3. Update the robust mask when adversarial predictions change the label.
4. Report final robust accuracy over all examples and per-attack accounting.

## Validation
Run `python tests/test_protocol.py` or use the generated skill validator.

## Limitations
This helper records the AutoAttack accounting pattern; it does not implement FAB or Square Attack internally.

---
name: masked_input_transformation
description: Use this skill when converting lower-dimensional target vectors into a frozen source model input space by zero-padding and applying a masked, trainable additive reprogramming pattern. It preserves target coordinates and exposes metadata for downstream training checks.
---

# masked_input_transformation

## When to use
Use this skill when converting lower-dimensional target vectors into a frozen source model input space by zero-padding and applying a masked, trainable additive reprogramming pattern. It preserves target coordinates and exposes metadata for downstream training checks.

Do not use this skill to fine-tune or inspect an original paper repository. It is for reusable model-reprogramming mechanisms derived from the paper.

## Inputs
- Small target-domain samples or source-output vectors.
- Declared source dimensions/classes and target dimensions/classes.
- Reprogramming parameters, masks, mappings, or training traces as appropriate.

## Outputs
- Deterministic transformed vectors, target probabilities, training traces, or mechanism-check dictionaries.
- Explicit metadata sufficient for downstream validation of source-model immutability and trainable-parameter scope.

## Workflow
1. Validate dimensional assumptions from the model-reprogramming paper: target input dimension no larger than source input dimension and target label count no larger than source label count when using label mapping.
2. Apply only the local transformation, mapping, training, or checking operation owned by this skill.
3. Record numeric outputs and do not mutate frozen source model parameters.
4. In recovery, save traces so the experiment gate can verify optimizer steps and mechanism checks.

## Validation
Run `python ../../../../Paper2Skills-Agent/src/packages/paper2skills-agent/src/paper2skills/skills/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests` from a suitable workspace, or directly run the tests in `tests/`.

## Limitations
These utilities are deliberately small and deterministic. They validate the mechanism, not full-scale ImageNet, speech, biomedical, or language-model experiments.

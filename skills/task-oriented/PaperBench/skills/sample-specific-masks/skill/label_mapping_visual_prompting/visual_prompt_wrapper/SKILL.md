---
name: visual_prompt_wrapper
description: Apply and audit universal visual prompts for frozen source-model adaptation experiments.
---

# Visual Prompt Wrapper

Use this skill when reproducing or adapting visual prompting/model reprogramming methods that keep a source model fixed and learn only an input prompt. Do not use it for methods that fine-tune source-model weights.

## Inputs
- Target examples as numeric feature vectors or tensors.
- A universal prompt vector/pattern, optionally with a binary mask.
- A frozen source model callable or serialized linear-source specification.

## Outputs
- Prompted inputs.
- Source logits or predictions.
- An audit record with fingerprints before and after inference.

## Workflow
1. Verify that the prompt shape matches the embedded source input shape.
2. If a mask is supplied, apply prompt values only where the mask is nonzero.
3. Run the source model and record logits/top-1 labels.
4. Compare source-model fingerprints before and after the call; source parameters must not change.
5. Pass logits/predictions to a label-mapping or ILM-VP optimizer skill.

## Validation
Run `python tests/test_visual_prompt_wrapper.py` or validate the skill tree with `validate_skill_tree.py --run-tests`.

## Limitations
This deterministic helper uses vector/tiny tensor abstractions for tests. Full image resizing and GPU model execution belong in the recovery harness.

---
name: visual_prompt_templates
description: Create and validate task-level pixel visual prompt templates for frozen vision model adaptation.
---

# Visual Prompt Templates

Use this skill when implementing the input-transformation half of visual prompting from the paper *Exploring Visual Prompts for Adapting Large-Scale Models*. It is appropriate when a frozen vision model should receive the same learned pixel pattern for every downstream image. Do not use it to create per-example adversarial examples or to update model weights.

## Inputs
- An image represented as a `C x H x W` nested list or array-like object.
- A prompt represented with the same shape or a compact border/patch specification.
- A template name: `padding`, `fixed_patch`, or `random_patch`.

## Outputs
- A prompted image with the same shape as the input.
- A mask describing which pixels were controlled by the prompt.

## Workflow
1. Resize and preprocess images before prompt application; this skill assumes the final model input shape.
2. Prefer `padding` for paper-faithful CLIP experiments. The paper uses padding size 30 as the default for 224x224 inputs, but reduced experiments may use smaller sizes.
3. Add prompt values only in the template region and leave the non-prompt image content unchanged.
4. Use one shared prompt for all examples in a downstream task.
5. Clamp values only when the downstream runtime requires bounded image ranges; keep unclamped values during pure optimization tests if that matches the proxy.

## Validation
Run `python tests/test_visual_prompt_templates.py` or validate the whole skill tree with the Paper2Skills `validate_skill_tree.py --run-tests` command.

## Limitations
This skill does not train the prompt and does not implement CLIP text-label scoring. Pair it with output-transformation and prompt-training skills.

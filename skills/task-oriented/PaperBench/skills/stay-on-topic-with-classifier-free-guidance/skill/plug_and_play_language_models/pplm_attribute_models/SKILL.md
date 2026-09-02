---
name: pplm_attribute_models
description: Use when a recovery or implementation needs differentiable PPLM attribute scores for BoW or simple discriminator-style control.
---

# PPLM Attribute Models

Use this skill to build the plug-in attribute model p(a|x) used by PPLM. Do not use it to modify base LM weights.

## Inputs
- Vocabulary tokens.
- Topic BoW terms or linear classifier weights.
- Candidate token probabilities or a hidden vector.

## Outputs
- Numeric attribute score.
- Attribute loss suitable for gradient ascent/descent in a controller.
- Diagnostics for missing BoW terms.

## Workflow
1. Normalize vocabulary and target words.
2. For BoW control, score the probability mass assigned to target words using `-log(sum p(target))` as a minimization loss.
3. For discriminator-style control, apply a linear score or softmax outside the base LM.
4. Return diagnostics; never update the base LM.

## Validation
Run `python tests/test_attribute_models.py`.

## Limitations
Reduced proxy implementations must declare that they are not full GPT-2 345M reproduction.

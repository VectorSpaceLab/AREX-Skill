---
name: pplm_attribute_objectives
description: Compute PPLM-style bag-of-words or linear-classifier attribute losses and gradients for controlled generation.
---

# PPLM Attribute Objectives

Use this skill when implementing or validating Plug and Play Language Model control objectives. It is appropriate when a fixed language model distribution must be steered toward a topic, sentiment, or toxicity-related attribute without changing model weights.

## Inputs
- `tokens`: vocabulary strings aligned with logits.
- `logits`: numeric next-token logits or a perturbable logit proxy.
- `target_words`: bag-of-words target tokens, or `classifier_weights` for a linear classifier proxy.

## Outputs
- Attribute loss where lower is better.
- Gradient over logits for minimization.
- Diagnostics including target probability mass.

## Workflow
1. Convert logits to a stable softmax distribution.
2. For bag-of-words control, sum probability mass assigned to target words.
3. Return `-log(target_mass)` as the loss and the analytic gradient with respect to logits.
4. Treat missing target words as an explicit contract error rather than silently succeeding.

## Validation
Run `python tests/test_attribute_objectives.py` from this skill directory, or validate through the Distiller skill-tree validator.

## Limitations
This deterministic helper validates the PPLM objective interface; it is not a full neural discriminator or GPT-2 forward pass.

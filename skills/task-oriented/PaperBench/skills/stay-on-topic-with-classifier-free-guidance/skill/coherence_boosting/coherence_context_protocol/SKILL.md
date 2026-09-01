---
name: coherence_context_protocol
description: Build and validate full-context and premise-free-context records for coherence boosting answer-selection experiments.
---

# Coherence Context Protocol

Use this skill when preparing multiple-choice or cloze examples for coherence boosting. It separates a long premise-bearing context from the premise-free prompt that captures answer-format or answer-prior effects.

## Inputs
- Examples with `premise`, `prompt`, `candidates`, and `label`.
- Optional metadata identifying dataset and split.

## Outputs
- Records with `full_context = premise + prompt`, `premise_free_context = prompt`, unchanged candidates, and label.
- Validation errors for missing fields, empty candidates, invalid labels, or leaked premise text in the premise-free context.

## Workflow
1. Normalize whitespace but do not rewrite candidate text.
2. Concatenate premise and prompt for the full context.
3. Keep the premise-free context free of the premise.
4. Validate candidate count and label bounds.
5. Pass records to scoring modules; this skill must not choose answers.

## Validation
Run `python tests/test_context_protocol.py` or validate through `validate_skill_tree.py --run-tests`.

## Limitations
This skill does not call a language model. It prepares the contexts whose likelihoods are later computed or supplied by a cache.

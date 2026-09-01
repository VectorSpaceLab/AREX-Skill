---
name: scienceqa_style_evaluation
description: Canonicalize option-only or short-form ScienceQA-style answers and compute deterministic accuracy.
---

# ScienceQA Style Evaluation

Use this skill when evaluating visual question-answering predictions whose labels are multiple-choice option letters or short spans. It is especially useful for LLaVA-style ScienceQA recovery, where answer formatting can otherwise dominate the metric.

## Inputs
- Prediction records with `id`, `raw_answer`, and `label`.
- Optional answer choices keyed by option letter.

## Outputs
A metrics object with accuracy and per-item canonicalized predictions.

## Workflow
1. Extract an explicit option letter when present.
2. Otherwise match the answer text against provided choices.
3. Normalize case and punctuation for short-span labels.
4. Compute accuracy and retain raw/extracted answers separately.

## Validation
Run the included tests or the skill-tree validator with tests enabled.

## Limitations
This evaluator is deterministic and local. It does not call GPT-4 for open-ended judging.

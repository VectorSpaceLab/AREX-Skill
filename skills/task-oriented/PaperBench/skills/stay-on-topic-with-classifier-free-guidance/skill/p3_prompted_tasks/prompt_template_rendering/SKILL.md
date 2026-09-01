---
name: prompt_template_rendering
description: Render structured dataset examples into PromptSource-style natural-language source and target pairs for prompted multitask recovery.
---

# Prompt Template Rendering

Use this skill when a recovery or implementation needs to convert structured NLP examples into the text-to-text prompted format used by T0/P3-style multitask training. Do not use it to choose train/evaluation splits or to score model outputs; those are separate contracts.

## Inputs
- JSON examples containing fields referenced by prompt templates.
- Template specifications with `dataset_id`, `template_id`, `input_format`, `target_field`, and optional `answer_choices`.

## Outputs
- Rendered records containing `dataset_id`, `task_family`, `example_id`, `template_id`, `source`, `target`, and `label`.

## Workflow
1. Validate that every placeholder in `input_format` exists in the raw example.
2. Format the source string with Python-style named placeholders.
3. Resolve the target from `target_field`; if `answer_choices` is supplied, map numeric or symbolic labels to target text.
4. Preserve metadata for downstream leakage checks and prompt robustness evaluation.

## Validation
Run `python tests/test_prompt_template_rendering.py` or validate the whole tree with the Distiller skill validator.

## Limitations
This skill implements deterministic rendering only; it does not provide the original PromptSource package or full dataset loading.

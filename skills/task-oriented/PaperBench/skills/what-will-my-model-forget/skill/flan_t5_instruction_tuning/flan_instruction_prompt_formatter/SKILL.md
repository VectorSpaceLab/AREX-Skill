---
name: flan_instruction_prompt_formatter
description: Render FLAN-style direct, few-shot, and chain-of-thought instruction prompt/completion pairs without leaking hidden answers into prompts.
---

# FLAN Instruction Prompt Formatter

Use this skill after mixture construction to format examples for instruction finetuning or held-out evaluation.

## Inputs

- Examples with `instruction`, `input`, `answer`, and optional `rationale`.
- Mode `direct`, `few_shot`, or `cot`.

## Outputs

- Prompt/completion records and metadata.

## Workflow

1. Build prompts from instruction and input fields.
2. Put target answers only in completions for query examples.
3. Put rationale plus final answer in CoT completions.
4. Record metadata for mechanism checks.

## Validation

Run `python tests/test_prompt_formatter.py`.

## Limitations

Uses compact deterministic templates rather than every original FLAN template.

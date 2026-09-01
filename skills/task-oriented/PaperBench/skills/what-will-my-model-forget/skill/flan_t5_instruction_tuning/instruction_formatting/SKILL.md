---
name: instruction_formatting
description: Render FLAN-style instruction examples with direct, exemplar, and chain-of-thought formatting controls.
---

# Instruction Formatting

Use this skill when building FLAN-style instruction-finetuning data, recovery fixtures, or tests that need prompt-target records. Do not use it to evaluate model outputs or to compose the full task mixture; it only formats individual examples.

## Inputs
- A task record with `instruction`, `input`, `answer`, `mode`, optional `rationale`, and optional `exemplars`.
- `mode` must be `direct` or `cot`.

## Outputs
- `prompt`: user-visible instruction prompt.
- `target`: supervised target text.
- `metadata`: mode, exemplar count, and chain-of-thought flag.

## Workflow
1. Validate required fields and mode.
2. Add exemplar blocks before the current input when provided.
3. Render direct targets as the concise answer only.
4. Render CoT targets as rationale plus `Final answer: ...`.
5. Keep rationales out of direct examples and out of prompts.

## Validation
Run `python tests/test_instruction_formatter.py` or validate the tree with `validate_skill_tree.py --run-tests`.

## Limitations
This skill does not choose task sampling weights and does not call a language model. It preserves the paper's formatting contract for downstream mixture, training, and proxy-evaluation modules.

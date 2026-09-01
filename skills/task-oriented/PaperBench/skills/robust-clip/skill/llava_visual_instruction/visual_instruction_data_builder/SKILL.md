---
name: visual_instruction_data_builder
description: Build LLaVA-style visual instruction records from captions and boxes for mechanism-faithful recovery experiments.
---

# Visual Instruction Data Builder

Use this skill when a task needs to convert symbolic image evidence into a multimodal instruction-following record in the style of Visual Instruction Tuning. Do not use it to hallucinate image content; every generated field must be grounded in supplied captions or boxes.

## Inputs
- `image_id`: stable identifier for the image or proxy image.
- `captions`: one or more natural-language captions.
- `boxes`: object records with `label` and normalized `bbox` coordinates.
- `response_type`: one of `conversation`, `detail`, or `reasoning`.
- Optional `question` and `answer` strings.

## Outputs
A JSON-compatible record with `human_prompt`, `assistant_answer`, `symbolic_context`, `response_type`, `is_resource_derived`, and `resource_files` when available.

## Workflow
1. Validate that captions and boxes are non-empty.
2. Summarize captions and object labels as the symbolic visual context that a language-only teacher could read.
3. Create a response-type-specific user instruction while keeping the assistant answer in a separate field.
4. Attach provenance so recovery can prove the item was derived from allowed evidence.

## Validation
Run `python tests/test_visual_instruction_data_builder.py` or validate the full skill tree with `validate_skill_tree.py --run-tests`.

## Limitations
This skill does not call GPT-4 or inspect pixels. It creates deterministic proxy records that preserve the paper's caption/box-to-instruction mechanism.

---
name: instruction_encoding_variants
description: Render Natural Instructions task records into paper-faithful instruction encoding variants for text-to-text models.
---

# Instruction Encoding Variants

Use this skill when a recovery harness needs the exact style of textual model input compared in the paper. Do not include the held-out reference answer for the current instance in the encoding.

## Inputs
- A normalized instruction task record.
- Current instance input text.
- Variant: `no_instruction`, `prompt`, `prompt_definition`, `positive_examples`, `prompt_definition_positive_examples`, or `full_instruction`.

## Outputs
- Encoded text ending with `output:`.
- Included field names for audit logs.

## Workflow
1. Choose the variant based on the ablation being tested.
2. Render selected fields in a stable order: definition, prompt, things to avoid, emphasis, examples, current input.
3. Label positive and negative examples explicitly.
4. Append only the current input and an empty output slot.
5. Pass the encoding to a model or reduced proxy scorer.

## Validation
Run `python tests/test_instruction_encoding_variants.py` or validate with `validate_skill_tree.py --run-tests`.

## Limitations
This skill does not truncate to BART’s maximum sequence length. Callers running full models must apply model-specific token limits.

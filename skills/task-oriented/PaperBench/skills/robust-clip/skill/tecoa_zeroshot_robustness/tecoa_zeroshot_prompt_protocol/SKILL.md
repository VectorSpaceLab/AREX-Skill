---
name: tecoa_zeroshot_prompt_protocol
description: Build deterministic CLIP-style zero-shot text prompts for TeCoA image-text adversarial robustness experiments.
---

# TeCoA Zero-Shot Prompt Protocol

Use this skill when a recovery or evaluation needs CLIP-style text prompts from class labels for zero-shot adversarial robustness. It preserves the paper's language-supervised contract: labels are represented as natural-language prompts that can be encoded as text embeddings, not as a new task-specific classifier head.

Do not use this skill to score predictions, create adversarial examples, or emit final answers. Its output is only prompt metadata consumed by contrastive and recovery modules.

## Inputs

- `labels`: ordered non-empty class labels.
- `template`: a prompt template with exactly one replacement field, for example `a photo of a {}`.
- Optional cleanup settings; the default strips whitespace, replaces underscores with spaces, and collapses repeated spaces.

## Outputs

- `prompts`: ordered prompt strings.
- `mapping`: ordered label/prompt pairs.
- `metadata`: template, count, and normalization rules.

## Workflow

1. Validate that labels are non-empty and the template has exactly one replacement field.
2. Normalize labels deterministically without changing class order.
3. Format each label into the template.
4. Save or return the prompt payload for text-embedding construction.
5. Check that downstream modules use the same ordering for target labels.

## Validation

Run `python tests/test_prompt_protocol.py` or validate the skill tree with `python <distiller>/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests`.

## Limitations

This skill does not tokenize prompts with CLIP, download models, or infer dataset-specific aliases unless the caller supplies the labels. It is safe for reduced recovery because it uses only standard-library logic.

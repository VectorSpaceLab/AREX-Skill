---
name: clip_pair_protocol
description: Build and validate CLIP-style image-text pair records and prompt templates for bounded recovery experiments.
---

# CLIP Pair Protocol

Use this skill when a recovery or evaluation task needs a compact representation of CLIP-style natural-language supervision. Do not use it to read the original CLIP repository during recovery.

## Inputs
- Class names as non-empty strings.
- Prompt templates containing `{}` placeholders.
- Pair records with `id`, `class_name`, `image_embedding`, and `text_embedding` fields.

## Outputs
- Validated pair records with consistent embedding dimensions.
- Rendered prompt strings for each class.
- JSON-serializable diagnostics describing rejected fields.

## Workflow
1. Validate that every class name and template is non-empty.
2. Render class prompts by substituting each class name into each template.
3. Validate pair records and ensure image/text embeddings are numeric vectors with matching dimensions.
4. Preserve provenance fields separately from labels so downstream classifiers do not invent supervision.

## Validation
Run `python tests/test_pair_protocol.py` or validate the tree with the Distiller skill validator.

## Limitations
This skill defines protocol and prompt construction only. It does not encode images or text with a pretrained CLIP model.

## Refinement Note
Refinement note: mismatched image/text embedding dimensions must fail fast and must not be padded or truncated.

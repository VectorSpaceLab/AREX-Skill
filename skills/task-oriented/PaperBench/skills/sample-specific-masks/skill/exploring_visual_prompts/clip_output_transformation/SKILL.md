---
name: clip_output_transformation
description: Build CLIP-style text label prompts and classify frozen image embeddings by cosine similarity.
---

# CLIP Output Transformation

Use this skill for the output-transformation or answer-engineering part of visual prompting with CLIP-like models. It maps downstream class labels into text prompts, computes image/text similarities, normalizes them, and selects labels. Do not use this skill as a learned classifier head; it should keep text features fixed except for normal feature normalization.

## Inputs
- Class labels such as `cat`, `truck`, or `three`.
- A text template, usually `This is a photo of a {label}`; dataset-specific templates are allowed when recorded.
- Frozen image embeddings and frozen text embeddings, or deterministic proxy vectors for tests.

## Outputs
- Prompt strings for every class.
- Cosine-similarity logits and softmax probabilities.
- Predicted class labels.

## Workflow
1. Construct one text prompt per downstream class.
2. Encode text prompts with the frozen text encoder, or provide proxy text vectors.
3. Encode prompted images with the frozen image encoder, or provide proxy image vectors.
4. Compute cosine similarities and a softmax distribution across classes.
5. Predict the highest-probability downstream label.

## Validation
The tests use deterministic vectors to check prompt construction, cosine logits, probability normalization, and argmax behavior.

## Limitations
This skill does not learn visual pixels. It should be cross-checked during recovery so the harness cannot silently replace CLIP scoring with unrelated logic.

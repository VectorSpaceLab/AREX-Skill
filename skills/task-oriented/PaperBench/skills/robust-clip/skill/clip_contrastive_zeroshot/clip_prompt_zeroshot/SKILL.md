---
name: clip_prompt_zeroshot
description: Build prompt-ensemble zero-shot classifiers from normalized image and text embeddings in the CLIP style.
---

# CLIP Prompt Zero-Shot

Use this skill when a task must classify image embeddings by comparing them with text embeddings of rendered class prompts. It preserves the paper's zero-shot transfer mechanism without requiring target-task supervised training.

## Inputs
- Image embeddings to classify.
- Class names and prompt templates.
- A deterministic prompt embedding mapping or model adapter.

## Outputs
- Class scores, probabilities, and top predictions.
- Prompt ensemble diagnostics showing which prompt vectors contributed to each class vector.

## Workflow
1. Render prompts from class names and templates.
2. Obtain or supply one embedding per rendered prompt.
3. Normalize prompt embeddings and average them per class, then normalize the class vector.
4. Compare normalized image embeddings to class text vectors and select the highest score.

## Validation
Run `python tests/test_prompt_zeroshot.py` or validate with the Distiller skill validator.

## Limitations
The skill does not download pretrained models. In reduced recovery, prompt embeddings may be deterministic fixtures if declared as proxy evidence.

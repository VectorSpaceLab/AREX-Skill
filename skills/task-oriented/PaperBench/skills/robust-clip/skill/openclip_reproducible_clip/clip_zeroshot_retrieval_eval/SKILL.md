---
name: clip_zeroshot_retrieval_eval
description: Evaluate CLIP-style zero-shot classification and cross-modal retrieval with normalized similarity rankings.
---

# CLIP Zero-Shot And Retrieval Evaluation

Use this skill when checking downstream CLIP transfer mechanisms: class-prompt similarity for zero-shot classification and image/text ranking for retrieval.

## Inputs
- Image embeddings.
- Class text embeddings and labels for classification.
- Caption/text embeddings aligned by index for retrieval.
- Recall cutoffs.

## Outputs
- Top-1 accuracy percentage.
- Recall@K percentages.
- Ranking traces.

## Workflow
1. Normalize image and text/class embeddings.
2. For classification, choose the class with maximum similarity.
3. For retrieval, rank candidates by similarity with deterministic tie-breaking.
4. Compute percentages and save trace data.

## Validation
Run `python tests/test_zeroshot_retrieval_eval.py`.

## Limitations
This skill evaluates provided embeddings; it does not download datasets or run large model inference.

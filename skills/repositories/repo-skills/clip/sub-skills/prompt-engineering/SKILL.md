---
name: prompt-engineering
description: "Build CLIP zero-shot class prompts, tokenizer-safe templates, and
  normalized text classifier weights."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Prompt Engineering

Use this sub-skill when an agent needs to turn class labels into CLIP text prompts, tokenize them safely, build zero-shot classifier weights, or diagnose prompt/template failures.

## Route

- Start with `references/prompting-workflows.md` for class taxonomies, template design, prompt ensembling, normalized text features, and top-k zero-shot scoring.
- Use `references/tokenization.md` before generating large prompt sets or when `clip.tokenize` raises context-length errors.
- Use `references/troubleshooting.md` for unsafe category design, malformed templates, device mismatches, unnormalized features, and multilingual/English limitations.
- Use `scripts/build_zeroshot_classifier.py` when you need a reusable helper for expanding templates, dry-run tokenization, or building normalized classifier weights from a loaded CLIP model.

## Boundaries

- Model selection, `clip.load`, image preprocessing, and image-text inference setup belong in `../model-loading-inference/`.
- Linear probes, cached image feature evaluation, and dataset-scale benchmark loops belong in `../feature-evaluation/`.
- Dataset downloads mentioned in source docs are reference-only; do not make prompt workflows depend on downloading raw datasets by default.

## Minimal Safe Flow

1. Define a fixed English class taxonomy with non-overlapping labels and avoid sensitive or deployment-risk categories unless the user explicitly asks for a research-only audit.
2. Choose templates containing exactly one `{}` placeholder, such as `a photo of a {}.` or domain-specific variants like `a photo of a {}, a type of bird.`
3. Dry-run tokenize the expanded prompts with `clip.tokenize(..., context_length=77, truncate=False)` before running model inference.
4. Encode prompt batches with a loaded CLIP model, normalize every prompt embedding, average templates per class, normalize the averaged class vector, then stack weights as `[text_feature_dim, num_classes]`.
5. For image classification, normalize image features and compute `100.0 * image_features @ zeroshot_weights`; treat softmax/top-k scores as relative to the candidate class list, not calibrated real-world confidence.

## Helper Script

Dry-run prompt tokenization without loading or downloading model checkpoints:

```bash
python sub-skills/prompt-engineering/scripts/build_zeroshot_classifier.py \
  --class-name cat --class-name "electric ray" \
  --template "a photo of a {}." \
  --dry-run-tokenize
```

Build classifier weights only when a model load is explicitly requested or a caller imports `build_zeroshot_classifier(model, class_names, templates)` with an already loaded model. See `references/prompting-workflows.md` for the importable contract.

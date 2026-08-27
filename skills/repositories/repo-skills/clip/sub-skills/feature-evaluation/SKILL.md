---
name: feature-evaluation
description: "Extract CLIP features and evaluate downstream workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CLIP Feature Evaluation

Use this sub-skill when an agent needs dataset-scale CLIP embeddings, normalized image/text features, similarity or search prototypes, `.npz` feature storage, or a downstream linear-probe evaluation plan.

## Start Here

- For batch image embedding extraction, run `python scripts/extract_image_features.py --help`; it writes deterministic `.npz` outputs and only downloads weights if the selected named model is not already cached.
- For image/text embedding workflows, normalization rules, similarity/search prototypes, feature storage, validation checks, and scikit-learn linear probes, read [references/feature-workflows.md](references/feature-workflows.md).
- For intended research use, deployment boundaries, bias/fairness warnings, English-language limits, class taxonomy risk, and dataset licensing/scale caveats, read [references/responsible-evaluation.md](references/responsible-evaluation.md).
- For OOM, dtype/device mismatch, missing scikit-learn, unnormalized embeddings, dataset fixture/download issues, misleading linear-probe accuracy, and large-batch performance, read [references/troubleshooting.md](references/troubleshooting.md).

## Scope Boundaries

This sub-skill owns feature extraction after a CLIP model/preprocess pair is available, `model.encode_image`, `model.encode_text`, feature normalization, evaluation storage, linear probes, small similarity/search prototypes, batch-size/device choices, and responsible evaluation caveats.

Do not use this sub-skill for first-time model loading, cache setup, image preprocessing mechanics, or single-image inference setup; route those steps to [../model-loading-inference/](../model-loading-inference/). Do not use it for prompt template design, prompt ensembling, or label wording strategy; route those decisions to [../prompt-engineering/](../prompt-engineering/). Treat large dataset and checkpoint downloads as explicit opt-in operations, not default evaluation steps.

---
name: feature-extraction
description: "Route Torchreid feature extraction, model discovery/building,
  checkpoint loading, distance scoring, rank evaluation, re-ranking, model
  complexity, ranked-result visualization, and activation-map visualization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Feature Extraction

Use this sub-skill when the task mentions any of the following:

- `FeatureExtractor`, embeddings, or extracting features from images, numpy arrays, or tensors
- comparing query and gallery sets
- `show_avai_models` or `build_model`
- `load_pretrained_weights` or local checkpoint loading
- `compute_distance_matrix`, `evaluate_rank`, or `re_ranking`
- `compute_model_complexity`
- `visualize_ranked_results` or `visrank`
- activation maps / `visactmap` / `return_featuremaps=True`

## Route elsewhere

- Training, data managers, `Engine.run`, or dataset setup → training-evaluation
- ONNX / OpenVINO / TFLite export → model-export
- DML, OSNet-AIN NAS, or PA-100K attribute-recognition projects are excluded long-tail gaps unless a future extension bundles those project sources

## Start here

- [API reference](references/api-reference.md)
- [Metrics and re-ranking](references/metrics-and-reranking.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled helpers

- [scripts/feature_extraction_smoke.py](scripts/feature_extraction_smoke.py) — CPU synthetic build/load/extract/metric smoke with no downloads.
- [scripts/compare_embeddings.py](scripts/compare_embeddings.py) — local-weight query/gallery embedding and distance helper.
- [scripts/visualize_actmap.py](scripts/visualize_actmap.py) — activation-map wrapper with dry-run preview by default.

## Core rules

- Prefer local checkpoint paths. Do not rely on automatic pretrained downloads in helper scripts.
- `FeatureExtractor` returns a tensor shaped `(B, D)` and accepts image paths, HWC numpy arrays, or `torch.Tensor` inputs.
- `compute_distance_matrix` returns squared Euclidean distances for `metric='euclidean'`.
- `evaluate_rank` consumes NumPy distance matrices plus pid/camid arrays and raises if none of the query identities appear in the gallery.
- Activation-map visualization only works when the model `forward()` accepts `return_featuremaps=True` and returns 4-D feature maps at eval time.

# API Reference

## Purpose

This file records the public Alibi constructors and helper functions that are safe to route from the root skill. It is intentionally compact; the focused sub-skills carry the deeper usage notes.

## Verified base APIs

### Global tabular explainers

- `alibi.explainers.ALE(predictor, feature_names=None, target_names=None, check_feature_resolution=True, low_resolution_threshold=10, extrapolate_constant=True, extrapolate_constant_perc=10.0, extrapolate_constant_min=0.1)`
- `alibi.explainers.PartialDependence(predictor, feature_names=None, categorical_names=None, target_names=None, verbose=False)`
- `alibi.explainers.TreePartialDependence(predictor, feature_names=None, categorical_names=None, target_names=None, verbose=False)`
- `alibi.explainers.PartialDependenceVariance(predictor, feature_names=None, categorical_names=None, target_names=None, verbose=False)`
- `alibi.explainers.PermutationImportance(predictor, loss_fns=None, score_fns=None, feature_names=None, verbose=False)`

### Anchors

- `alibi.explainers.AnchorTabular(predictor, feature_names, categorical_names=None, dtype=np.float32, ohe=False, seed=None)`
- `alibi.explainers.AnchorText(predictor, sampling_strategy='unknown', nlp=None, language_model=None, seed=0, **kwargs)`
- `alibi.explainers.AnchorImage(predictor, image_shape, dtype=np.float32, segmentation_fn='slic', segmentation_kwargs=None, images_background=None, seed=None)`

### Confidence and prototypes

- `alibi.confidence.TrustScore(k_filter=10, alpha=0.0, filter_type=None, leaf_size=40, metric='euclidean', dist_filter_type='point')`
- `alibi.confidence.LinearityMeasure(method='grid', epsilon=0.04, nb_samples=10, res=100, alphas=None, model_type='classifier', agg='pairwise', verbose=False)`
- `alibi.prototypes.ProtoSelect(kernel_distance, eps, lambda_penalty=None, batch_size=10000000000.0, preprocess_fn=None, verbose=False)`

### Persistence

- `alibi.saving.save_explainer(explainer, path)`
- `alibi.saving.load_explainer(path, predictor)`

## Verified call patterns

- `ALE.explain(X, features=None, min_bin_points=4, grid_points=None)`
- `PartialDependence.explain(X, features=None, kind='average', percentiles=(0.0, 1.0), grid_resolution=100, grid_points=None)`
- `PartialDependenceVariance.explain(X, features=None, method='importance', percentiles=(0.0, 1.0), grid_resolution=100, grid_points=None)`
- `PermutationImportance.explain(X, y, features=None, method='estimate', kind='ratio', n_repeats=50, sample_weight=None)`
- `AnchorTabular.fit(train_data, disc_perc=(25, 50, 75), **kwargs)`
- `AnchorTabular.explain(X, threshold=0.95, delta=0.1, tau=0.15, batch_size=100, coverage_samples=10000, beam_size=1, stop_on_first=False, max_anchor_size=None, min_samples_start=100, n_covered_ex=10, binary_cache_size=10000, cache_margin=1000, verbose=False, verbose_every=1, **kwargs)`
- `AnchorImage.explain(image, p_sample=0.5, threshold=0.95, delta=0.1, tau=0.15, batch_size=100, coverage_samples=10000, beam_size=1, stop_on_first=False, max_anchor_size=None, min_samples_start=100, n_covered_ex=10, binary_cache_size=10000, cache_margin=1000, verbose=False, verbose_every=1, **kwargs)`
- `TrustScore.fit(X, Y, classes=None)` and `TrustScore.score(X, Y, k=2, dist_type='point')`
- `LinearityMeasure.fit(X_train)` and `LinearityMeasure.score(predict_fn, x)`
- `ProtoSelect.fit(X, y=None, Z=None)` and `ProtoSelect.summarise(num_prototypes=1)`

## Optional exports to treat as placeholders until extras are installed

- SHAP / gradient family: `KernelShap`, `TreeShap`, `IntegratedGradients`
- Counterfactual / similarity family: `CEM`, `Counterfactual`, `CounterfactualProto`, `CounterfactualRL`, `CounterfactualRLTabular`, `GradientSimilarity`
- Distributed or backend-gated helpers: `DistributedAnchorTabular`, `LanguageModel`, `DistilbertBaseUncased`, `BertBaseUncased`, `RobertaBase`, `fetch_fashion_mnist`

Use `scripts/check_optional_backends.py` when a user wants to know whether one of those names is a real runtime object or a `MissingDependency` placeholder.

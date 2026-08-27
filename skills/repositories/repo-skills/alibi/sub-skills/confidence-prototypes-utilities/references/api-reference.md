# API Reference

## Purpose

This file records the verified confidence, prototype, and persistence APIs.

## Constructors

- `TrustScore(k_filter=10, alpha=0.0, filter_type=None, leaf_size=40, metric='euclidean', dist_filter_type='point')`
- `LinearityMeasure(method='grid', epsilon=0.04, nb_samples=10, res=100, alphas=None, model_type='classifier', agg='pairwise', verbose=False)`
- `ProtoSelect(kernel_distance, eps, lambda_penalty=None, batch_size=10000000000.0, preprocess_fn=None, verbose=False)`

## Main call patterns

- `TrustScore.fit(X, Y, classes=None)`
- `TrustScore.score(X, Y, k=2, dist_type='point')`
- `LinearityMeasure.fit(X_train)`
- `LinearityMeasure.score(predict_fn, x)`
- `ProtoSelect.fit(X, y=None, Z=None)`
- `ProtoSelect.summarise(num_prototypes=1)`
- `save_explainer(explainer, path)`
- `load_explainer(path, predictor)`

## Output notes

- `TrustScore.score` returns trust values and the closest non-predicted class.
- `LinearityMeasure.score` returns a scalar or an array-like score depending on the call site.
- `ProtoSelect.summarise` returns selected prototypes plus prototype indices and labels.
- `load_explainer` requires the predictor again because it is not persisted.

## Gotchas

- TrustScore needs labels and class count that match the trained classifier.
- LinearityMeasure needs a predictor compatible with the model type you declared.
- ProtoSelect needs a kernel distance that can handle the batched representation.
- Save/load is version-sensitive.

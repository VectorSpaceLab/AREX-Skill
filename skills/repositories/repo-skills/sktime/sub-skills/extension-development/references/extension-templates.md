# Extension Templates and Estimator Contracts

`sktime` estimators use a strategy/template-method split. Public user methods are owned by the base class; concrete estimators implement private hooks.

| Scitype | Base class | Mandatory hooks |
| --- | --- | --- |
| Forecaster | `BaseForecaster` | `_fit(self, y, X=None, fh=None)`, `_predict(self, fh=None, X=None)` |
| Transformer | `BaseTransformer` | `_fit(self, X, y=None)`, `_transform(self, X, y=None)` |
| Classifier | `BaseClassifier` | `_fit(self, X, y)`, `_predict(self, X)` |
| Regressor | `BaseRegressor` | `_fit(self, X, y)`, `_predict(self, X)` |
| Clusterer | `BaseClusterer` | `_fit(self, X)` and often `_predict` |
| Detector | `BaseDetector` | `_fit(self, X, y=None)`, `_predict(self, X)` |
| Splitter | `BaseSplitter` | `_split(self, y)` |
| Pairwise transformer | pairwise base classes | `_transform(self, X, X2=None)` |

Constructor rules: expose every hyperparameter in `__init__`, write it to `self` without mutation, call `super().__init__()`, clone estimator components before fitting, and store fitted state in attributes ending with `_`.

Do not override public methods such as `fit`, `predict`, `transform`, or `update` merely to add validation. Use tags, `__post_init__`, dynamic tags, and private hooks so the framework keeps doing validation, conversion, vectorization, and fitted-state checks.

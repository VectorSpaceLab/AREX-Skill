# Preprocessing workflows

## Choosing the transformer

| Goal | Use |
| --- | --- |
| Remove linear correlation between non-sensitive columns and columns that encode sensitive information | `CorrelationRemover` |
| Learn a compact prototype representation with reconstruction, prediction, and fairness terms | `PrototypeRepresentationLearner` |

Both transformers are sklearn-style estimators with `fit`, `transform`, and `fit_transform`.

## CorrelationRemover

Signature verified for this source:

```text
CorrelationRemover(*, sensitive_feature_ids=(), alpha=1)
```

- `sensitive_feature_ids`: column names for DataFrames or integer indices for arrays.
- `alpha`: strength of decorrelation. `1` applies full removal; smaller values mix the transformed features with the original non-sensitive features.
- Output contains transformed non-sensitive features; the sensitive columns are not retained in the transformed matrix.

Example:

```python
import pandas as pd
from fairlearn.preprocessing import CorrelationRemover

X_train = pd.DataFrame({
    "score": [0.1, 0.4, 0.8, 0.9],
    "proxy": [1.0, 1.2, 2.2, 2.4],
    "group_code": [0, 0, 1, 1],
})

remover = CorrelationRemover(sensitive_feature_ids=["group_code"], alpha=1.0)
X_train_transformed = remover.fit_transform(X_train)
X_test_transformed = remover.transform(X_test)
```

For a sklearn pipeline, keep the sensitive columns in the input to the remover if the remover needs them, and then ensure the downstream estimator receives the transformed non-sensitive array.

## PrototypeRepresentationLearner

Signature verified for this source:

```text
PrototypeRepresentationLearner(
    n_prototypes=2,
    reconstruct_weight=1.0,
    target_weight=1.0,
    fairness_weight=1.0,
    random_state=None,
    tol=1e-06,
    max_iter=1000,
)
```

Fit signature:

```text
fit(self, X, y=None, *, sensitive_features=None)
```

Use `PrototypeRepresentationLearner` when the task needs a learned representation rather than a simple linear decorrelation step.

```python
from fairlearn.preprocessing import PrototypeRepresentationLearner

learner = PrototypeRepresentationLearner(
    n_prototypes=4,
    fairness_weight=1.0,
    target_weight=1.0,
    random_state=0,
    max_iter=200,
)
Z_train = learner.fit_transform(X_train_numeric, y_train, sensitive_features=A_train)
Z_test = learner.transform(X_test_numeric)
```

Parameter effects:

- `n_prototypes`: representation size; larger values can fit more structure but increase optimization cost.
- `reconstruct_weight`: preserves input reconstruction.
- `target_weight`: preserves prediction target information.
- `fairness_weight`: penalizes sensitive-feature information in the representation.
- `tol` and `max_iter`: optimizer stopping controls.

## Assessment loop

A preprocessing task is not complete until the downstream model is assessed:

```python
from sklearn.linear_model import LogisticRegression
from fairlearn.metrics import MetricFrame, selection_rate
from sklearn.metrics import accuracy_score

estimator = LogisticRegression(solver="liblinear")
estimator.fit(X_train_transformed, y_train)
pred = estimator.predict(X_test_transformed)

mf = MetricFrame(
    metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
    y_true=y_test,
    y_pred=pred,
    sensitive_features=A_test,
)
print(mf.by_group)
print(mf.difference())
```

Compare against the same estimator trained on untransformed features if the user asks whether preprocessing helped.

## Data handling checklist

- Split before fitting transformers.
- Preserve the row order of `A_train`/`A_test` for later assessment.
- For `CorrelationRemover`, do not remove the sensitive column before fitting the remover.
- For `PrototypeRepresentationLearner`, make `X` numeric and finite before fitting.
- Validate `transform` output shape before fitting the downstream estimator.

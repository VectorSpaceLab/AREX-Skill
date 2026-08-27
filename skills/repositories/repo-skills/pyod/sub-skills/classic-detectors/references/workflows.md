# Classic Detector Workflows

Read this for direct, non-ADEngine PyOD recipes. Use these patterns when a user
already knows the detector family, wants a transparent baseline, or needs a
small reproducible check.

## 1. Synthetic smoke test before real data

```python
from pyod.models.knn import KNN
from pyod.utils.data import generate_data, evaluate_print

X_train, X_test, y_train, y_test = generate_data(
    n_train=200,
    n_test=100,
    n_features=2,
    contamination=0.1,
    random_state=42,
)

clf = KNN(contamination=0.1)
clf.fit(X_train)
y_test_scores = clf.decision_function(X_test)
y_test_labels = clf.predict(X_test)

evaluate_print("KNN", y_test, y_test_scores)
print(y_test_labels[:10])
```

For a command-line equivalent, run the bundled helper:

```bash
python scripts/classic_detector_smoke.py --detector KNN --json
```

The helper is self-contained and creates synthetic data; it does not need the
original PyOD checkout.

## 2. Fit a detector on user-provided numeric data

```python
import numpy as np
from sklearn.preprocessing import StandardScaler
from pyod.models.ecod import ECOD

X_train = np.asarray(user_train_features, dtype=float)
X_test = np.asarray(user_test_features, dtype=float)

# Scale when using distance/density/kernel detectors; ECOD is often a good
# scale-insensitive baseline, but scaling still makes comparisons easier.
scaler = StandardScaler().fit(X_train)
X_train_s = scaler.transform(X_train)
X_test_s = scaler.transform(X_test)

clf = ECOD(contamination=0.05)
clf.fit(X_train_s)
scores = clf.decision_function(X_test_s)
labels = clf.predict(X_test_s)
```

Use the same preprocessing fit on training data for train and test. If the data
contains categorical strings, dates, text, lists, or mixed columns, encode or
route to a modality-specific workflow before fitting.

## 3. Choose a first detector family

Start simple unless the user has strong constraints:

- Need fast, parameter-light baseline: `ECOD`, `COPOD`, or `HBOS`.
- Need tree ensemble and robust general baseline: `IForest`.
- Need local/proximity anomalies on low/medium data: `KNN` or `LOF`, after
  scaling.
- Need linear subspace behavior: `PCA`, `KPCA`, `MCD`, or `OCSVM`.
- Need supervised anomaly detection with labels: `XGBOD` via `pyod[xgboost]`,
  then route operational dependency checks to `model-operations`.
- Need deep neural detectors: route to `specialized-modalities` for torch,
  data-size, and device cautions.

If the user does not know which detector to choose and wants an automated plan,
use `automated-lifecycle` and `ADEngine` instead of manually picking one.

## 4. Validate with labels when available

```python
from sklearn.metrics import roc_auc_score
from pyod.utils.utility import precision_n_scores

auc = roc_auc_score(y_test, scores)
pr_at_n = precision_n_scores(y_test, scores)
print({"roc_auc": auc, "precision_at_n": pr_at_n})
```

Always evaluate raw scores, not only binary labels. A detector can rank true
anomalies well even when the contamination threshold needs adjustment.

## 5. Tune contamination and threshold expectations

`contamination` must be in `(0, 0.5]` when passed as a float. It controls the
training score percentile threshold used for `labels_` and `predict`.

Recommended process:

1. Estimate a plausible anomaly rate from domain knowledge or labels.
2. Fit with that contamination.
3. Inspect the number of flagged samples and score distribution.
4. If labels exist, tune with validation metrics rather than visual guesses.
5. If labels do not exist, report ranks/top anomalies and caveat threshold
   uncertainty.

## 6. Present results to non-experts

A useful report should include:

- Detector name and why it was selected.
- Data preprocessing assumptions.
- Contamination or threshold assumption.
- Count and percentage flagged.
- Top anomaly indices with scores/ranks.
- Whether labels were used for validation.
- Known caveats: scale sensitivity, categorical encoding, high-stakes context,
  missing values, small sample size, or detector-specific optional dependency.

Avoid saying "these rows are definitely fraud/defects" from unsupervised labels
alone. Say they are ranked as unusual by the selected detector and should be
reviewed with domain evidence.

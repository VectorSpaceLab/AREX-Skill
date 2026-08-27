# Workflows — model workflows

## 1. Leakage-safe pipeline pattern

The safe pattern is:

1. Split the data.
2. Put the sampler inside the pipeline.
3. Fit the pipeline on the training split only.
4. Evaluate on an untouched test split or cross-validation fold.

Example shape:

```python
from imblearn.pipeline import make_pipeline
from imblearn.under_sampling import RandomUnderSampler
from sklearn.linear_model import LogisticRegression

model = make_pipeline(RandomUnderSampler(random_state=0), LogisticRegression())
model.fit(X_train, y_train)
```

Do not resample the full dataset before splitting when the user is trying to
avoid leakage.

## 2. Choose the ensemble

- `BalancedBaggingClassifier`: user wants bagging and an internal sampler.
- `BalancedRandomForestClassifier`: user wants the familiar random-forest API.
- `EasyEnsembleClassifier`: user wants AdaBoost trained on balanced subsets.
- `RUSBoostClassifier`: user wants boosting with under-sampling between rounds.

## 3. Use instance-hardness cross-validation carefully

`InstanceHardnessCV` is only for binary classification.
It needs an estimator that supports `predict_proba`.
It is best used for model selection and hyperparameter tuning, not as a generic
performance-estimation splitter.

## 4. Check fit/transform semantics

The imbalanced-learn pipeline has a non-scikit-learn surprise:

- `fit_transform` can resample.
- `fit` followed by `transform` does not resample.

Document this when a user expects the old scikit-learn equivalence.

## 5. Native evidence to match later

- `test_make_pipeline`
- `test_pipeline_methods_pca_svm`
- `test_balanced_random_forest`
- `test_easy_ensemble_classifier`
- `test_rusboost`
- `test_default_params` for `InstanceHardnessCV`

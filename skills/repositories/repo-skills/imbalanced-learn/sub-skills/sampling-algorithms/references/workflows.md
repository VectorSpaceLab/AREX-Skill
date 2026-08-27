# Workflows — sampling algorithms

## 1. Pick the family

| User goal | Preferred family | Why |
|---|---|---|
| Duplicate the minority class safely | `RandomOverSampler` | Simple and easy to explain. |
| Create synthetic minority points | `SMOTE`, `ADASYN`, or a SMOTE variant | Adds new points rather than duplicates. |
| Handle mixed numeric + categorical data | `SMOTENC` | Categorical features are treated specially. |
| Handle all-categorical data | `SMOTEN` | Uses categorical distance logic. |
| Remove majority examples | `RandomUnderSampler` | Fast reduction of class imbalance. |
| Remove borderline or noisy points | `TomekLinks`, ENN, RENN, AllKNN, NCR | Cleaning-focused under-sampling. |
| Generate representative prototypes | `ClusterCentroids` | Synthesizes centroids instead of selecting originals. |
| Combine over- and under-sampling | `SMOTEENN`, `SMOTETomek` | Packaged two-stage workflow. |
| Wrap custom logic | `FunctionSampler` | Thin adapter around user code. |

## 2. Check the input form

- Dense numeric arrays usually work with any sampler family.
- Sparse matrices are accepted by many samplers, but some outputs may densify.
- pandas DataFrames preserve column labels in many workflows and are especially
  useful for `SMOTENC` feature-name routing.
- Object arrays are useful for mixed-type toy examples, but be explicit about
  categorical columns and dtype expectations.

## 3. Check the strategy

- `sampling_strategy='auto'` is the default for most public samplers.
- A `dict` strategy gives exact per-class target counts.
- A callable strategy can compute targets from the current label distribution.
- For custom policies, confirm the result with a tiny count check before using
  the sampler in a pipeline.

## 4. Keep resampling inside the training branch

A safe pattern looks like this:

```python
from imblearn.pipeline import make_pipeline
from imblearn.under_sampling import RandomUnderSampler
from sklearn.linear_model import LogisticRegression

model = make_pipeline(RandomUnderSampler(random_state=0), LogisticRegression())
model.fit(X_train, y_train)
```

Do not resample the whole dataset before the split if the task is meant to
avoid data leakage.

## 5. Prefer a tiny proof

The bundled `sampler_smoke.py` should finish in seconds and demonstrate one
representative success case for each major sampler family.

## Native evidence to match later

- `test_ros_fit_resample`
- `test_sample_regular` in `test_smote.py`
- `test_smotenc_pandas`
- `test_rus_fit_resample`
- `test_tl_fit_resample`
- `test_sample_regular` in `test_smote_enn.py`
- `test_function_sampler_func`

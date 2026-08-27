# Automatic preprocessing guide

MLJAR-Supervised trains model pipelines that include preprocessing. The normal user contract is: pass raw tabular data to `AutoML.fit(X, y)`, then pass raw rows with matching columns to `predict()`, `predict_proba()`, `predict_all()`, `score()`, apps, or report workflows. The fitted preprocessing is saved with the model and reused at prediction time.

## What is automatic

MLJAR can automatically handle:

- missing feature values
- missing target-row exclusion
- categorical encoding
- text vectorization
- datetime expansion
- numeric scaling for algorithms that need it
- target encoding and regression target scaling
- empty or constant feature removal
- optional feature engineering such as golden features, feature selection, k-means features, and mixed encoding

Do not run `pd.get_dummies()`, manual label encoders, or manual scalers first unless the user has an external production schema that requires it.

## Type detection and column cleanup

During data inspection:

- empty columns and constant columns are marked for removal;
- columns with missing values are marked for imputation;
- pandas `category` columns are treated as categorical;
- object/string columns are categorical unless they look like high-cardinality text;
- datetime dtype columns are treated as datetime;
- numeric columns are checked for whether scaling is useful.

Important dtype guidance:

- If a column is intended as datetime, parse it with `pd.to_datetime()` before `fit()`. Raw date strings can look categorical or text.
- If short free-text fields have only a few repeated values, they may be treated as categorical. This is usually acceptable for IDs such as state or product code, but not for semantic text fields.
- Very high-cardinality object columns can be treated as text and transformed with TF-IDF. Remove identifier columns first if their uniqueness is not predictive.

## Missing values

Feature missing-value handling uses learned fill values from training:

| Feature type | Default fill behavior |
| --- | --- |
| numeric | median |
| categorical | most frequent value, or a placeholder in fill-min variants |
| datetime | most frequent timestamp |
| text | placeholder/zero text-vector behavior |

Target missing values are not imputed. Rows with missing targets are removed. When sample weights or sensitive features are provided, matching rows are removed from those arrays too.

Prediction-time missing values are handled by the stored preprocessing. If new missing values appear in columns that did not have missing values during training, MLJAR has a fallback fill pass, but you should still investigate why serving data differs from training data.

## Categorical encoding

Categorical handling depends on the learner and training configuration.

Common behavior:

- For algorithms that require numeric categoricals, MLJAR uses integer encoding or one-hot encoding.
- Low-cardinality categoricals can be one-hot encoded in mixed-encoding flows.
- Higher-cardinality categoricals are typically integer encoded.
- Binary one-hot encoding creates one indicator column for the second learned value; multicategory one-hot creates columns for learned values.
- Integer encoders can assign new integer codes to unseen prediction categories. One-hot encoders leave unseen categories as all-zero indicator combinations for that feature.
- CatBoost workflows can use a lighter conversion path for categoricals, but missing values, datetime, text, and target preprocessing still apply.

Practical recommendations:

1. Leave string/category predictors raw unless you need a fixed external schema.
2. Normalize obvious dirty categories before fit, for example inconsistent casing or whitespace.
3. Avoid high-cardinality IDs as predictors unless they are truly meaningful.
4. Expect unseen categories at prediction time to be accepted but not necessarily informative.

## Text features

Text columns are vectorized with TF-IDF-style features. The transformer lowercases, uses word tokens, applies English stop words, and limits the vocabulary to a compact maximum feature count.

Use text preprocessing carefully:

- Remove IDs or hashes that only appear once.
- Keep enough non-null text examples for a meaningful vocabulary.
- Consider converting short enumerated text fields to pandas `category` if they are categories rather than free text.
- Expect transformed text features to be stored in the fitted pipeline and reused at prediction time.

## Datetime features

Datetime columns are expanded into numeric calendar and relative-time features when those values vary in the training data. Possible derived columns include year, month, day, weekday, day-of-year, hour, and days since the minimum training timestamp. The original datetime column is dropped after expansion.

Recommendations:

- Convert raw strings with `pd.to_datetime(..., errors="coerce")` and inspect the number of missing timestamps before fit.
- Do not pre-split datetimes unless you need custom calendar logic; MLJAR can generate common features.
- For time-series leakage, design validation splits before fitting. Automatic datetime expansion does not make random validation safe for time-dependent problems.

## Numeric scaling and target scaling

Some learners require scaled numeric inputs, while tree learners often do not. MLJAR applies standard scaling when required by the selected model pipeline or when numeric columns are marked for scaling. Regression targets can be scaled normally or with log-plus-normal scaling when the target distribution suggests it.

Scaling is part of the stored preprocessing. Do not manually scale new prediction data before calling prediction methods.

## Target preprocessing

Classification targets can be converted to numeric labels internally. Binary labels that are not already `0`/`1` are encoded, and multiclass labels are encoded for learner compatibility. Public predictions are mapped back to the original target labels where possible.

Regression targets may be scaled internally and inverse-transformed for predictions. If task inference is not what you intend, set `ml_task` explicitly before fitting.

## Feature-engineering flags

These options live in the `AutoML(...)` constructor and affect training workload. Route final training-mode and algorithm decisions to `../training-core/`, but keep the data implications in mind.

| Option | Automatic defaults by mode | Data effect | Cost and artifact impact |
| --- | --- | --- | --- |
| `golden_features` | off in `Explain` and `Optuna`; on in `Perform` and `Compete` | Creates arithmetic features from numeric feature pairs, such as differences, ratios, sums, and products. | Trains/evaluates many small decision trees, writes a golden-feature summary, and can add extra trained models. Disable for speed or when no useful numeric pairs exist. |
| `features_selection` | off in `Explain` and `Optuna`; on in `Perform` and `Compete` | Adds a random feature, uses permutation importance, drops features less important than random, and retrains selected models on the reduced set. | Adds model-training time and can remove weak columns. Disable when feature count is already small or runtime matters. |
| `kmeans_features` | on only in `Compete` when left `auto` | Creates cluster-distance features and a cluster label from continuous columns. | Adds per-model/fold feature generation and can fail when there are no continuous features. Disable for very small or mostly categorical datasets. |
| `mix_encoding` | on only in `Compete` when left `auto` | Tries alternative categorical encodings, using one-hot for low-cardinality columns and integer labels for higher-cardinality columns. | Adds alternative model candidates. Disable for deterministic fast runs or if the category schema is externally fixed. |

Fast smoke configuration example:

```python
automl = AutoML(
    mode="Explain",
    algorithms=["Baseline", "Decision Tree"],
    train_ensemble=False,
    stack_models=False,
    explain_level=0,
    golden_features=False,
    features_selection=False,
    kmeans_features=False,
    mix_encoding=False,
)
```

This example is intentionally about preprocessing cost control. For full model-quality setup, use `../training-core/`.

## When to preprocess manually

Manual preprocessing is reasonable when:

- a production serving contract requires fixed feature columns before AutoML;
- privacy policy requires redacting or tokenizing fields before any model sees them;
- raw identifiers or leakage columns must be removed;
- domain-specific datetime or text transformations are materially better than generic ones;
- custom validation requires row filtering before split indices are computed.

Even then, avoid duplicating MLJAR's fitted transformations at prediction time. Either hand MLJAR raw columns consistently, or own the entire external schema consistently before both fit and predict.

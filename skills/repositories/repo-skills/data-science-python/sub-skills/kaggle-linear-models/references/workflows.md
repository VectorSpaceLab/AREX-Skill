# Workflows

Use `scripts/make_tiny_fixtures.py` first when you want a self-contained smoke run. The examples below assume fixtures are written under `./fixtures/` and outputs go under `./out/`.

Before any real run, `--help` should work for every bundled script.

## Common smoke pass

```bash
python scripts/make_tiny_fixtures.py --output-dir ./fixtures
python scripts/sklearn_svm_submission.py --help
python scripts/hashed_logistic_sgd.py --help
python scripts/categorical_logistic_submission.py --help
```

That sequence verifies the bundled CLI surface before model training begins.

## 1) Dense matrix SVC submission

Use this route for a dense numeric matrix with a separate label vector.

### Inputs

- `--train`: dense numeric CSV matrix, one sample per row.
- `--labels`: one label per row, same order as `--train`.
- `--test`: dense numeric CSV matrix with the same feature count.
- `--output`: prediction file to create.

### Example

```bash
python scripts/sklearn_svm_submission.py \
  --train ./fixtures/dense/train.csv \
  --labels ./fixtures/dense/train_labels.csv \
  --test ./fixtures/dense/test.csv \
  --output ./out/svm_predictions.csv \
  --kernel rbf \
  --C 1.0
```

### What it does

- Loads the matrices with `numpy.loadtxt`.
- Fits `sklearn.svm.SVC` on the training matrix and label vector.
- Writes one class prediction per test row.
- Keeps the output small and deterministic; there is no probability column.

### Useful SVC flags

- `--kernel`: `rbf`, `linear`, `poly`, `sigmoid`.
- `--C`: margin penalty.
- `--gamma`: kernel scale control.
- `--degree`: polynomial degree.
- `--coef0`: polynomial/sigmoid offset.
- `--cache-size`: SVC cache size in MB.
- `--max-iter`: cap on solver iterations.
- `--random-state`: included for API completeness when supported by the solver.

### Notes

- This helper assumes integer-coded class labels.
- Dense CSVs should be headerless.
- If the label file has a different row count than the train matrix, the script should stop before fitting.

Read `references/troubleshooting.md` if `numpy.loadtxt` complains about headers or if the matrix shape is not what you expect.

## 2) Hashed SGD logistic regression for Criteo-like CSVs

Use this route when the data is sparse, mixed numeric/categorical, and best handled by feature hashing.

### Inputs

- `--train`: CSV with a header row that includes `Label` and `Id`.
- `--test`: CSV with a header row that includes `Id` and the feature columns.
- `--output`: probability CSV to create.

### Example

```bash
python scripts/hashed_logistic_sgd.py \
  --train ./fixtures/hashed/train.csv \
  --test ./fixtures/hashed/test.csv \
  --output ./out/hashed_logistic_submission.csv \
  --bits 12 \
  --alpha 0.1 \
  --epochs 2
```

### What it does

- Treats every non-label, non-id field as a categorical token of the form `field=value`.
- Normalizes blanks to a missing token instead of dropping them.
- Hashes each token into a power-of-two feature space with a stable BLAKE2b hash.
- Trains an online logistic model with an adaptive per-feature step size.
- Writes `Id,Predicted` probabilities for the test rows.

### Useful flags

- `--bits`: log2 of the hash space size; larger values reduce collisions.
- `--alpha`: SGD learning rate.
- `--epochs`: number of passes over the training CSV.
- `--label-column`: training label column name, default `Label`.
- `--id-column`: row identifier column name, default `Id`.
- `--missing-token`: placeholder token for empty cells.

### Notes

- Keep the label column binary.
- The script is safe for categorical strings, numeric strings, and mixed rows.
- It is deliberately bounded: there is no unbounded feature search.

Read `references/troubleshooting.md` if a CSV row is malformed, if the label column is missing, or if you need to understand why `citreo_code_v2.py` is not runnable.

## 3) One-hot categorical logistic regression with bounded CV

Use this route for a categorical table where the target is in `ACTION` and the identifier is in `id`.

### Inputs

- `--train`: CSV with a label column and, usually, an id column.
- `--test`: CSV with the same feature columns, usually including an id column.
- `--output`: submission CSV to create.

### Example

```bash
python scripts/categorical_logistic_submission.py \
  --train ./fixtures/categorical/train.csv \
  --test ./fixtures/categorical/test.csv \
  --output ./out/categorical_submission.csv \
  --cv-splits 3
```

### What it does

- Reads the train/test tables with pandas.
- Selects all non-label, non-id columns as features.
- Reindexes the test set to the training feature columns so column order stays stable.
- Fills missing categories with a placeholder token.
- Fits `OneHotEncoder(handle_unknown="ignore", sparse_output=True)` and a logistic regression model in a single pipeline.
- Optionally reports ROC AUC with bounded `StratifiedKFold` when `--cv-splits` is greater than 1.
- Writes `id,ACTION` probabilities by default.

### Useful flags

- `--label-column`: target column name, default `ACTION`.
- `--id-column`: row identifier column name, default `id`.
- `--C`: logistic regression regularization strength.
- `--solver`: logistic regression solver; `liblinear` is a safe sparse baseline.
- `--max-iter`: upper bound on solver iterations.
- `--cv-splits`: number of stratified folds to evaluate; `0` disables CV.
- `--seed`: random seed for fold shuffling.

### Notes

- The encoder is fit on the training feature columns only; unseen categories in test are ignored safely.
- If the id column is missing, the helper may need to fall back to generated row numbers.
- Keep `--cv-splits` small; the point is a bounded check, not a long validation loop.

Read `references/troubleshooting.md` if a fold contains only one class, if unseen categories appear, or if you need to modernize more of the old starter code.

## 4) Reference-only interaction-feature recipe

The expanded Amazon-style source example, `logistic_regression_updated.py`, explored pairwise and triple feature combinations plus greedy feature selection. That idea is useful, but the original exhaustive loop is not bundled as a runnable helper.

Use the pattern only when a user explicitly supplies a small dataset and a clear time budget.

### Bounded recipe

1. Pick a short, named list of candidate interactions instead of all combinations.
2. Add them with a modern transformer such as `PolynomialFeatures(interaction_only=True, include_bias=False)` or a small hand-built combiner.
3. Score each bounded candidate set with `StratifiedKFold` and `roc_auc_score`.
4. Stop after a fixed number of folds and a fixed candidate budget.

### Why it stays reference-only

- The original greedy search can expand combinatorially.
- The source uses removed or legacy APIs such as `cross_validation`, `.ix`, and `metrics.auc_score`.
- The full search is a poor default for a safe, reusable runtime skill.

If a future task explicitly requests interaction search, start from this bounded recipe instead of reviving the full greedy loop.

# Troubleshooting

This file covers the most common failures for the Kaggle-style linear-model routes in this sub-skill.

## Quick triage order

1. Run `--help` on the script you want to use.
2. Confirm the CSV layout matches `references/data-formats.md`.
3. Use `scripts/make_tiny_fixtures.py` to verify the environment and the helper itself.
4. Read the row-specific notes below.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError` or empty output | Wrong path or missing fixture | Recheck the explicit `--train`, `--labels`, `--test`, and `--output` values. The bundled scripts do not guess paths. |
| `numpy.loadtxt` complains about text or headers | Dense matrix files are not raw numeric CSVs | Strip the header row or convert the file to a headerless numeric matrix before using `scripts/sklearn_svm_submission.py`. |
| `ValueError: Found unknown categories ...` | Old categorical code or an encoder fit on the wrong data | Use `scripts/categorical_logistic_submission.py`, which fits `OneHotEncoder(handle_unknown="ignore", sparse_output=True)` on the training columns and ignores unseen test categories. |
| `ValueError: This solver needs samples of at least 2 classes` | Train data or a CV fold contains only one class | Reduce `--cv-splits`, use stratified folds, or skip CV entirely with `--cv-splits 0`. Make sure the smoke fixtures are intact. |
| `roc_auc_score` fails inside CV | A validation fold still ended up with one class | Lower the fold count or let the helper skip CV when the minority class is too small. |
| `TypeError: got an unexpected keyword argument 'sparse'` | Legacy one-hot code | Use `sparse_output=True` instead of `sparse=True`. |
| `AttributeError: module sklearn has no attribute cross_validation` | Legacy starter code | Use the bundled modern scripts and `sklearn.model_selection` instead of `sklearn.cross_validation`. |
| `AttributeError: module sklearn.metrics has no attribute auc_score` | Legacy starter code | Replace the legacy call with `sklearn.metrics.roc_auc_score`. |
| `raw_input` blocks or crashes | Python 2 starter code | Use the bundled CLI arguments; none of the runtime scripts ask interactively for filenames. |
| `DataFrame.ix` fails | Old pandas indexing syntax | Use `.loc`, `.iloc`, or explicit column names. The bundled categorical helper already does this. |
| `citreo_code_v2.py` looks like it should work but does not | `get_x` is commented out in the source variant | Ignore that broken variant and use `scripts/hashed_logistic_sgd.py` instead. |
| Logistic regression converges slowly or warns about iterations | Feature space too large or `max_iter` too low | Increase `max_iter` a little, reduce `--cv-splits`, or keep the feature set bounded. |
| SVC is slow or overfits on tiny dense data | Default RBF kernel on too few samples | Try `--kernel linear` or lower `C` on the dense route. |
| Output probabilities look empty or all identical | Model saw too little signal or the feature layout was wrong | Recheck the input columns and confirm the fixture generator created the expected labels and categories. |
| Feature-interaction search explodes in size | Using the reference-only greedy idea as if it were a default route | Keep the candidate list small and bounded, or stop and use the reference-only recipe rather than the full greedy loop. |

## Route-specific notes

### Dense matrix SVC

- The helper expects a train matrix, a separate label file, and a test matrix with matching feature counts.
- Labels should be integer-coded class values.
- If you need probabilities instead of class labels, this is the wrong helper; use a different workflow or add a separate calibration step outside the bundle.

### Hashed logistic SGD

- Every non-label, non-id column is hashed as a token.
- Empty cells are not dropped; they become the missing token.
- If a CSV row is malformed and has extra fields, fix the source file first rather than silently dropping data.

### Categorical logistic

- The helper reindexes test columns to match the training feature columns.
- If the id column is absent, the helper may fall back to generated row numbers, but a real submission file is clearer when the id column is present.
- Use a small `--cv-splits` value so the CV check stays bounded.

### Reference-only interaction recipe

- The original expanded Amazon example explored pairwise and triple combinations with a greedy loop.
- That loop is not bundled because it is expensive and depends on old APIs.
- If you need interaction features, start with a short candidate list and a fixed fold budget, not with an unbounded search.

## Broken source variant reminder

The source file `citreo_code_v2.py` is intentionally treated as a troubleshooting example, not as a runtime helper. Its hashed feature extractor is commented out, so it does not define a complete runnable workflow.

## When to stop and rethink

If the data layout is not clearly one of the three supported formats, pause and normalize the input files first. Do not try to force a dense matrix helper onto sparse categorical data or a one-hot helper onto a raw numeric matrix.
# Environment and dependency guidance

## Purpose

Read this when a future agent needs to run the generated DataSciencePython helper scripts or diagnose missing imports. The source repository is a tutorial/example collection, not an installable Python package.

## Public dependency set

For the generated helpers, use Python 3.10+ or 3.11+ and install only the workflow dependencies you need:

```bash
python -m pip install numpy pandas scipy scikit-learn statsmodels matplotlib
```

- `numpy` and `scipy`: numeric arrays, sparse matrices, and helper utilities.
- `pandas`: CSV table loading for statsmodels and categorical logistic workflows.
- `scikit-learn`: SVC, LogisticRegression, OneHotEncoder, CV, and AUC metrics.
- `statsmodels`: admissions logistic regression via `statsmodels.api.Logit`.
- `matplotlib`: optional non-interactive plot output for the admissions workflow.

Optional live Twitter/X streaming needs Tweepy and credentials; the offline JSONL extractor does not:

```bash
python -m pip install tweepy
```

The R/jsonlite converter from the source evidence is represented by a Python stdlib JSONL extractor in the generated skill, so R is not required for the selected runtime workflows.

## Quick check

From the generated skill root, run:

```bash
python scripts/check_data_science_python_env.py
```

Add `--check-plots` before requesting plot output and `--check-tweepy` before using the optional live-stream template.

## Compatibility notes

- The source examples were Python 2-era and used removed APIs such as `sklearn.cross_validation`, `metrics.auc_score`, pandas `.ix`, and bare `print` statements. Use the generated helpers instead of copying those legacy patterns.
- The source repository does not provide package metadata, console entry points, or a native test suite. Treat the generated scripts as self-contained adaptations of the examples, not as wrappers around a package import.
- Do not install broad data-science stacks for every route if the task only needs one helper. For example, tweet JSONL extraction uses only Python stdlib.

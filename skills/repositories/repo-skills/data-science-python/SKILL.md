---
name: data-science-python
description: "Use the DataSciencePython tutorial/example collection through
  modern self-contained helpers for Python data-science resources, statsmodels
  logistic regression, scikit-learn Kaggle-style tabular classifiers, and
  Twitter JSONL extraction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DataSciencePython

Use this repo skill when the task names **DataSciencePython** or asks for a safe, modern way to use its historical Python data-science tutorial list and standalone examples.

This repository is not an installable Python package. It is a curated README plus legacy scripts. Use the generated sub-skills and bundled helper scripts instead of running the original Python 2-era files directly.

## Start here

1. Read `references/repo-provenance.md` when checking staleness against a checkout.
2. Read `references/environment.md` before running helper scripts.
3. Run `scripts/check_data_science_python_env.py` when dependency availability is uncertain.
4. Route to the smallest matching sub-skill below.

## Route map

| User intent | Load this sub-skill | Why |
| --- | --- | --- |
| Navigate the README's Python/data science/pandas/sklearn/ML/NLP resource categories or modernize the tiny Python basics snippets. | `sub-skills/tutorial-resource-map/SKILL.md` | Distills the tutorial index and Python 2-era snippets without relying on external links being live. |
| Fit the admissions logistic-regression example with pandas and statsmodels, including dummy variables, an intercept, predictions, and optional plots. | `sub-skills/statsmodels-logit-workflow/SKILL.md` | Owns the copied admissions CSV fixtures and modernized `statsmodels_admission_logit.py` helper. |
| Run Kaggle-style dense SVM, hashed SGD logistic regression, or one-hot categorical LogisticRegression examples. | `sub-skills/kaggle-linear-models/SKILL.md` | Modernizes the legacy scikit-learn/Criteo/Amazon examples and supplies tiny fixture generation. |
| Extract text from stored Twitter/X JSON-lines data or plan an optional safe live-streaming attempt. | `sub-skills/twitter-json-workflow/SKILL.md` | Replaces local R/Windows/Tweepy examples with offline extraction and credential-safe streaming guidance. |

## Dependency quick check

From this generated skill root:

```bash
python scripts/check_data_science_python_env.py
```

For optional plot output, add:

```bash
python scripts/check_data_science_python_env.py --check-plots
```

For the optional live-stream template, add:

```bash
python scripts/check_data_science_python_env.py --check-tweepy
```

## Important operating constraints

- Treat README links as topic signals, not guaranteed live URLs.
- Do not instruct future agents to run original source scripts; the bundled helpers are the runtime surface.
- Do not assume `pip install -e .` works; there is no package metadata in the source snapshot.
- Keep live Twitter/X collection opt-in only. It requires user-provided credentials, Tweepy compatibility, network access, and explicit authorization to connect.
- Use tiny bundled/generated fixtures for smoke tests when the original Kaggle/Amazon data files are missing.

## Cross-cutting references

- `references/environment.md` explains the public dependency set and compatibility notes.
- `references/troubleshooting.md` covers missing package metadata, legacy APIs, missing competition data, stale links, and credentialed workflows.
- `references/repo-routing-metadata.json` contains managed router metadata for a later import transaction.

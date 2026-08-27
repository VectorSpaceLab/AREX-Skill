# Cross-cutting troubleshooting

## Repository is not importable as a package

**Symptom:** `pip install -e .`, `import DataSciencePython`, or a package-version lookup fails.

**Cause:** DataSciencePython is a curated tutorial/example repository with standalone scripts and CSV fixtures, not a packaged library.

**Recovery:** Use the generated helper scripts under this skill. Run `python scripts/check_data_science_python_env.py` to verify third-party dependencies instead of expecting a repo package import.

## Legacy Python 2 syntax or removed APIs appear

**Symptoms:** `SyntaxError` near `print ...`, `AttributeError: module 'sklearn' has no attribute 'cross_validation'`, `AttributeError: 'DataFrame' object has no attribute 'ix'`, or `AttributeError: module 'sklearn.metrics' has no attribute 'auc_score'`.

**Cause:** Several source examples predate modern pandas and scikit-learn.

**Recovery:** Do not run the legacy source scripts directly. Route to the matching generated sub-skill:

- Statsmodels admissions regression: `sub-skills/statsmodels-logit-workflow/SKILL.md`
- Dense SVM, hashed logistic, or categorical logistic submissions: `sub-skills/kaggle-linear-models/SKILL.md`
- Twitter JSONL extraction: `sub-skills/twitter-json-workflow/SKILL.md`

## Missing competition data

**Symptoms:** `FileNotFoundError` for `train.csv`, `test.csv`, `trainLabels.csv`, or `data/train.csv`.

**Cause:** Some source examples assume Kaggle/Amazon files that are not bundled in the source repository.

**Recovery:** Use the generated fixture maker in `sub-skills/kaggle-linear-models/scripts/make_tiny_fixtures.py` for smoke tests, or pass explicit paths to user-supplied data. For the admissions statsmodels workflow, use the copied CSVs under `sub-skills/statsmodels-logit-workflow/references/data/`.

## Stale external tutorial links

**Symptoms:** README links fail, redirect, or require sign-in.

**Cause:** The README is a historical curated list. Network resources can move or disappear.

**Recovery:** Treat the README-derived topic index as route guidance, not proof that every external URL is live. Use local generated references and scripts for executable workflows.

## Optional credentials or network are required

**Symptoms:** Tweepy import errors, missing Twitter/X tokens, authentication failures, HTTP 401/403/429, or a task that asks to stream live tweets.

**Cause:** Live streaming is optional and requires credentials, network access, and current Twitter/X API compatibility.

**Recovery:** Use `sub-skills/twitter-json-workflow/scripts/extract_tweet_text.py` for offline JSONL files. Only use the live-stream template after the user provides explicit credentials and authorizes a network connection.

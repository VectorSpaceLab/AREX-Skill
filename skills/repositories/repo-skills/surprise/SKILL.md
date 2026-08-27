---
name: surprise
description: "Use Surprise for explicit-feedback recommender workflows: load
  rating data, fit collaborative-filtering predictors, evaluate and tune models,
  generate recommendations, and serialize results."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Surprise

Use this skill when a task involves `scikit-surprise` / `surprise`, explicit rating recommendation, collaborative filtering, rating prediction, dataset loading, evaluation and search, top-N ranking, or serialization.

## Start Here

- Install with `pip install scikit-surprise`.
- Add `pandas` when you need dataframe loading or the bundled smoke script's optional fit/test check.
- Add `pytest` only for repository verification or local native smoke runs.
- Run [`scripts/check_surprise_environment.py`](scripts/check_surprise_environment.py) for a safe local import/version/CLI check. Use `--smoke-fit` when pandas is available and you want a tiny end-to-end fit/test check.
- For CLI discovery, use `surprise --help` or `python -m surprise --help`.

## Route by Task

- Load, inspect, validate, or split rating data: [`sub-skills/data-loading/`](sub-skills/data-loading/SKILL.md)
- Choose and configure predictors, fit/test/predict, inspect baseline or similarity options, retrieve neighbors, or build a custom `AlgoBase`: [`sub-skills/prediction-algorithms/`](sub-skills/prediction-algorithms/SKILL.md)
- Score predictions, split data, cross-validate, tune hyperparameters, inspect `cv_results`, or use the CLI: [`sub-skills/evaluation-and-search/`](sub-skills/evaluation-and-search/SKILL.md)
- Build top-N recommendations, precision/recall@k summaries, or dump/load roundtrips: [`sub-skills/recommendation-and-analysis/`](sub-skills/recommendation-and-analysis/SKILL.md)

## Shared References

- Read [`references/overview.md`](references/overview.md) for the package/module map and common data flow.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for install, data, id, evaluation, search, CLI, and serialization pitfalls.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill still matches the current checkout.

## Boundaries

This is a runtime user skill, not a maintainer guide. It does not cover docs builds, benchmark generation, or release publishing.

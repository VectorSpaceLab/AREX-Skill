---
name: query-strategies
description: "Router for modAL uncertainty, disagreement, batch, density,
  expected-error, multilabel, and strategy-combinator workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# query-strategies

Use this sub-skill when the learner or committee already exists and you need to choose, compose, or troubleshoot how it queries the pool. It covers uncertainty, disagreement, ranked batch, expected-error reduction, information density, multilabel SVM selectors, and selector/combinator helpers.

Query callables receive `(learner_or_estimator, X_pool, **kwargs)` and may return bare indices, an index/instance pair, or `(indices, metrics)`. `BaseLearner.query(..., return_metrics=True)` only forwards metrics when the strategy supplies them.

## Read
- [references/strategy-reference.md](references/strategy-reference.md) — built-in strategies, signatures, return shapes, defaults, and selector behavior.
- [references/custom-strategies.md](references/custom-strategies.md) — combined utilities, custom selectors, ranked batch helpers, density-aware strategies, and multilabel recipes.
- [references/troubleshooting.md](references/troubleshooting.md) — `NotFittedError`, missing `predict_proba`, tuple-vs-index confusion, batch cost, and multilabel shape recovery.

## Run
- [scripts/query_strategy_smoke.py](scripts/query_strategy_smoke.py) — deterministic tiny-data smoke for custom combinations, ranked batch returns, information density, and multilabel return shapes.

## Route elsewhere
- [`../learners-and-committees/SKILL.md`](../learners-and-committees/SKILL.md) — build `ActiveLearner`, `Committee`, or `CommitteeRegressor` objects before picking a strategy.
- [`../bayesian-optimization/SKILL.md`](../bayesian-optimization/SKILL.md) — Bayesian acquisition functions such as `max_PI`, `max_EI`, and `max_UCB`.
- [`../deep-and-optional-integrations/SKILL.md`](../deep-and-optional-integrations/SKILL.md) — MC dropout and other optional deep-learning strategies.

## Covered surfaces
- uncertainty: `classifier_uncertainty`, `classifier_margin`, `classifier_entropy`, `uncertainty_sampling`, `margin_sampling`, `entropy_sampling`
- disagreement: `vote_entropy`, `consensus_entropy`, `KL_max_disagreement`, `vote_entropy_sampling`, `consensus_entropy_sampling`, `max_disagreement_sampling`, `max_std_sampling`
- batch: `uncertainty_batch_sampling`, `ranked_batch`, `select_instance`, `select_cold_start_instance`
- expected error: `expected_error_reduction`
- density: `information_density`, `similarize_distance`
- multilabel: `SVM_binary_minimum`, `max_loss`, `mean_max_loss`, `min_confidence`, `avg_confidence`, `max_score`, `avg_score`
- utilities: `multi_argmax`, `multi_argmin`, `shuffled_argmax`, `shuffled_argmin`, `weighted_random`, `make_linear_combination`, `make_product`, `make_query_strategy`

## Use when
- the query policy changes but the learning object stays the same
- you need to combine or normalize several utility measures
- you need to debug whether a strategy returns indices only or `(indices, metrics)`

## Do not use when
- you still need learner or committee construction
- the task is Bayesian optimization
- the task depends on MC dropout or another deep-only acquisition path

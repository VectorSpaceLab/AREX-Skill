# modAL package overview

## When to read

Read this when you need a quick map of the modAL package, its core abstractions, and the boundary between minimum classical active-learning workflows and optional deep-learning integrations.

## Package identity

- Distribution package: `modAL-python`
- Import package: `modAL`
- Version covered by this skill: `0.4.2`
- Core dependency family: NumPy, SciPy, pandas, scikit-learn, skorch; PyTorch is needed for `modAL.dropout` but is not a CUDA requirement by itself.

Do not confuse this package with unrelated packages named `modal` or cloud/serverless frameworks. The import is case-sensitive: use `import modAL`.

## Public module map

| Module | Primary public surface | Route |
|---|---|---|
| `modAL.models` | `ActiveLearner`, `DeepActiveLearner`, `BayesianOptimizer`, `Committee`, `CommitteeRegressor` | Learners, Bayesian optimization, optional deep integration |
| `modAL.uncertainty` | classifier uncertainty/margin/entropy measures and sampling wrappers | [../sub-skills/query-strategies/SKILL.md](../sub-skills/query-strategies/SKILL.md) |
| `modAL.disagreement` | committee vote/consensus/KL disagreement and `max_std_sampling` | [../sub-skills/query-strategies/SKILL.md](../sub-skills/query-strategies/SKILL.md) with learner setup in [../sub-skills/learners-and-committees/SKILL.md](../sub-skills/learners-and-committees/SKILL.md) |
| `modAL.batch` | ranked batch active-learning helpers and `uncertainty_batch_sampling` | [../sub-skills/query-strategies/SKILL.md](../sub-skills/query-strategies/SKILL.md) |
| `modAL.expected_error` | `expected_error_reduction` | [../sub-skills/query-strategies/SKILL.md](../sub-skills/query-strategies/SKILL.md) |
| `modAL.density` | `information_density`, `similarize_distance` | [../sub-skills/query-strategies/SKILL.md](../sub-skills/query-strategies/SKILL.md) |
| `modAL.multilabel` | SVM-oriented multilabel active-learning strategies | [../sub-skills/query-strategies/SKILL.md](../sub-skills/query-strategies/SKILL.md) |
| `modAL.acquisition` | PI/EI/UCB acquisition score functions and max-selection wrappers | [../sub-skills/bayesian-optimization/SKILL.md](../sub-skills/bayesian-optimization/SKILL.md) |
| `modAL.dropout` | PyTorch/skorch Monte Carlo dropout query helpers | [../sub-skills/deep-and-optional-integrations/SKILL.md](../sub-skills/deep-and-optional-integrations/SKILL.md) |
| `modAL.utils` | data stacking/retrieval, selection helpers, utility combinators, validation helpers | Usually [../sub-skills/query-strategies/SKILL.md](../sub-skills/query-strategies/SKILL.md); data-shape issues also appear in [../sub-skills/learners-and-committees/SKILL.md](../sub-skills/learners-and-committees/SKILL.md) |

## Core workflow shape

A classical modAL workflow has four moving parts:

1. An estimator implementing the relevant scikit-learn methods (`fit`, `predict`, and often `predict_proba`).
2. A learner/committee wrapper that stores active-learning state.
3. A query strategy callable that scores the unlabeled pool.
4. A loop that queries rows, obtains labels or objective values from an external oracle, then calls `teach`.

For active learning, the oracle is outside modAL. The package selects samples; it does not obtain ground-truth labels, call a labeling platform, or manage annotation cost accounting by itself.

## Optional boundaries

- `DeepActiveLearner` expects skorch-like estimators with `initialize()` and `partial_fit()` behavior.
- `modAL.dropout` imports PyTorch and skorch utilities. CPU tensors are enough for API inspection and small checks; CUDA requires a separately installed backend and smoke test.
- Legacy Keras/TensorFlow examples are examples only in this generated skill. They are not minimum dependencies and often require dataset downloads.
- There is no command-line interface in this package snapshot. Use Python APIs and bundled smoke scripts.

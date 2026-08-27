---
name: modal
description: "Guides modAL-python active-learning workflows, query strategies,
  committees, Bayesian optimization, and optional deep integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# modAL repo skill

Use this skill when a task names `modAL`, `modAL-python`, `ActiveLearner`, `Committee`, `BayesianOptimizer`, active learning, uncertainty sampling, query by committee, ranked batch selection, expected error reduction, label-efficient model development, or optional modAL deep-learning integrations.

modAL is imported as `modAL` but installed from the package distribution `modAL-python`. It is a scikit-learn-oriented active-learning framework; most core workflows are CPU-only and do not require a GPU.

## Start here

1. Read [references/repo-provenance.md](references/repo-provenance.md) when deciding whether this skill matches a source checkout or package version.
2. Read [references/package-overview.md](references/package-overview.md) for the public module map, dependency boundaries, and which optional integrations are intentionally not minimum installs.
3. If install/import or dependency compatibility is uncertain, read [references/troubleshooting.md](references/troubleshooting.md) and run [scripts/modal_environment_smoke.py](scripts/modal_environment_smoke.py).

Minimal package check for a user environment:

```bash
python -m pip install modAL-python
python - <<'PY'
from importlib.metadata import version
import modAL
from modAL.models import ActiveLearner, Committee, CommitteeRegressor, BayesianOptimizer
print("modAL-python", version("modAL-python"), "import ok")
PY
```

For the historical `0.4.2` code covered by this skill, modern dependency resolvers may pick versions that are too new. If imports fail with `np.float`, `force_all_finite`, or `pkg_resources` errors, use the compatibility guidance in [references/troubleshooting.md](references/troubleshooting.md).

## Route by task

| Task signal | Read |
|---|---|
| Pool-based or stream-based active learning, `ActiveLearner.query`, `teach`, `fit`, single-row shapes, `only_new`, `bootstrap`, `on_transformed` | [sub-skills/learners-and-committees/SKILL.md](sub-skills/learners-and-committees/SKILL.md) |
| Query by committee, `Committee`, `CommitteeRegressor`, `vote`, `vote_proba`, `predict_proba`, `rebag`, regression standard deviation | [sub-skills/learners-and-committees/SKILL.md](sub-skills/learners-and-committees/SKILL.md) |
| Choosing or composing uncertainty, disagreement, batch, density, expected-error, multilabel, selector, or custom query strategies | [sub-skills/query-strategies/SKILL.md](sub-skills/query-strategies/SKILL.md) |
| `BayesianOptimizer`, PI/EI/UCB acquisition functions, bounded objective-evaluation loops, or `get_max()` tracking | [sub-skills/bayesian-optimization/SKILL.md](sub-skills/bayesian-optimization/SKILL.md) |
| `DeepActiveLearner`, skorch/PyTorch estimators, MC dropout, `modAL.dropout`, Keras/TensorFlow examples, or optional backend imports | [sub-skills/deep-and-optional-integrations/SKILL.md](sub-skills/deep-and-optional-integrations/SKILL.md) |

## Operating rules

- Treat modAL strategies as callables. A learner's `query` method calls `query_strategy(self, X_pool, **kwargs)` and returns selected indices plus the selected rows; metrics are available only when the strategy returns them.
- For classical active learning, start with a fitted scikit-learn estimator or pass `X_training` and `y_training` so modAL can fit during learner initialization.
- Use probability-based strategies only with estimators that implement `predict_proba`; route regression uncertainty to regressors that provide predictive standard deviation or to committee-regressor disagreement.
- Preserve row shapes when teaching queried samples. For NumPy data, a single queried sample normally needs `X_pool[idx].reshape(1, -1)` and `y_pool[idx].reshape(1,)`.
- Keep optional deep workflows explicit. The core modAL active-learning workflow is CPU-friendly; Keras/TensorFlow examples and CUDA-specific behavior require separate installation and smoke checks.
- Do not rely on original repository examples or tests at runtime. This skill bundles runnable smoke helpers under `scripts/` and sub-skill `scripts/` directories.

## Bundled checks

Run these from any current working directory in an environment with modAL installed:

```bash
python path/to/modal/scripts/modal_environment_smoke.py
python path/to/modal/scripts/modal_environment_smoke.py --include-optional-deep
```

Sub-skills contain deeper workflow-specific smoke helpers:

- [sub-skills/learners-and-committees/scripts/active_learning_smoke.py](sub-skills/learners-and-committees/scripts/active_learning_smoke.py)
- [sub-skills/learners-and-committees/scripts/committee_smoke.py](sub-skills/learners-and-committees/scripts/committee_smoke.py)
- [sub-skills/query-strategies/scripts/query_strategy_smoke.py](sub-skills/query-strategies/scripts/query_strategy_smoke.py)
- [sub-skills/bayesian-optimization/scripts/bayesian_optimizer_smoke.py](sub-skills/bayesian-optimization/scripts/bayesian_optimizer_smoke.py)
- [sub-skills/deep-and-optional-integrations/scripts/dropout_inspection.py](sub-skills/deep-and-optional-integrations/scripts/dropout_inspection.py)

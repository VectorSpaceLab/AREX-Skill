---
name: pomegranate
description: "Guides pomegranate probabilistic modeling workflows:
  distributions, mixture models, Bayesian classifiers, Bayesian networks, factor
  graphs, HMMs, Markov chains, KMeans, and PyTorch-backed training features."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pomegranate

## Use this skill when

Use this repo skill when a task needs package-specific guidance for pomegranate v1.x probabilistic modeling: distribution fitting/scoring, mixture models, Bayesian classifiers, Bayesian networks, factor graphs, hidden Markov models, Markov chains, KMeans initialization/clustering, missing values, priors, out-of-core updates, or PyTorch device/dtype behavior.

Pomegranate v1.x is a PyTorch-backed rewrite. Prefer current imports such as `from pomegranate.distributions import Normal` and `from pomegranate.hmm import DenseHMM`; do not rely on pre-v1 Cython-era names such as `NormalDistribution`, `HiddenMarkovModel`, `State`, `Node`, or `bake`.

## Install and import check

For a published install, use:

```bash
python -m pip install pomegranate
```

For a local checkout of this package, use:

```bash
python -m pip install -e .
```

Then verify imports with the bundled helper:

```bash
python scripts/check_env.py
# optional CUDA allocation check when a CUDA torch build is installed:
python scripts/check_env.py --cuda
```

Core dependencies are `numpy`, `scipy`, `scikit-learn`, `torch`, `apricot-select`, and `networkx`. There are no repository-defined console entry points; use the Python APIs directly.

## Route by task

| User task or signal | Read next |
| --- | --- |
| Fit, score, sample, weight, freeze, or compose individual distributions such as `Normal`, `Categorical`, `ConditionalCategorical`, `Gamma`, `Poisson`, `IndependentComponents`, or `ZeroInflated` | [sub-skills/distributions/SKILL.md](sub-skills/distributions/SKILL.md) |
| Build unsupervised mixture models, Gaussian or heterogeneous mixtures, Bayes classifiers, posterior probabilities, or prior-weighted component inference | [sub-skills/mixtures-and-classifiers/SKILL.md](sub-skills/mixtures-and-classifiers/SKILL.md) |
| Build Bayesian networks, run factor-graph inference, learn categorical network structures, or impute discrete missing values from graph evidence | [sub-skills/graph-models/SKILL.md](sub-skills/graph-models/SKILL.md) |
| Work with Markov chains, dense/sparse HMMs, sequence likelihoods, variable-length sequence batches, Baum-Welch fitting, posterior decoding, or Viterbi | [sub-skills/sequence-models/SKILL.md](sub-skills/sequence-models/SKILL.md) |
| Use pomegranate `KMeans` as a standalone clusterer or as an initialization helper for probabilistic models | [sub-skills/clustering/SKILL.md](sub-skills/clustering/SKILL.md) |
| Need a compact class-to-subskill map before routing | [references/model-catalog.md](references/model-catalog.md) |
| Need missing-value, GPU, mixed precision, priors, out-of-core, serialization, or `torch.compile` behavior | [references/feature-guide.md](references/feature-guide.md) |
| Encounter install, import, legacy API, shape, dtype, masked tensor, or backend errors | [references/troubleshooting.md](references/troubleshooting.md) and the nearest sub-skill troubleshooting file |
| Need to check whether this skill matches a repository version | [references/repo-provenance.md](references/repo-provenance.md) |

## Common API pattern

Most pomegranate models either subclass `torch.nn.Module` directly or subclass the pomegranate `Distribution` abstraction. Expect these recurring methods where implemented:

- `fit(...)` performs one-shot training, often by calling `summarize(...)` followed by `from_summaries()`.
- `summarize(...)` accumulates sufficient statistics for mini-batch or out-of-core updates.
- `from_summaries()` applies accumulated statistics and resets caches.
- `probability(...)` and `log_probability(...)` score complete examples.
- Composite models add `predict(...)`, `predict_proba(...)`, and `predict_log_proba(...)` for posterior assignments or missing-value inference.

Use `check_data=False` only when inputs are already known to satisfy the documented shapes and ranges, or when following `torch.compile` guidance. Otherwise leave validation enabled while debugging.

## Guardrails

- Keep current v1.x import paths and class names in generated code.
- Move both model and tensors to the same PyTorch device before using CUDA.
- Use `torch.masked.MaskedTensor` for missing values where supported; read the feature guide first because not every distribution supports missingness.
- Treat optional GPU and mixed-precision workflows as PyTorch-device workflows, not pomegranate-specific installs.
- Do not tell users to run original repository notebooks or tests as runtime steps. Use the bundled smoke scripts and references instead.

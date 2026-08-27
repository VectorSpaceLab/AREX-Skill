---
name: aix360
description: "Routes AIX360 explainability tasks across local black-box
  attribution, counterfactuals and certification, interpretable models,
  time-series explanations, datasets, and explanation-quality metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AIX360

Use this repository skill for AI Explainability 360 (`aix360`) workflows over
tabular, text, image, and time-series data. It covers package version 0.3.0,
including modern CPU-usable routes and explicit boundaries around historical
TensorFlow/Keras and other optional dependency stacks.

AIX360 is a toolkit, not one universal explainer. First identify:

1. whether the artifact to explain is **data**, an already-trained **black-box
   model**, or a **directly interpretable model** to fit;
2. whether the requested result is **local**, **global**, **counterfactual**,
   **certified**, or a **quality metric**;
3. the input domain and model-callable output shape;
4. constraints on actions, downloads, hardware, latency, and optional packages.

## Installation and inspection

Use an isolated environment because AIX360 extras pin mutually incompatible
versions for some algorithm families.

```bash
python -m pip install aix360
python -c "import aix360; from importlib.metadata import version; print(version('aix360'))"
```

Install only the extra for the chosen workflow, for example:

```bash
python -m pip install 'aix360[lime]'
python -m pip install 'aix360[tslime]'
python -m pip install 'aix360[rbm]'
```

Do not install every extra into one environment. In particular, CEM/ProfWeight
and historical SHAP paths pin TensorFlow 1.14 with Keras 2.3.1, whereas
nearest-neighbor contrastive pins TensorFlow 2.9.3; keep incompatible families
in separate environments. Read [installation and runtime
troubleshooting](references/troubleshooting.md) before changing versions.

Run the bundled [environment diagnostic](scripts/check_environment.py) to
inspect the base package and selected optional modules without downloading data
or models.

## Route by task

### Local black-box attribution and examples

Read [local-black-box](sub-skills/local-black-box/SKILL.md) for LIME, SHAP,
Grouped Conditional Expectation, nearest-neighbor contrastive examples,
faithfulness, monotonicity, prediction-callable contracts, feature names, and
local explanation output validation.

Typical signals: `explain_instance`, `predict_proba`, local feature weights,
SHAP values, tabular/text/image attribution, exemplar/nearest-neighbor
explanation, or local metric debugging.

### Counterfactuals, recourse, certification, and matching

Read [counterfactual-and-certification](sub-skills/counterfactual-and-certification/SKILL.md)
for CEM/CEM-MAF pertinent positives and negatives, Ecertify trust regions,
GLANCE recourse/action costs, and order-constrained optimal-transport matching.

Typical signals: target class, actionable or immutable features, feature bounds,
recourse, robustness certificate, perturbation budget, `OTMatchingExplainer`, or
legacy CEM model setup.

### Directly interpretable models, rules, and prototypes

Read [interpretable-models](sub-skills/interpretable-models/SKILL.md) for
ProtoDash, Boolean/linear rule models, RIPPER/TRXF, interpretable model
differencing, teaching explanations, and optional CoFrNet, DIPVAE, and
ProfWeight workflows.

Typical signals: prototype selection, `FeatureBinarizer`, BRCG/GLRM, rule
induction, model comparison, explanation labels, directly interpretable
training, solver errors, graph export, or rule serialization.

### Time-series explanations

Read [time-series](sub-skills/time-series/SKILL.md) for TSICE, TSLime, and
TSSaliency over univariate or multivariate histories, including forecast
lookahead, relevant history, exogenous variables, perturbation windows, data
shapes, and numeric-versus-plot output.

Typical signals: temporal attribution, integrated gradients, local surrogate,
forecast window, time axis, feature axis, perturbation count, or exogenous
series alignment.

### Datasets, preprocessing, and explanation metrics

Read [datasets-and-metrics](sub-skills/datasets-and-metrics/SKILL.md) for AIX360
dataset constructors, local data layout, offline checks, preprocessing, and
Faithfulness/Monotonicity metrics.

Typical signals: HELOC, COMPAS, CDC, MEPS, Ford, Sunspots, CIFAR, MNIST,
CelebA, e-SNLI, missing dataset paths, downloads, coefficient alignment, or
explanation-quality evaluation.

## Cross-route decisions

- Use dataset and metric guidance as support for any algorithm route, but keep
  explainer construction with the algorithm-owning sub-skill.
- Prefer a callable whose batch input and output shape are explicit; many local
  explainers fail because a classifier returns labels instead of probabilities
  or a time-series forecaster drops its batch axis.
- Treat notebook-scale image training, remote datasets, pretrained weights, and
  graph rendering as opt-in operations. The bundled skill defaults to tiny,
  local, deterministic checks.
- Verify whether an explanation is local/global and post-hoc/direct before
  comparing methods. Their outputs are not interchangeable.
- A successful `import aix360` proves only the base package. Import the selected
  algorithm module and run a tiny fixture before trusting an optional route.

Read [API and method overview](references/api-overview.md) when the user names an
algorithm but not its route. Read [repository provenance](references/repo-provenance.md)
before deciding whether this skill is stale for another checkout.

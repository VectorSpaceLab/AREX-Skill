---
name: pgmpy
description: "Route pgmpy causal and probabilistic graphical-model tasks to
  focused modeling, learning, inference, causal, data I/O, and extension
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pgmpy

Use this repo skill when the task names pgmpy or asks for Python workflows around causal graphs, Bayesian networks, Markov networks, conditional probability distributions, structure learning, probabilistic inference, causal identification/effect estimation, example graphical models, model file formats, or pgmpy extension work.

pgmpy is a Python package for causal and probabilistic reasoning with graphical models. It provides graph/model classes, CPDs and factors, causal discovery, parameter estimation, inference, sampling/simulation, causal identification and prediction, datasets/example models, metrics, and read/write utilities.

## First checks

- Install/use pgmpy with Python 3.10-3.14. For package use, start with `pip install pgmpy` or `conda install conda-forge::pgmpy`.
- For local repository maintenance, prefer `pip install -e .[tests]` and focused `pytest` targets. Do not commit or push from an agent session.
- Optional surfaces require explicit extras: `pgmpy[torch]` for `FunctionalBayesianNetwork`/`FunctionalCPD`; `pgmpy[optional]` for plotting, xgboost, and LLM-assisted discovery dependencies. Provider credentials/network are still separate requirements.
- To verify an installed package without source checkout access, run `python scripts/check_pgmpy_environment.py --json` from the skill root. Add `--check-optional` only when optional imports matter.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) before refreshing this skill for a changed checkout.
- Read [`references/package-map.md`](references/package-map.md) when choosing between canonical modules, legacy compatibility imports, optional extras, and public entry points.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import, optional dependency, state-name, network/cache, and package-version issues before diving into a sub-skill.

## Route by task

| User task | Read |
|---|---|
| Build a DAG, PDAG, ADMG, MAG, BN, DBN, Markov network, factor graph, CPD, or factor; debug `check_model()` or CPD shapes. | [`modeling-and-factors`](sub-skills/modeling-and-factors/SKILL.md) |
| Learn graph structure, choose PC/GES/HillClimb/Chow-Liu/TAN, select CI tests or scores, use expert knowledge, or fit CPDs from data. | [`learning-structure-and-parameters`](sub-skills/learning-structure-and-parameters/SKILL.md) |
| Query posterior probabilities, run MAP, use Variable Elimination or Belief Propagation, sample/simulate from a fitted model, or work with DBN inference. | [`inference-sampling-and-simulation`](sub-skills/inference-sampling-and-simulation/SKILL.md) |
| Identify adjustment/frontdoor sets, use `CausalInference.query(..., do=...)`, estimate ATE, or use causal prediction regressors. | [`causal-identification-and-effects`](sub-skills/causal-identification-and-effects/SKILL.md) |
| Load/list built-in datasets or example models, save/load BIF/XMLBIF/NET/UAI/XDSL files, or compute graph/data evaluation metrics. | [`data-io-and-evaluation`](sub-skills/data-io-and-evaluation/SKILL.md) |
| Add a new causal discovery algorithm, CI test, score, metric, dataset, or example model to a pgmpy checkout. | [`extending-pgmpy`](sub-skills/extending-pgmpy/SKILL.md) |

## Routing rules and boundaries

1. If the user only needs a graph object with roles and no CPDs, start in `modeling-and-factors`; do not force a Bayesian-network model.
2. If the user has data and wants a learned graph or learned CPDs, route to `learning-structure-and-parameters`, then back to `modeling-and-factors` only for model-family construction details.
3. If the user asks for `P(Y | X=x)`, posterior marginals, MAP, or sampling under evidence, route to `inference-sampling-and-simulation`. If they ask for `do(X=x)`, ATE, adjustment, frontdoor, instruments, or treatment effects, route to `causal-identification-and-effects`.
4. If a workflow begins by loading `bnlearn/alarm`, a dataset name, or a `.bif`/`.uai`/`.xmlbif` file, route first to `data-io-and-evaluation`, then to the workflow that consumes the loaded object.
5. Prefer canonical packages for new code: `pgmpy.causal_discovery`, `pgmpy.parameter_estimator`, `pgmpy.structure_score`, `pgmpy.ci_tests`, `pgmpy.metrics`, `pgmpy.datasets`, and `pgmpy.example_models`. Treat `pgmpy.estimators` as a legacy compatibility surface unless the task is explicitly maintaining backwards compatibility.
6. Do not treat optional torch/Pyro functional models, LLM-assisted discovery, plotting backends, or remote HuggingFace-backed assets as verified unless the user environment explicitly has the needed extras, credentials, network/cache, and hardware.

## Common package facts

- Core CPU workflows use NetworkX, NumPy, SciPy, pandas, scikit-learn, statsmodels, tqdm, pyparsing, joblib, opt_einsum, scikit-base, and HuggingFace Hub helpers.
- `BayesianNetwork` and `MarkovNetwork` are deprecated aliases for `DiscreteBayesianNetwork` and `DiscreteMarkovNetwork`.
- Most user-facing algorithms expose sklearn-like constructors and `fit(...)`; fitted discovery results are typically available as `causal_graph_` and `adjacency_matrix_`.
- Model validation is not optional. Run `check_model()` before inference, simulation, serialization, or causal queries on parameterized models.
- Use `show_progress=False` in automated examples/tests unless progress bars are explicitly useful.

## Safe validation

For a quick installed-package check:

```bash
python scripts/check_pgmpy_environment.py --json
```

For workflow-specific checks, use the nearest bundled script:

- `modeling-and-factors/scripts/check_modeling_smoke.py`
- `learning-structure-and-parameters/scripts/learn_structure_smoke.py`
- `inference-sampling-and-simulation/scripts/inference_smoke.py`
- `causal-identification-and-effects/scripts/causal_effect_smoke.py`
- `data-io-and-evaluation/scripts/data_io_smoke.py`
- `extending-pgmpy/scripts/extension_template_check.py`

These scripts are deterministic, no-network by default, and do not require the original repository checkout except `extension_template_check.py`, which is intentionally a checkout-maintenance helper and requires `--repo` when run away from the checkout.

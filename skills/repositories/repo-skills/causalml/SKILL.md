---
name: causalml
description: "Use CausalML for causal inference, uplift modeling, matching,
  validation, interpretation, and treatment optimization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# causalml

Use this repo skill when the task names CausalML or needs Python operating guidance for causal effect estimation, uplift modeling, propensity/matching, causal trees, optional neural causal models, validation metrics, sensitivity analysis, feature selection, or treatment decision optimization.

## Install and environment check

For normal package use, install the package and only the optional extras needed by the requested workflow:

```bash
pip install causalml
pip install "causalml[tf]"      # TensorFlow DragonNet only when needed
pip install "causalml[torch]"   # Torch/Pyro CEVAE only when needed
pip install "causalml[jax]"     # JAX DragonNet/CEVAE only when needed
```

When working from a source checkout, use the equivalent editable install such as `pip install -e .` or `pip install -e ".[tf,torch,jax]"` from that checkout.

After installation, run the bundled diagnostic from this skill tree if import status is uncertain:

```bash
python scripts/check_env.py
python scripts/check_env.py --backend tf --backend jax
python scripts/check_env.py --backend all --json
```

The diagnostic checks core imports and only checks optional backends that are explicitly requested.

## Route by workflow

| Task | Open |
| --- | --- |
| Synthetic data, feature matrix preparation, propensity scores, matching, balance tables, CSV matching | [sub-skills/data-preparation/](sub-skills/data-preparation/) |
| S/T/X/R/DR meta-learners, TMLE, IV/DRIV, estimator API contracts, Polars/DataFrame support, persistence | [sub-skills/causal-estimation/](sub-skills/causal-estimation/) |
| Causal trees, causal forests, uplift trees, uplift forests, tree plots, tree save/load, compiled tree import issues | [sub-skills/tree-models/](sub-skills/tree-models/) |
| TensorFlow DragonNet, Torch/Pyro CEVAE, JAX DragonNet, JAX CEVAE, deep-backend setup and smoke checks | [sub-skills/deep-models/](sub-skills/deep-models/) |
| AUUC/Qini/RATE/validation metrics, sensitivity analysis, feature selection, SHAP/importances, policy/value optimization, PNS bounds | [sub-skills/analysis-and-decision/](sub-skills/analysis-and-decision/) |

Start at the most specific sub-skill. Return here only when routing across workflows or diagnosing cross-cutting install/import failures.

## Operating defaults

1. Prefer keyword arguments for estimator calls: `fit(X=X, treatment=treatment, y=y, ...)`. Positional argument order is migration-sensitive in current CausalML.
2. Keep `control_name` explicit whenever treatment labels are strings or multi-arm.
3. Treat propensity scores as probabilities strictly inside `(0, 1)`; clip extreme scores before X/R/DR/TMLE, validation, and matching workflows when appropriate.
4. For multi-treatment CATE arrays, use the learner's treatment-group metadata (`t_groups` or `_classes`) rather than guessing column order.
5. For metrics and policy workflows, separate model prediction columns from feature columns. Many metrics treat every non-reserved column as a model score.
6. Do not rely on old documentation references to `causalml.inference.nn`; current neural models route through `causalml.inference.tf`, `causalml.inference.torch`, or `causalml.inference.jax`.
7. CPU execution is sufficient for small correctness and wiring checks. Do not claim GPU/accelerator behavior unless the selected backend stack has been installed and verified separately.

## Cross-cutting references

- [references/troubleshooting.md](references/troubleshooting.md): install/import, optional dependency, Graphviz/OpenMP, argument-order, backend, and stale-API issues.
- [references/repo-provenance.md](references/repo-provenance.md): source commit, package version, evidence paths, selected coverage, and refresh triggers.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json): structured router scenario metadata for managed repo-skill import.

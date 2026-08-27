---
name: causal-identification-and-effects
description: "Guides pgmpy causal graph role annotations, identification,
  do-queries, ATE, and causal effect regressors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Causal Identification and Effects

Use this sub-skill when the user asks for causal, interventional, or treatment-effect work in pgmpy: role-aware causal graphs, adjustment/frontdoor identification, `CausalInference.query(..., do=...)`, `CausalInference.estimate_ate`, or sklearn-style causal effect regressors from `pgmpy.prediction`.

## Route First

- **Identify before estimating.** Start with a graph carrying at least `exposures` and `outcomes`; identify or validate `adjustment`/`frontdoor` roles before making effect claims.
- **For `P(Y | do(X=x))`, ATE, adjustment, frontdoor, IV, or DML:** stay here and read [references/workflows.md](references/workflows.md).
- **For ordinary posterior `P(Y | X=x)` without intervention:** route to the sibling inference/sampling skill instead of using causal terminology.
- **For discovering the graph from data:** route to the sibling structure-learning skill, then return here after the graph is accepted.
- **For basic CPDs, factors, or Bayesian-network construction:** route to the sibling modeling/factors skill.

## What to Read

- [references/causal-api.md](references/causal-api.md) — role names, supported classes, signatures, estimator inputs, and data assumptions.
- [references/workflows.md](references/workflows.md) — copyable recipes for adjustment, frontdoor, do-queries, ATE, and `pgmpy.prediction` regressors.
- [references/troubleshooting.md](references/troubleshooting.md) — symptoms and fixes for missing roles, non-identifiability, data-column mismatches, do/evidence confusion, numeric/categorical issues, and IV role mistakes.
- [scripts/causal_effect_smoke.py](scripts/causal_effect_smoke.py) — safe installed-package smoke test for adjustment identification, frontdoor identification, ATE, and a causal regressor.

## Operating Checklist

1. Confirm the requested estimand: observational posterior, interventional distribution, ATE, CATE-style prediction, or IV-style effect estimation.
2. Confirm graph roles and graph type. `Adjustment` needs `exposures` and `outcomes`; `NaiveIVRegressor` specifically needs singular role `instrument`.
3. Run identification/validation (`Adjustment` or `Frontdoor`) before fitting regressors or reporting effect estimates.
4. Confirm data columns exactly match role variable names and that regressor inputs are numeric.
5. Validate with the smoke script when adapting a new environment or when role/data mismatches are suspected:

```bash
python sub-skills/causal-identification-and-effects/scripts/causal_effect_smoke.py --help
python sub-skills/causal-identification-and-effects/scripts/causal_effect_smoke.py
```

## Guardrails

- Do not claim causal identification from data alone; pgmpy's effect APIs assume the supplied causal graph is defensible.
- Do not treat `evidence={"X": x}` as `do={"X": x}`. Evidence conditions on observations; `do` intervenes.
- Do not use ordinary predictive accuracy as proof of causal validity. It can verify code execution, not the causal assumptions.
- Do not use deprecated legacy backdoor/frontdoor helpers when the `pgmpy.identification.Adjustment` or `Frontdoor` API covers the task.

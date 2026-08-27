---
name: model-selection
description: "Choose and configure StatsForecast model classes and direct model APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Model selection

Use this sub-skill to pick a StatsForecast model class, confirm constructor knobs, and call the direct array API on a model object.

## Use this when
- choosing between automatic, manual statistical, baseline, intermittent, volatility, machine-learning, or fallback model classes
- checking constructor highlights, aliases, exogenous support, interval support, or simulation support
- using direct `fit`, `predict`, `forecast`, `forward`, `predict_in_sample`, or `simulate` methods on a model object

## Route elsewhere
- panel orchestration, `StatsForecast`, `X_df`, cross-validation, persistence, or distributed execution -> [core-forecasting](../core-forecasting/SKILL.md)
- MSTL feature decomposition or feature generation -> [feature-engineering](../feature-engineering/SKILL.md)
- local or distributed backend routing -> [distributed-execution](../distributed-execution/SKILL.md)

## Bundled references
- [Model catalog](references/model-catalog.md)
- [API reference](references/model-api-reference.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled script
- [model_catalog.py](scripts/model_catalog.py)

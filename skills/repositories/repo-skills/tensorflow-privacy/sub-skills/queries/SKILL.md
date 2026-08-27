---
name: queries
description: "Routes TensorFlow Privacy users who need low-level DPQuery stacks,
  query composition, quantile clipping helpers, or tree aggregation mechanics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Queries

Use this sub-skill when the user needs to work directly with TensorFlow Privacy's `DPQuery` family or its tree-aggregation helpers.

## Trigger phrases

- "custom DPQuery"
- "Gaussian query"
- "discrete Gaussian"
- "Skellam query"
- "normalized query"
- "nested query"
- "quantile adaptive clipping"
- "restart query"
- "tree aggregation"

## What this sub-skill covers

- `DPQuery` and `SumAggregationDPQuery`
- Gaussian, discrete-Gaussian, distributed discrete-Gaussian, and Skellam query classes
- `NoPrivacy*` and `NormalizedQuery` helpers
- nested queries and restart indicators
- quantile estimator and quantile-adaptive clipping query classes
- tree aggregation query helpers and the lower-level `tree_aggregation` module

## What it does not cover

- privacy budgets or epsilon/noise search -> `../privacy-accounting/`
- training loops or model wrappers -> `../training/`
- membership inference and secret-sharer analysis -> `../privacy-tests/`
- fast gradient clipping internals -> `../fast-clipping/`

## Read this before you act

- `references/api-reference.md` for class constructors, helper signatures, and the safe query smoke pattern.
- `references/troubleshooting.md` for nesting, state, and restart failures.
- `../../references/install-and-scope.md` for the minimum CPU runtime.

## Typical workflow

1. Decide whether the user needs a turn-key query or a custom nested composition.
2. Pick the narrowest query class that matches the desired mechanism.
3. Use `test_utils.run_query()` when you need a tiny deterministic smoke check.
4. If the user is actually asking for privacy accounting, route them to `privacy-accounting` instead of building a query by hand.

## Bundled helper

Run `scripts/tiny_dp_query_smoke.py` for a tiny deterministic query check. It exercises a Gaussian sum query and a no-privacy sum query on a scalar toy fixture.

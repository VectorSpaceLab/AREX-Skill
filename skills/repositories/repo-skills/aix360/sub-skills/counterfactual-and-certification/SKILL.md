---
name: counterfactual-and-certification
description: "Use AIX360 for contrastive CEM/CEM-MAF explanations, black-box
  certification, GLANCE recourse, and order-constrained optimal-transport
  matching."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Counterfactual and certification

Use this route when the request is about a contrastive explanation, a
pertinent positive or negative, actionable recourse, a robustness/trust-region
certificate, or an alternative matching under transport/order constraints.
The route covers AIX360 0.3.0 APIs; it does not promise that every optional
backend can be installed in the current environment.

## Route by goal

- **CEM / CEM-MAF**: image or array contrastive explanations. A pertinent
  positive (PP) retains the minimum sufficient content for the original class;
  a pertinent negative (PN) is added content whose presence changes the class.
  Use the API and legacy-backend caveats in [api-reference.md](references/api-reference.md).
- **Ecertify**: certify a scalar quality/fidelity callable in a neighborhood of
  one instance. This is black-box, query-budgeted, and probabilistic/empirical;
  it is not an exhaustive proof over arbitrary data domains.
- **GLANCE**: generate local counterfactuals or global subgroup actions for a
  binary tabular model. Make favorable class `1`, numeric/categorical columns,
  immutable features, and the cost definition explicit before fitting.
- **OTMatching**: produce alternative transport plans and salient changed
  positions while preserving row/column marginals within the configured error
  tolerance. The matching and costs must already be prepared by the caller.

## Do not route here

- LIME, SHAP, GroupedCE, or nearest-neighbor contrastive explanations go to
  [../local-black-box/SKILL.md](../local-black-box/SKILL.md).
- Rules, prototypes, IMD, or TED go to
  [../interpretable-models/SKILL.md](../interpretable-models/SKILL.md).
- Time-series explanations go to
  [../time-series/SKILL.md](../time-series/SKILL.md).
- Dataset-loader ownership and download lifecycle go to
  [../datasets-and-metrics/SKILL.md](../datasets-and-metrics/SKILL.md).

## Required inputs

Before invoking an algorithm, record:

1. The input representation and shape, target/favorable class, and the model
   prediction interface.
2. Which features or pixels may change, hard lower/upper bounds, and whether
   categorical changes, monotonic directions, or immutable columns must be
   enforced outside the algorithm.
3. The expected output: counterfactual array, action table, certificate width,
   or list of matching alternatives; also record the acceptance test.
4. Optional-dependency and network policy. Never start a model, image, GAN,
   embedding, or dataset download as an implicit side effect.

## Safe decision flow

1. Validate shapes, dtypes, finite values, class semantics, and constraints
   with a tiny local fixture. For GLANCE, apply candidate actions and re-run
   the model; for matching, check non-negativity and marginal sums.
2. Prefer the CPU-oriented GLANCE action/cost primitives, a small synthetic
   Ecertify quality function, or a tiny transport plan for verification.
3. Treat contrastive image execution as optional until the TensorFlow 1.x and
   Keras stack, model assets, and input preprocessing have been independently
   confirmed. Do not substitute a modern TensorFlow result for that historical
   path.
4. Treat a returned candidate as a proposal: re-predict it, check bounds and
   actionability, and report fewer-than-requested or no-solution outcomes.
5. Summarize approximation, random seeds, query budgets, dependency failures,
   and unverified paths with the result.

## Output and handoff

Return the requested artifact together with the input shape, target/favorable
class, constraint policy, model-output adapter, dependency status, and a
post-call validation result. Distinguish a valid candidate from a failed or
empty search. For a certificate, include width, strategy, query budget, and
confidence interpretation; for GLANCE, include effectiveness and cost
semantics; for matching, include marginal residuals and salient positions.

See [api-reference.md](references/api-reference.md) for signatures and output
contracts, [workflows.md](references/workflows.md) for no-network recipes, and
[troubleshooting.md](references/troubleshooting.md) for recovery boundaries.

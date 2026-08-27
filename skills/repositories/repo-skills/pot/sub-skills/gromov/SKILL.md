---
name: gromov
description: "Use POT Gromov-Wasserstein and Fused GW solvers for graphs,
  structured data, heterogeneous spaces, GW barycenters, dictionary learning,
  quantized approximations, and validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# POT Gromov-Wasserstein and Fused GW

Use this sub-skill when the task involves comparing or aligning objects whose samples live in different metric spaces or have graph/relational structure: Gromov-Wasserstein (GW), Fused Gromov-Wasserstein (FGW), structured graph matching, node-feature-aware graph comparison, GW/FGW barycenters, dictionary learning/unmixing, semirelaxed/partial/unbalanced variants, quantized approximations, and GW validation.

Read [references/api-reference.md](references/api-reference.md) when choosing a POT GW API, checking verified signatures/defaults, understanding `ot.solve_gromov` versus `ot.gromov.*`, or validating expected plan/log/result fields.

Read [references/workflows.md](references/workflows.md) when building an end-to-end GW or FGW workflow for graphs, node features, heterogeneous spaces, barycenters, dictionary learning, or approximate/quantized GW.

Read [references/troubleshooting.md](references/troubleshooting.md) when cost matrices, weights, `loss_fun`/`loss`, `alpha`, marginal constraints, `symmetric`, partial/semirelaxed/unbalanced semantics, convergence, quantized helpers, or optional GNN dependencies fail.

Run [scripts/gromov_smoke.py](scripts/gromov_smoke.py) after installing POT to exercise deterministic NumPy GW and FGW fixtures with no plotting, downloads, original checkout, or optional graph dependencies.

## Route quickly

- Use **GW** when each object is represented only by an internal structure matrix (`C1`, `C2`), such as pairwise graph distances, adjacency-derived dissimilarities, shape geodesics, or relational similarities.
- Use **FGW** when structures also have cross-space attributes or node features. Provide a feature cost matrix `M` of shape `(n_source, n_target)` and tune `alpha`: `0` emphasizes features/linear OT and `1` emphasizes pure GW structure.
- Use **`ot.solve_gromov`** for a unified `OTResult` with `.plan`, `.value`, `.value_linear`, `.value_quad`, and marginal helpers. Use **`ot.gromov.*`** functions when you need a specific classical, entropic, semirelaxed, partial, quantized, barycenter, dictionary, or estimator API.
- Use **entropic GW/FGW** when exact conditional-gradient plans are too slow or too sparse and a smoother approximation is acceptable.
- Use **semirelaxed GW/FGW** when the source marginal is fixed but the target-side mass may be reweighted, for example matching a graph to a prototype or community structure.
- Use **partial GW/FGW** when only a known amount of mass should match, such as subgraph matching with outliers.
- Use **fused unbalanced GW** when marginal masses should be penalized rather than enforced. Route general unbalanced/partial OT fundamentals to `unbalanced-partial`.
- Use **quantized, sampled, pointwise, or low-rank GW** when graph/sample sizes make full GW too expensive; validate the approximation on a reduced problem before trusting ranking or downstream decisions.
- Use **GW/FGW barycenters** when the output is itself a structure matrix or an attributed graph prototype. Route ordinary Wasserstein barycenters to `barycenters`.
- Use **dictionary learning/unmixing** when many structured samples should be represented as convex combinations of learned GW/FGW atoms.
- Treat **POT GNN layers** (`ot.gnn`) as optional reference-only functionality unless the user's environment has PyTorch and PyTorch Geometric installed and verified. Route backend installation and batch-array issues to `backend-and-batch`.

## Stay in scope

This sub-skill owns structured GW/FGW modeling, solver selection, validation, and workflow-specific recovery. It does not cover ordinary vector-space OT except as the `M` term inside FGW; route those tasks to `core-solvers`. It does not teach general mass-relaxation theory outside GW/FGW; route that to `unbalanced-partial`. It does not install optional backend stacks, PyTorch Geometric, plotting, NetworkX, or scikit-learn; route setup questions to `backend-and-batch` or keep them explicitly optional.

## Minimal operating checklist

1. Build finite floating-point square structure matrices `C1` and `C2`; normalize scales when comparing multiple costs.
2. If using FGW, build `M` with shape `(C1.shape[0], C2.shape[0])` from comparable node-feature distances.
3. Set one-dimensional nonnegative weights `p` and `q` whose lengths match the structure matrices, or let POT use uniform weights.
4. Choose the mass model: balanced GW/FGW, semirelaxed target reweighting, partial transported mass, or unbalanced marginal penalty.
5. Run the solver with explicit `loss_fun`/`loss`, `alpha`, `reg`, `symmetric`, `max_iter`, and `tol` when reproducibility matters.
6. Validate the returned plan: finite nonnegative values, expected shape, total mass, row/column marginal behavior for the selected mass model, and a finite GW/FGW value.
7. For larger graphs, compare an approximate/quantized result against a tiny exact subset or the bundled smoke script before scaling up.

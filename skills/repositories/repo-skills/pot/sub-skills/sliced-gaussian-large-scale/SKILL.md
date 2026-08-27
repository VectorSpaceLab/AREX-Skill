---
name: sliced-gaussian-large-scale
description: "Fast structured POT alternatives for sliced, Gaussian, GMM,
  low-rank, BSP, stochastic, semidiscrete, SGOT, COOT, and other large-scale
  optimal transport workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# POT sliced, Gaussian, and large-scale alternatives

Use this sub-skill when a POT task asks for a faster or more structured alternative to dense exact optimal transport: sliced or spherical sliced Wasserstein distances and plans, Gaussian or GMM Bures-Wasserstein maps and plans, low-rank/Nystroem/factored approximations, BSP bijections, stochastic or semidiscrete solvers, SGOT, COOT, or one-dimensional DMMOT-style barycenter notes.

Read [references/api-reference.md](references/api-reference.md) when checking verified signatures, default parameters, input shapes, return values, and module ownership for sliced, Gaussian/GMM, and large-scale APIs.

Read [references/workflows.md](references/workflows.md) when replacing dense OT with sliced approximations, controlling projection variance, building sliced transport plans, using spherical sliced distances, or validating a large-problem approximation against a tiny baseline.

Read [references/gaussian-gmm.md](references/gaussian-gmm.md) when inputs are Gaussian means/covariances or GMM component parameters and the goal is a Bures distance, affine Gaussian map, GMM component plan, GMM map, density, or family-level barycenter without discretizing samples.

Read [references/large-scale-solvers.md](references/large-scale-solvers.md) when selecting among low-rank Sinkhorn, Nystroem kernels, factored OT, BSP-OT, semidiscrete OT, stochastic dual solvers, SGOT, COOT, and DMMOT notes for larger or structured problems.

Read [references/troubleshooting.md](references/troubleshooting.md) when sliced estimates vary by seed, covariance or GMM shapes fail, optional low-rank/BSP dependencies are missing, stochastic settings diverge, or memory usage grows unexpectedly.

Run [scripts/sliced_gaussian_smoke.py](scripts/sliced_gaussian_smoke.py) with `python scripts/sliced_gaussian_smoke.py --mode all` to check a local POT install against deterministic tiny sliced, Gaussian, GMM, and low-rank fixtures before adapting these workflows.

## Route quickly

- Random projections or high-dimensional samples: prefer `ot.sliced.sliced_wasserstein_distance`, `ot.sliced.max_sliced_wasserstein_distance`, spherical variants, or `ot.solve_sample(..., method="sliced" | "max_sliced")` when a scalar approximation is enough.
- Approximate plans from projections: use `ot.sliced.min_sliced_transport_plan` or `ot.sliced.expected_sliced_plan`; validate plan mass and treat projection count/seed as approximation controls.
- Gaussian parameters: use `ot.gaussian.bures_wasserstein_distance`, `ot.gaussian.bures_wasserstein_mapping`, high-dimensional Gaussian helpers, or Bures barycenters.
- GMM parameters: use `ot.gmm.gmm_ot_plan`, `ot.gmm.gmm_ot_loss`, `ot.gmm.gmm_ot_apply_map`, and `ot.gmm.gmm_barycenter_fixed_point` to avoid sample discretization.
- Large sample clouds: compare `ot.lowrank.lowrank_sinkhorn`, `ot.solve_sample(..., method="lowrank" | "nystroem" | "factored" | "bsp")`, `ot.factored.factored_optimal_transport`, and `ot.bsp.compute_bspot_bijection` against a tiny dense baseline before scaling.
- Structured matrix/operator tasks: use semidiscrete OT for continuous-to-atomic maps, stochastic dual solvers for mini-batch regularized OT, SGOT for spectral operators, COOT for row/feature alignment, and DMMOT only for one-dimensional grid multi-marginal barycenter-style problems.

## Boundaries

Route balanced exact EMD/Sinkhorn fundamentals, cost-matrix construction basics, and generic `OTResult` usage to `core-solvers`. Route domain adaptation estimator classes to `domain-adaptation`. Route backend installation, mixed backend arrays, GPU claims, and batch solvers to `backend-and-batch`. This sub-skill documents large-scale and structured alternatives; it does not claim optional-backend or GPU verification beyond the NumPy-backed evidence summarized here.

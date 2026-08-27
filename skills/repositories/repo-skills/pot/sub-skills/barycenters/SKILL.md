---
name: barycenters
description: "Fixed-support, free-support, entropic, debiased, convolutional,
  and sample-cloud Wasserstein barycenter workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# POT barycenters

Use this sub-skill when a task asks for a Wasserstein barycenter on a fixed grid, a moving/free support barycenter, a debiased or convolutional image barycenter, or a sample-cloud barycenter with POT.

Read [references/api-reference.md](references/api-reference.md) when choosing the correct barycenter API, checking signatures, or validating shapes and return fields.

Read [references/workflows.md](references/workflows.md) when deciding between fixed-support histograms, free-support point clouds, convolutional images, and `solve_bary_sample` workflows.

Read [references/troubleshooting.md](references/troubleshooting.md) when barycenters have unexpected mass, convergence warnings, shape errors, LP solver issues, or confusing sample-cloud behavior.

Run [scripts/barycenter_smoke.py](scripts/barycenter_smoke.py) to check a local POT install against deterministic tiny barycenter fixtures before adapting a workflow.

## Route quickly

- Shared histogram grid: use `ot.bregman.barycenter` for entropic barycenters, `ot.bregman.barycenter_debiased` when entropic blur is a concern, or `ot.lp.barycenter` for tiny exact LP barycenters.
- Moving support with explicit point-cloud measures: use `ot.lp.free_support_barycenter` for exact 2-Wasserstein support updates or `ot.bregman.free_support_sinkhorn_barycenter` for entropic support updates.
- Unequal-size sample clouds where the barycenter support itself must be optimized: use `ot.solvers.solve_bary_sample` and inspect its `BaryResult`.
- Image stacks on a regular grid: use `ot.bregman.convolutional_barycenter2d` or `ot.bregman.convolutional_barycenter2d_debiased`.
- Graph/structured GW or FGW barycenters belong in the `gromov` sub-skill. Gaussian and GMM barycenters belong primarily in the `sliced-gaussian-large-scale` sub-skill, with only cross-link notes here.

## Stay in scope

This sub-skill covers barycenter setup, shape validation, convergence recovery, and tiny self-checks. It does not teach core EMD/Sinkhorn theory, Gromov-Wasserstein barycenter internals, or Gaussian/GMM distribution-family modeling beyond routing hints.

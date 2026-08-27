---
name: unbalanced-partial
description: "Use POT unbalanced and partial optimal transport solvers when
  masses may differ, outliers should be ignored, or only part of the mass should
  move."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# POT unbalanced and partial optimal transport

Use this sub-skill when a POT task is about relaxed marginals, unequal total mass, explicit transported mass, outlier rejection, unbalanced barycenters, or regularization paths for unbalanced OT.

## Route the request

- Read [references/api-reference.md](references/api-reference.md) when choosing between `ot.unbalanced.*`, `ot.partial.*`, `ot.regpath.*`, and unified `ot.solve(..., unbalanced=...)` APIs or when checking signatures, return shapes, and parameter meanings.
- Read [references/workflows.md](references/workflows.md) when implementing an end-to-end recipe: compare UOT against partial OT for outliers, stabilize entropic partial OT, build an unbalanced barycenter, use 1D helpers, or sample an L2-UOT regularization path.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a plan has unexpected mass, `m` is infeasible, `reg`/`reg_m` are confused, a divergence name is rejected, small entropic regularization produces NaNs, or optional backend behavior is unclear.
- Run [scripts/unbalanced_partial_smoke.py](scripts/unbalanced_partial_smoke.py) after installing POT to check deterministic NumPy UOT/partial/barycenter/regpath behavior; the legacy `--include-optional-uot-1d` flag attempts the optional autodiff-backed 1D UOT check and records a structured skip when that backend is unavailable.

## Boundaries

This sub-skill owns unbalanced and partial OT semantics: `sinkhorn_unbalanced`, `sinkhorn_unbalanced2`, `mm_unbalanced`, `lbfgsb_unbalanced`, `uot_1d`, `barycenter_unbalanced`, `partial_wasserstein`, `entropic_partial_wasserstein`, `partial_wasserstein_1d`, unbalanced/partial GW routing notes, and `ot.regpath` L2-UOT paths.

Route balanced exact OT, balanced Sinkhorn basics, distance matrix construction basics, and `OTResult` fundamentals to `core-solvers`. Route detailed Gromov-Wasserstein and fused GW modeling to `gromov`. Route sliced high-dimensional UOT variants and Gaussian/GMM approximations to `sliced-gaussian-large-scale`. Route optional backend installation, batch solvers, and mixed-array backend issues to `backend-and-batch`.

## Operating checklist

1. Validate that weights are one-dimensional, nonnegative, finite, and aligned with the rows/columns of the cost matrix.
2. Decide the mass model: UOT relaxes marginal constraints with `reg_m`/`unbalanced`; partial OT fixes transported mass with `m`.
3. Scale or inspect the cost matrix before choosing `reg` and `reg_m`; the same numeric parameters mean different things after cost rescaling.
4. Validate the returned plan: shape `(len(a), len(b))`, finite nonnegative entries, transported mass, and row/column sums appropriate to UOT or partial constraints.
5. For entropic partial OT at small `reg`, prefer `method="sinkhorn_log"` and confirm finite output plus `plan.sum() ≈ m`.

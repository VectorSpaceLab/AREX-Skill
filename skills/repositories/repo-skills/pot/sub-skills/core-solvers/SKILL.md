---
name: core-solvers
description: "Use POT core solvers for exact and regularized optimal transport
  on cost matrices or sample clouds, including unified APIs, EMD, Sinkhorn, 1D,
  circle, sparse, lazy helpers, and OTResult validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# POT Core Solvers

Use this sub-skill when the task is balanced discrete optimal transport between histograms or sample clouds: exact network-simplex OT, entropic or L2 regularized OT, `ot.solve`, `ot.solve_sample`, `ot.emd`/`emd2`, `ot.sinkhorn`/`sinkhorn2`, cost construction with `ot.dist`, uniform weights with `ot.unif`, and `OTResult` inspection.

For verified signatures, return objects, solver routing, weight conventions, sparse/lazy support, gradient modes, and parameter defaults, read [references/api-reference.md](references/api-reference.md).

For copy-pasteable recipes that convert between classical and unified APIs, validate `OTResult` attributes, handle sample-cloud workflows, and run 1D/circle/sparse/lazy checks, read [references/workflows.md](references/workflows.md).

For failure diagnosis covering mass mismatch, invalid weights, too-small regularization, invalid methods, compiled EMD import/build issues, `n_threads`/OpenMP caveats, sparse matrices, and gradient memory, read [references/troubleshooting.md](references/troubleshooting.md).

To verify a tiny deterministic installation-level core-solver path without plotting or external data, run [scripts/core_solver_smoke.py](scripts/core_solver_smoke.py) with `python scripts/core_solver_smoke.py --mode all`.

Route barycenters to `barycenters`, GW/FGW to `gromov`, unbalanced or partial OT workflows to `unbalanced-partial`, optional backend installation and batched arrays to `backend-and-batch`, and large-scale approximation families such as sliced, Gaussian, low-rank, Nystroem, factored, or BSP-heavy workflows to `sliced-gaussian-large-scale` unless this task only needs to recognize the `solve_sample` entry point.

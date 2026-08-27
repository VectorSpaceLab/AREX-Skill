---
name: pot
description: "Use POT/Python Optimal Transport for optimal-transport solvers,
  Wasserstein distances, Sinkhorn, Gromov-Wasserstein, barycenters, unbalanced
  or partial OT, domain adaptation, Gaussian/GMM and backend-aware scientific ML
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# POT (Python Optimal Transport)

Use this repo skill when a task involves POT, the `ot` import package, optimal transport, Wasserstein distances, Sinkhorn solvers, transport plans, cost matrices, Gromov-Wasserstein, unbalanced or partial mass transport, barycenters, sliced/Gaussian/GMM OT, OT domain adaptation, or POT's NumPy/PyTorch/JAX/TensorFlow/CuPy backend behavior.

## Start here

1. Install or verify POT. The distribution is `POT`, but code imports `ot`.
2. Run [scripts/check_pot_install.py](scripts/check_pot_install.py) when you need a fast base-package check for import, compiled extensions, and a tiny NumPy solve.
3. Read [references/package-overview.md](references/package-overview.md) for package concepts, install routes, optional extras, and a solver-family map.
4. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, compiled-extension, optional-dependency, mixed-backend, and numerical-scale issues.
5. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout.

## Sub-skill routes

| If the user asks about... | Read |
| --- | --- |
| Exact OT, Wasserstein distance, `ot.solve`, `ot.solve_sample`, EMD/EMD2, Sinkhorn, cost matrices, 1D/circle/sparse/lazy solvers, or `OTResult` | [sub-skills/core-solvers/SKILL.md](sub-skills/core-solvers/SKILL.md) |
| Fixed-support or free-support barycenters, entropic/debiased/convolutional barycenters, or sample-cloud barycenters | [sub-skills/barycenters/SKILL.md](sub-skills/barycenters/SKILL.md) |
| Gromov-Wasserstein, Fused GW, semirelaxed/partial/unbalanced/quantized GW, graph/relational alignment, GW barycenters, or GW dictionary learning | [sub-skills/gromov/SKILL.md](sub-skills/gromov/SKILL.md) |
| Unbalanced OT, partial OT, outlier mass, relaxed marginals, transported mass `m`, UOT barycenters, or regularization paths | [sub-skills/unbalanced-partial/SKILL.md](sub-skills/unbalanced-partial/SKILL.md) |
| Sliced/max/spherical sliced Wasserstein, Gaussian/Bures/GMM OT, low-rank/factored/Nystroem/BSP/semidiscrete/SGOT/COOT/stochastic solvers, or large-scale approximation choices | [sub-skills/sliced-gaussian-large-scale/SKILL.md](sub-skills/sliced-gaussian-large-scale/SKILL.md) |
| OT domain adaptation estimators, mapping transport, source/target sample alignment, JCPOT, WDA/EWCA optional routes, or nearest Brenier potentials | [sub-skills/domain-adaptation/SKILL.md](sub-skills/domain-adaptation/SKILL.md) |
| NumPy/Torch/JAX/TensorFlow/CuPy backends, mixed-backend errors, optional backend checks, gradient modes, or batch OT solvers | [sub-skills/backend-and-batch/SKILL.md](sub-skills/backend-and-batch/SKILL.md) |

## Minimal install and smoke check

```bash
pip install POT
python - <<'PY'
import ot
print(ot.__version__)
PY
python scripts/check_pot_install.py --json
```

The base install should support NumPy/SciPy workflows plus compiled extensions used by exact EMD, partial OT, and BSP-OT. Optional extras are task-specific; do not install `POT[all]` unless the user explicitly wants all optional packages and accepts licensing/runtime implications.

## Solver-family decision hints

- Use `ot.solve(M, ...)` when the user already has a cost matrix and wants a unified result object.
- Use `ot.solve_sample(Xs, Xt, ...)` when the user has samples and wants POT to compute the cost matrix or choose sample-specific methods.
- Use classical functions such as `ot.emd`, `ot.emd2`, `ot.sinkhorn`, and `ot.sinkhorn2` when the user needs the historical API or a specific solver.
- Use unbalanced or partial APIs when total mass should not be fully conserved.
- Use GW/FGW APIs when source and target samples live in different spaces but have internal distance/feature structures.
- Use sliced, Gaussian/GMM, low-rank, lazy, stochastic, semidiscrete, or batch routes before building huge dense cost/plan matrices.
- Use optional backend routes only after the active environment verifies the corresponding framework.

## Validation checklist

For every POT workflow, check:

- Input arrays are finite, shaped as documented, and use one numerical backend per solver call.
- Histograms are nonnegative and aligned with cost-matrix rows/columns.
- Cost matrix scale matches the chosen `reg`, `reg_m`, tolerance, and approximation family.
- Returned plans are finite, nonnegative within tolerance, and have expected shape/mass/marginals.
- Result objects expose the values needed by the task (`value`, `value_linear`, `value_quad`, `plan`, `potentials`, `X`, `b`, or `log`).
- Any optional backend, plotting, CVX, DR, GNN, or GeomLoss path is installed and verified in the environment that will run it.

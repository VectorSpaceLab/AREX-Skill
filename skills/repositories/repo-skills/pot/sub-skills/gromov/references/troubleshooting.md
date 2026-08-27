# POT GW/FGW Troubleshooting

## Purpose

Read this when a GW/FGW workflow fails, converges slowly, returns surprising mass, or needs optional graph/GNN dependencies. Start by running the bundled smoke script from this sub-skill directory:

```bash
python scripts/gromov_smoke.py --mode all
```

If the smoke script fails at import time, fix the POT installation before diagnosing solver parameters.

## Failure matrix

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'ot'` or `ImportError` while importing POT | POT is not installed in the active Python environment. | Install the public POT package in the environment that will run the workflow, then rerun `python scripts/gromov_smoke.py --mode all`. Do not rely on a source checkout being present. |
| `ModuleNotFoundError: No module named 'torch'` while importing `ot.gnn` | Optional GNN route requires PyTorch. | Treat GNN as optional. Install and verify PyTorch/PyTorch Geometric only if the user requested GNN layers; otherwise stay with NumPy GW/FGW APIs. |
| Warning that `torch_geometric` is not installed | `ot.gnn` utilities require PyTorch Geometric for graph neural network layers. | Route setup to `backend-and-batch`; then verify `import torch`, `import torch_geometric`, and `import ot.gnn` before using `TFGWPooling` or `TWPooling`. |
| `Not implemented GW loss="..."` from `ot.solve_gromov` | Unified API uses `loss='L2'` or `loss='KL'`, not classical `loss_fun`. | Change to `loss='L2'` or `loss='KL'`. If using `ot.gromov.*`, use `loss_fun='square_loss'` or `loss_fun='kl_loss'`. |
| `ValueError` from helper initialization with unknown loss | Classical `loss_fun` is neither `square_loss` nor `kl_loss`. | Use `loss_fun='square_loss'` for squared differences or `loss_fun='kl_loss'` for KL-style loss. |
| `Unknown unbalanced_type` or `Not implemented reg_type` | Unsupported combination in `ot.solve_gromov`. | Check the route table in `api-reference.md`. For partial GW use `unbalanced_type='partial'`; for semirelaxed use `unbalanced_type='semirelaxed'`; for entropy use `reg_type='entropy'`. |
| `Partial GW mass given in unbalanced is too large` or `ValueError` for `m` | Partial transported mass exceeds available mass or is negative. | Choose `m` with `0 <= m <= min(sum(p), sum(q))`. In `ot.solve_gromov`, partial mass is passed as `unbalanced=m`. In classical partial APIs, use `m=m`. |
| Assertion or failure around `G0` / initial plan marginals | Warm-start coupling does not satisfy the selected marginal constraints. | For balanced GW/FGW, set `G0 = np.outer(p, q)` or validate `G0.sum(1) ≈ p` and `G0.sum(0) ≈ q`. For partial, validate total mass and upper-bound marginals. For semirelaxed, validate source rows only. |
| Plan row/column sums do not match both weights | The selected variant is not balanced, or convergence tolerance was too loose. | For balanced GW/FGW, row sums should match `p` and column sums should match `q`. For semirelaxed, only source rows are fixed. For partial, total mass is fixed and row/column sums are bounded. For unbalanced, deviations are penalized. |
| FGW result ignores node features | `alpha` is too close to `1`, `M` is missing, `M` is incorrectly shaped, or feature distances are badly scaled. | Check `M.shape == (len(p), len(q))`. Normalize `M`, `C1`, and `C2` to comparable scales. Sweep `alpha`; smaller `alpha` emphasizes `M`. |
| GW result ignores graph structure | `alpha` is too close to `0` in FGW or the call accidentally routes to ordinary OT on `M`. | Increase `alpha` toward `1`. If using `ot.solve_gromov`, remember `alpha=0` is the ordinary linear OT route and `alpha=1` is pure GW. |
| Confusing `alpha` behavior in fused unbalanced GW | Lower-level `ot.gromov.fused_unbalanced_gromov_wasserstein` uses `alpha` as the linear-cost coefficient, unlike `ot.solve_gromov`, where `alpha` weights the GW quadratic term. | Prefer `ot.solve_gromov` for unified behavior. If directly calling FUGW, document the alpha convention and validate against a tiny sweep. |
| `C1`/`C2` shape errors or nonsensical values | Structure matrices are not square, finite, or aligned with weights. | Assert `C1.shape == (len(p), len(p))`, `C2.shape == (len(q), len(q))`, finite floating dtype, and no unintended integer casting. |
| Solver is slow or hits iteration budget | GW/FGW is nonconvex and expensive; costs may be poorly scaled; symmetry check or dense exact route may be costly. | Normalize costs, set `symmetric=True` when valid, start with smaller graphs, use `max_iter`/`tol` deliberately, warm-start with a valid plan, try entropic GW/FGW, or use quantized/sampled approximations. |
| Entropic GW/FGW plan is too diffuse | `epsilon` or `reg` is too large for the cost scale. | Lower `epsilon`/`reg`, but watch for underflow and slow convergence. Compare marginal errors and task-specific accuracy, not only the objective. |
| Entropic solver produces numerical warnings or unstable values | `epsilon`/`reg` too small, costs too large, or weights include zeros/near-zeros. | Rescale costs to `[0, 1]`, remove zero-mass nodes where appropriate, increase `epsilon`/`reg`, and validate finite plan entries. |
| `symmetric=True` gives wrong answer on directed/asymmetric graphs | Matrices are not symmetric but the solver was told to use symmetric gradients. | Set `symmetric=False` for directed adjacency, asymmetric costs, or nonreciprocal relations. If in doubt, test with `np.allclose(C, C.T)`. |
| `symmetric=None` is slow on repeated calls | POT checks symmetry each call. | Precompute whether both structures are symmetric and pass `symmetric=True` or `False` explicitly. |
| Integer inputs produce zeroed or low-precision plans | Some GW functions cast computed plans to the dtype of provided inputs. | Convert `C1`, `C2`, `M`, `p`, and `q` to floating arrays before solving. |
| Quantized helper silently uses poor partitions | Optional NetworkX/scikit-learn methods are missing, or fallback to `random` happened. | For reproducible minimum-dependency runs, set `part_method='random'`, `rep_method='random'`, and `random_state`. For graph-quality partitions, install and verify the optional dependencies, then compare against exact small cases. |
| Quantized helper errors that fused methods need feature matrices | A `*_fused` partition/representant method or `alpha != 1` was requested without `F1`/`F2`. | Provide feature matrices `F1` and `F2` with matching feature dimensions, or set `alpha=1` and use non-fused partition/representant methods. |
| `Unknown part_method` or `Unknown rep_method` | Unsupported quantized partition or representant name. | Use supported partition names such as `random`, `louvain`, `fluid`, `spectral`, `GW`, `FGW` where implemented by the chosen helper; use representant names such as `random` or `pagerank`. If optional packages are not verified, prefer `random`. |
| Barycenter raises `unknown stop criterion` | `stop_criterion` must be one of the supported names. | Use `stop_criterion='barycenter'` or `stop_criterion='loss'`. |
| Barycenter output cannot be plotted as a graph | GW barycenters produce structure/dissimilarity matrices, not necessarily adjacency matrices. | Treat thresholding, embedding, or graph reconstruction as a separate modeling step and validate it against the downstream task. |
| Dictionary learning is too slow or unstable | Too many atoms/nodes, high `epochs`, or expensive inner GW iterations. | Prototype with small `D`, `nt`, `epochs`, `batch_size`, and inner iteration limits. Set `random_state` and validate reconstruction errors before scaling. |
| Optional backend arrays behave differently from NumPy | Minimum verified backend for this generated skill is NumPy only; backend-specific gradients/devices were not verified here. | Reproduce the tiny NumPy result first, then route optional backend setup and mixed-array issues to `backend-and-batch`. Do not mix NumPy and tensor backends in one call unless POT backend conversion is intentional. |

## Mass-model diagnostics

Use these assertions after every solve. Adjust tolerances for large or entropic problems.

```python
import numpy as np

assert T.shape == (len(p), len(q))
assert np.isfinite(T).all()
assert T.min() >= -1e-10

# Balanced GW/FGW
np.testing.assert_allclose(T.sum(axis=1), p, atol=1e-5)
np.testing.assert_allclose(T.sum(axis=0), q, atol=1e-5)

# Semirelaxed GW/FGW
np.testing.assert_allclose(T.sum(axis=1), p, atol=1e-5)
print("learned target mass", T.sum(axis=0))

# Partial GW/FGW
np.testing.assert_allclose(T.sum(), m, atol=1e-5)
assert np.all(T.sum(axis=1) <= p + 1e-8)
assert np.all(T.sum(axis=0) <= q + 1e-8)

# Unbalanced GW/FGW
print("row deviation", np.linalg.norm(T.sum(axis=1) - p, ord=1))
print("column deviation", np.linalg.norm(T.sum(axis=0) - q, ord=1))
```

## Cost and feature validation snippet

```python
import numpy as np

def validate_gw_inputs(C1, C2, p=None, q=None, M=None):
    C1 = np.asarray(C1, dtype=float)
    C2 = np.asarray(C2, dtype=float)
    assert C1.ndim == C2.ndim == 2
    assert C1.shape[0] == C1.shape[1]
    assert C2.shape[0] == C2.shape[1]
    assert np.isfinite(C1).all() and np.isfinite(C2).all()
    if p is not None:
        p = np.asarray(p, dtype=float)
        assert p.ndim == 1 and p.shape[0] == C1.shape[0]
        assert (p >= 0).all() and np.isfinite(p).all()
    if q is not None:
        q = np.asarray(q, dtype=float)
        assert q.ndim == 1 and q.shape[0] == C2.shape[0]
        assert (q >= 0).all() and np.isfinite(q).all()
    if M is not None:
        M = np.asarray(M, dtype=float)
        assert M.shape == (C1.shape[0], C2.shape[0])
        assert np.isfinite(M).all()
    return C1, C2, p, q, M
```

## When to stop and reroute

- If the task is only exact or Sinkhorn OT between points in the same vector space, route to `core-solvers`.
- If the task is primarily mass relaxation, partial OT, or unbalanced Wasserstein outside GW/FGW, route to `unbalanced-partial`.
- If the task needs CUDA/PyTorch/JAX/TensorFlow/CuPy installation, PyTorch Geometric, or batched array solvers, route to `backend-and-batch`.
- If a quantized or stochastic approximation changes the downstream decision compared with a tiny exact check, do not scale it up until the user accepts the approximation trade-off.

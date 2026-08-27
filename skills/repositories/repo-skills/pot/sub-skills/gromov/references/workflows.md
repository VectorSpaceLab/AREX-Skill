# POT GW/FGW Workflows

## Purpose

Read this reference when implementing a GW/FGW workflow end to end: build structure matrices, choose GW versus FGW, select exact/entropic/semirelaxed/partial/unbalanced/quantized variants, and validate the resulting coupling. The examples are self-contained and use only public POT APIs.

## Start with a smoke check

From this sub-skill directory, run:

```bash
python scripts/gromov_smoke.py --mode all
```

Expected signal: the script reports finite GW/FGW values, valid coupling shapes, and balanced marginal errors below the selected tolerance. Use `--json` when a downstream tool needs machine-readable output.

## Workflow 1: balanced GW for structures without shared features

Use GW when the two objects do not live in the same vector space or when the geometry is entirely internal to each object.

```python
import numpy as np
import ot

# Four-node path-like structures. Replace these with graph distances,
# shortest-path matrices, geodesic distances, or similarity-derived costs.
x1 = np.arange(4.0)[:, None]
x2 = np.array([0.0, 1.0, 2.2, 3.0])[:, None]
C1 = np.abs(x1 - x1.T)
C2 = np.abs(x2 - x2.T)
C1 /= C1.max()
C2 /= C2.max()

p = ot.unif(C1.shape[0])
q = ot.unif(C2.shape[0])

res = ot.solve_gromov(C1, C2, a=p, b=q, loss="L2", symmetric=True, max_iter=200, tol=1e-9)
T = res.plan

assert T.shape == (C1.shape[0], C2.shape[0])
assert np.isfinite(T).all() and (T >= -1e-12).all()
np.testing.assert_allclose(T.sum(axis=1), p, atol=1e-5)
np.testing.assert_allclose(T.sum(axis=0), q, atol=1e-5)
print(float(res.value), float(res.value_quad))
```

Classical equivalent:

```python
T, log = ot.gromov.gromov_wasserstein(
    C1, C2, p, q, loss_fun="square_loss", symmetric=True, log=True,
    max_iter=200, tol_rel=1e-9, tol_abs=1e-9,
)
print(log["gw_dist"])
```

Validation checklist:

1. `C1` and `C2` are square and finite.
2. Costs are comparable after normalization.
3. `T` has shape `(ns, nt)`.
4. For balanced GW, `T.sum(1) ≈ p` and `T.sum(0) ≈ q`.
5. `res.value` or `log['gw_dist']` is finite.
6. If changing backends, compare a tiny NumPy result before trusting gradients or GPU behavior.

## Workflow 2: choose GW versus FGW for graphs with node features

Use this decision table before coding:

| Task signal | Use | Inputs |
| --- | --- | --- |
| Graphs only; no node attributes or attributes are not comparable | GW | `C1`, `C2`, `p`, `q` |
| Graph topology plus comparable node labels/features | FGW | `M`, `C1`, `C2`, `p`, `q`, `alpha` |
| Only node features matter | Ordinary OT on `M` | Route to `core-solvers`, or set `alpha=0` in `ot.solve_gromov` only when staying inside an FGW sweep. |
| Structure should dominate but features break symmetries | FGW with high `alpha` | Try `alpha` such as `0.7`, `0.9`, `0.95`. |
| Features should dominate but graph consistency matters | FGW with low `alpha` | Try `alpha` such as `0.1`, `0.3`, `0.5`. |

Self-contained FGW pattern:

```python
import numpy as np
import ot

# Same structure, reversed labels: GW alone is ambiguous; FGW can use features.
C1 = np.abs(np.arange(4.0)[:, None] - np.arange(4.0)[None, :])
C2 = C1.copy()
C1 /= C1.max()
C2 /= C2.max()

F1 = np.array([[0.0], [0.0], [1.0], [1.0]])
F2 = F1[::-1].copy()
M = ot.dist(F1, F2)
if M.max() > 0:
    M /= M.max()

p = q = ot.unif(4)

for alpha in [0.1, 0.5, 0.9]:
    res = ot.solve_gromov(C1, C2, M=M, a=p, b=q, alpha=alpha, loss="L2", symmetric=True)
    print(alpha, float(res.value), float(res.value_linear), float(res.value_quad))
```

Interpretation:

- `alpha=0` reduces to a linear OT problem on `M`.
- `alpha=1` ignores `M` and reduces to GW.
- Intermediate `alpha` values trade feature matching and structure matching.
- Inspect both `value_linear` and `value_quad` from `OTResult`; a lower total value can hide a worse feature or structure component.

## Workflow 3: exact versus entropic GW/FGW

Start with exact conditional-gradient GW/FGW on tiny or medium problems when sparsity and interpretability matter. Switch to entropic when plans are too sparse, iterations are slow, or a smoother differentiable-ish objective is useful.

```python
T_exact, log_exact = ot.gromov.gromov_wasserstein(C1, C2, p, q, log=True, symmetric=True)
T_ent, log_ent = ot.gromov.entropic_gromov_wasserstein(
    C1, C2, p, q, epsilon=0.05, solver="PGD", log=True, symmetric=True,
)
print(log_exact["gw_dist"], log_ent["gw_dist"])
```

Practical controls:

- `epsilon`: larger values produce smoother but more biased plans.
- `solver`: `PGD` is the verified default; `PPA` is commonly used for proximal Sinkhorn-style iterations.
- `max_iter`, `tol`: increase `max_iter` only after checking cost scale and weights.
- `G0`: warm-start from a previous alpha/reg setting only if it satisfies the relevant marginal constraints.

## Workflow 4: semirelaxed, partial, and unbalanced variants

Use this selection matrix:

| Variant | Call pattern | Plan mass behavior | Use case |
| --- | --- | --- | --- |
| Balanced GW/FGW | `ot.solve_gromov(C1, C2, M=None or M)` | rows `≈ p`, columns `≈ q` | Full matching of two structures. |
| Semirelaxed GW/FGW | `ot.solve_gromov(C1, C2, M, unbalanced_type="semirelaxed")` or `ot.gromov.semirelaxed_*` | source rows fixed; target columns are learned | Match a graph to a smaller/larger prototype or community template. |
| Partial GW/FGW | `ot.solve_gromov(..., unbalanced_type="partial", unbalanced=m)` or `ot.gromov.partial_*` | total transported mass fixed at `m`; row/column sums bounded | Subgraph matching or outlier rejection with known clean mass. |
| Fused unbalanced GW | `ot.solve_gromov(..., unbalanced=rho, unbalanced_type="KL" or "L2")` | marginal deviations penalized | Unknown mass mismatch where a soft penalty is preferable to fixed `m`. |

Partial FGW sketch:

```python
m = 0.75 * min(p.sum(), q.sum())
T, log = ot.gromov.partial_fused_gromov_wasserstein(
    M, C1, C2, p, q, m=m, alpha=0.5, log=True, symmetric=True,
)
assert T.sum() <= min(p.sum(), q.sum()) + 1e-8
np.testing.assert_allclose(T.sum(), m, atol=1e-5)
```

Semirelaxed sketch:

```python
T, log = ot.gromov.semirelaxed_gromov_wasserstein(C1, C2, p, log=True, symmetric=True)
np.testing.assert_allclose(T.sum(axis=1), p, atol=1e-5)
print("learned target weights", T.sum(axis=0))
```

For general UOT interpretation (`reg_m`, KL versus L2 divergences, partial OT outside GW), route to `unbalanced-partial`.

## Workflow 5: quantized or approximate GW for larger graphs

Full GW/FGW is quadratic/nonconvex over all pairwise structural relations. For larger graphs, use a staged approximation and validate the trade-off.

### Approximation choices

| Scale problem | Candidate route | Validation |
| --- | --- | --- |
| Need a quick graph-level distance and can cluster nodes | `quantized_fused_gromov_wasserstein` | Compare exact GW/FGW on a small induced subgraph; check ranking stability across `random_state` and partition counts. |
| Already have partitions/representants | `quantized_fused_gromov_wasserstein_partitioned` | Validate local/global mass sums and that partitions cover all nodes. |
| Point clouds, not explicit graph matrices | `quantized_fused_gromov_wasserstein_samples` or `lowrank_gromov_wasserstein_samples` | Compare against exact sample subset; track `rank`, `npart`, and seed. |
| Need stochastic estimates with custom loss | `pointwise_gromov_wasserstein` or `sampled_gromov_wasserstein` | Inspect estimated distance and variance fields in logs. |
| Dense exact plan is slow but problem is small enough | entropic GW/FGW | Sweep `epsilon`; compare plan marginals and task metric. |

### Quantized graph pattern

```python
T_global, Ts_local, T, log = ot.gromov.quantized_fused_gromov_wasserstein(
    C1, C2,
    npart1=4, npart2=4,
    p=p, q=q,
    F1=None, F2=None,
    alpha=1.0,             # qGW; lower than 1 uses features and requires F1/F2
    part_method="random",  # no optional graph dependency required
    rep_method="random",
    log=True,
    random_state=0,
)
```

If NetworkX or scikit-learn is installed and verified, graph-aware partition methods such as `louvain`, `fluid`, `pagerank`, `spectral`, and `kmeans` may be appropriate. Without those optional dependencies, prefer `random` in reproducible smoke checks and document that the graph partitioning quality was not verified.

### Approximation acceptance criteria

A cheap approximation is acceptable only when at least one of these checks passes:

1. On a reduced graph/sample subset, exact and approximate distances rank a set of candidate targets the same way.
2. A downstream classifier/clustering/alignment metric is stable across at least two seeds or partition counts.
3. Marginal and total-mass errors are within task tolerance, and logs show finite values.
4. The user explicitly accepts the approximation as a screening step rather than a final metric.

## Workflow 6: GW/FGW barycenters

Use GW barycenters for prototype structure matrices and FGW barycenters for attributed prototypes.

```python
Cs = [C1, C2]
ps = [p, q]
N = 4
p_bar = ot.unif(N)
C_bar = ot.gromov.gromov_barycenters(
    N, Cs, ps=ps, p=p_bar, lambdas=[0.5, 0.5],
    loss_fun="square_loss", symmetric=True, max_iter=50, tol=1e-7,
    random_state=0,
)
assert C_bar.shape == (N, N)
```

FGW barycenter pattern:

```python
Ys = [F1, F2]
X_bar, C_bar, log = ot.gromov.fgw_barycenters(
    N=4, Ys=Ys, Cs=Cs, ps=ps, lambdas=[0.5, 0.5], alpha=0.5,
    p=ot.unif(4), log=True, max_iter=20, tol=1e-7, random_state=0,
)
```

Validation:

- `C_bar` is square and finite.
- Feature barycenter `X_bar` has expected node count and feature dimension.
- If the barycenter is intended to become a graph, thresholding distances into adjacency is a modeling step; validate it separately.
- `stop_criterion` should be `barycenter` or `loss`; unknown values raise errors.

## Workflow 7: dictionary learning and unmixing

Use GW/FGW dictionary learning when many graphs or structures should be encoded as convex combinations of learned atoms.

```python
Cdict, log = ot.gromov.gromov_wasserstein_dictionary_learning(
    Cs=Cs,
    D=3,
    nt=5,
    ps=ps,
    q=ot.unif(5),
    epochs=5,
    batch_size=min(4, len(Cs)),
    learning_rate=0.1,
    projection="nonnegative_symmetric",
    use_log=True,
    random_state=0,
)

weights, embedded_C, T, recon_error = ot.gromov.gromov_wasserstein_linear_unmixing(
    C1, Cdict, p=p, q=ot.unif(5), max_iter_outer=10, max_iter_inner=50,
)
print(weights, recon_error)
```

Use FGW dictionary learning when each structure also has a feature matrix `Y`. Keep prototype runs small; dictionary learning is iterative and can become expensive quickly.

## Workflow 8: optional GNN route

Use this only when the task explicitly asks for POT GNN pooling layers and the environment has PyTorch plus PyTorch Geometric. This generated skill does not verify that optional stack.

High-level route:

1. Verify `import torch`, `import torch_geometric`, and `import ot.gnn` in the user's environment.
2. Use `TFGWPooling` for template FGW graph embeddings where both structure and node features matter.
3. Use `TWPooling` for template Wasserstein-style pooling where the structural GW term is not needed.
4. Validate with a tiny batch of `torch_geometric.data.Data` graphs before training.
5. Route installation, CUDA, and tensor-backend issues to `backend-and-batch`.

Do not treat a successful NumPy GW smoke check as proof that the GNN route is installed or trainable.

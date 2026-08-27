# POT domain-adaptation API reference

Use this reference when selecting and validating POT domain-adaptation APIs. POT installs as the distribution `POT` and imports as `ot`. The minimum verified runtime for this generated skill was NumPy-only; optional packages such as `cvxpy`, `scikit-learn`, `autograd`, `pymanopt`, PyTorch, and PyTorch Geometric must be verified in the user's active environment before claiming those routes are runnable.

## Shared estimator contract

Most `ot.da` classes are scikit-learn-like estimators:

```python
est = ot.da.EMDTransport()
est.fit(Xs=X_source, ys=y_source_or_none, Xt=X_target, yt=y_target_or_none)
X_source_mapped = est.transform(Xs=X_source_or_new, batch_size=128)
X_target_mapped = est.inverse_transform(Xt=X_target_or_new, batch_size=128)
y_target_soft = est.transform_labels(ys=y_source)
y_source_soft = est.inverse_transform_labels(yt=y_target)
```

Data conventions:

- `Xs`: source samples, shape `(n_source, n_features)`.
- `Xt`: target samples, shape `(n_target, n_features)`.
- `ys`: source labels, shape `(n_source,)`; required by class-regularized transports and JCPOT.
- `yt`: target labels, shape `(n_target,)`; optional for semi-supervised cost correction. Use `-1` for unknown target labels; do not use `-1` as a real class id.
- Fitted estimators commonly expose `cost_`, `coupling_`, transformed samples through `transform`, and sometimes `log_`, `classes_`, `proportions_`, `mapping_`, `A_`, `B_`, `phi`, or `G` depending on the estimator.
- Costs are pairwise distances from `ot.dist(Xs, Xt, metric=...)`; `norm` may scale the cost matrix for some transports.

## Estimator selection matrix

| Need | API | Important inputs | Main outputs/checks |
| --- | --- | --- | --- |
| Baseline unsupervised OTDA with exact couplings | `ot.da.EMDTransport` | `metric`, `norm`, `out_of_sample_map`, `limit_max`, `max_iter` | `coupling_` shape `(n_source, n_target)`, `cost_`, `transform(Xs=...)`. |
| Entropic OTDA with smoother couplings | `ot.da.SinkhornTransport` | `reg_e`, `method`, `max_iter`, `tol`, `out_of_sample_map` | Smoother `coupling_`; use when exact EMD is too sparse or slow. |
| Class-regularized Sinkhorn | `ot.da.SinkhornLpl1Transport`, `ot.da.SinkhornL1l2Transport` | `ys` is required; `reg_e`, `reg_cl`, inner iterations | Couplings penalize cross-class mass; useful for supervised source labels. |
| Unbalanced source/target mass adaptation | `ot.da.UnbalancedSinkhornTransport` | `reg_e`, `reg_m`, optional labels | Relaxed row/column sums; route mass-semantics questions to `unbalanced-partial`. |
| Linear OT mapping for Gaussian-like shift | `ot.da.LinearTransport`, `ot.da.LinearGWTransport` | `reg`, `bias`, source/target samples | Linear map attributes such as `A_` and `B_`; good for simple affine shifts. |
| Joint coupling + learned mapping | `ot.da.MappingTransport` | `kernel`, `mu`, `eta`, `bias`, `sigma`, iterations | `coupling_` plus `mapping_`; `transform` uses barycentric mapping for fitted points and learned mapping for new points. |
| Multi-source target-shift adaptation | `ot.da.JCPOTTransport` | `Xs` list, `ys` list, target `Xt`, `reg_e`, `max_iter` | `coupling_` list and `proportions_` target class proportions. |
| Strongly convex nearest Brenier potential | `ot.da.NearestBrenierPotential`, `ot.mapping.nearest_brenier_potential_fit` | Requires `cvxpy`; `strongly_convex_constant`, `gradient_lipschitz_constant`, `its` | Potential values and gradients; use only after optional dependency verification. |
| Wasserstein dimensionality reduction | `ot.dr.wda`, `ot.dr.ewca`, `ot.dr.projection_robust_wasserstein` | Requires `POT[dr]` (`autograd`, `pymanopt`, `scikit-learn`) | Projection matrix/callable; route missing dependency errors to troubleshooting. |
| Graph neural-network OT layers | `ot.gnn.TFGWPooling`, `ot.gnn.TWPooling` | Requires PyTorch and PyTorch Geometric | Route graph-layer details to `gromov` and backend installation to `backend-and-batch`. |

## Verified constructor/function signatures

These signatures were verified from the installed package facts:

```text
ot.da.EMDTransport(metric='sqeuclidean', norm=None, log=False, distribution_estimation=<function distribution_estimation_uniform>, out_of_sample_map='ferradans', limit_max=10, max_iter=100000)
ot.da.SinkhornTransport(reg_e=1.0, method='sinkhorn_log', max_iter=1000, tol=1e-08, verbose=False, log=False, metric='sqeuclidean', norm=None, distribution_estimation=<function distribution_estimation_uniform>, out_of_sample_map='continuous', limit_max=inf)
ot.da.SinkhornLpl1Transport(reg_e=1.0, reg_cl=0.1, max_iter=10, max_inner_iter=200, log=False, tol=1e-08, verbose=False, metric='sqeuclidean', norm=None, distribution_estimation=<function distribution_estimation_uniform>, out_of_sample_map='ferradans', limit_max=inf)
ot.da.MappingTransport(mu=1, eta=0.001, bias=False, metric='sqeuclidean', norm=None, kernel='linear', sigma=1, max_iter=100, tol=1e-05, max_inner_iter=10, inner_tol=1e-06, log=False, verbose=False, verbose2=False)
ot.da.JCPOTTransport(reg_e=0.1, max_iter=10, tol=1e-08, verbose=False, log=False, metric='sqeuclidean', out_of_sample_map='ferradans')
ot.da.NearestBrenierPotential(strongly_convex_constant=0.6, gradient_lipschitz_constant=1.4, log=False, its=100, seed=None)
ot.mapping.joint_OT_mapping_linear(xs, xt, mu=1, eta=0.001, bias=False, verbose=False, verbose2=False, numItermax=100, numInnerItermax=10, stopInnerThr=1e-06, stopThr=1e-05, log=False, **kwargs)
ot.mapping.nearest_brenier_potential_fit(X, V, X_classes=None, a=None, b=None, strongly_convex_constant=0.6, gradient_lipschitz_constant=1.4, its=100, log=False, init_method='barycentric', solver=None)
```

Class methods such as `fit`, `transform`, `inverse_transform`, `transform_labels`, and `inverse_transform_labels` are inherited or specialized; prefer keyword arguments (`Xs=`, `Xt=`, `ys=`, `yt=`) to avoid silent positional mistakes.

## Attributes to validate after fitting

- `cost_`: finite pairwise cost matrix after metric and normalization choices.
- `coupling_`: nonnegative transport plan. For ordinary transports it is an array; for `JCPOTTransport` it is a list of arrays, one per source domain.
- `log_`: present when `log=True` or for some algorithms; inspect convergence errors before trusting a stalled fit.
- `proportions_`: `JCPOTTransport` target class proportions; should be finite and sum close to one.
- `mapping_`: learned mapping coefficients for `MappingTransport`.
- `A_`, `B_`: affine mapping parameters for linear transports when exposed by the fitted class.
- `classes_`: label set discovered from `ys`/`yt` for label-transform methods.

## Optional dependency probes

Use the bundled smoke helper for a safe status summary:

```bash
python scripts/domain_adaptation_smoke.py --case dependencies --json
```

Interpret common probes:

- `ot.dr` failing with a message about `autograd`, `pymanopt`, and `scikit-learn` means WDA/EWCA routes need `POT[dr]` or equivalent packages.
- `ot.mapping.nearest_brenier_potential_fit` imports without `cvxpy`, but calling it will fail when the optimization problem is built. Verify `cvxpy` before selecting nearest-Brenier workflows.
- PyTorch/PyTorch Geometric are not needed for NumPy OTDA estimators; they only matter for GNN layers or backend-specific tensor workflows.

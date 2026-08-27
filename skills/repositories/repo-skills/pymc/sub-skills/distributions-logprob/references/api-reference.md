# Distribution/logp API reference

Key PyMC 6.3.0 APIs:

| API | Signature/use |
| --- | --- |
| `pm.CustomDist` | `(name, *dist_params, dist=None, random=None, logp=None, logcdf=None, support_point=None, ndim_supp=None, ndims_params=None, signature=None, dtype="floatX", **kwargs)` for named custom RVs. |
| `pm.DensityDist` | Compatibility route for custom log-density variables; prefer `CustomDist` in new code. |
| `pm.Mixture` | Named RV constructor; use `pm.Mixture.dist(w=..., comp_dists=...)` for an unregistered mixture. |
| `pm.Truncated` / `pm.Censored` | Wrap unregistered `.dist()` base distributions where appropriate. |
| `pm.logp` | `(rv, value, warn_rvs=True, **kwargs) -> Variable`; evaluate with `.eval()` or compile. |
| `pm.logcdf` | `(rv, value, warn_rvs=True) -> Variable`. |

`shape` is the final random-variable shape. `size` is replication/batch size and excludes support dimensions for multivariate distributions. Registered variables can use `dims`; unregistered `.dist()` tensors cannot use `dims` or `initval` and do not add named variables to the model.

For multivariate `CustomDist`, use a generalized ufunc-style `signature` such as `(n)->(n)` and ensure `random`, `logp`, and `support_point` agree on support dimensions.

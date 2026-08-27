# Distribution/logp troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Mixture component error | Already-registered model variables passed as components. | Use `.dist()` components and keep only parent parameters named. |
| `.dist()` rejects `dims` or `initval` | `.dist()` returns an unregistered tensor. | Put `dims`/`initval` on the named RV that consumes it, not on `.dist()`. |
| Logp shape surprises | Batch dimensions versus support dimensions are confused. | Check `shape`, `size`, and support signature; evaluate `pm.logp(rv, value).eval()` before sampling. |
| Invalid parameter errors appear only during logp evaluation | Parameter checks are symbolic. | Evaluate/compile logp at a representative point before sampling. |
| Posterior predictive fails for `CustomDist` | No `random` method supplied. | Add `random` with `rng` and `size` arguments, or avoid predictive draws for that variable. |
| Multivariate `CustomDist` support errors | Missing/wrong `signature`, `ndim_supp`, `ndims_params`, or `support_point`. | Provide a consistent signature such as `(n)->(n)` and smoke-test draw/logp shapes. |
| Transformed variable initial point invalid | Support/transform mismatch or impossible initval. | Choose support-compatible initial values and inspect `model.initial_point()`/`model.debug()`. |

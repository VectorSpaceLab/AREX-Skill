# Inference troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Low-draw warning | Smoke/test draw counts are too small. | Ignore only for API smokes; increase draws/tune/chains for real inference. |
| Divergences | Geometry, priors, scaling, or parameterization problem. | Reparameterize, standardize data, use stronger priors, increase `nuts={"target_accept": ...}`. |
| Tree-depth warnings | NUTS trajectories hit max tree depth. | First inspect divergences/model geometry; increase `max_treedepth` only when justified. |
| External NUTS rejects `callback`, custom `trace`, or `return_inferencedata=False` | External samplers do not support those PyMC-only features. | Pin `nuts_sampler="pymc"` or remove incompatible options. |
| JAX backend warning about CPU fallback | CPU-only JAX installed. | Accept for CPU workflows; install CUDA JAX only for explicit GPU work. |
| Posterior predictive has wrong group | `predictions=True` not used for out-of-sample prediction. | Use `predictions=True`; decide whether to set `extend_inferencedata=True`. |
| Shape error after changing data | `pm.Data` values and coords out of sync. | Route to modeling-data; update values and coords together. |
| Missing `log_likelihood` | Not computed during conversion. | Call `pm.compute_log_likelihood(idata, model=model)`. |

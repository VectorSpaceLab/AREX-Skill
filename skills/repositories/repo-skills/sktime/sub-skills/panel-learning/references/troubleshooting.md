# Panel Learning Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `X` has wrong shape | Not a supported Panel mtype | Route to `data-interfaces` and validate `numpy3D` or `pd-multiindex`. |
| `len(y)` mismatch | Labels/targets do not match instances | Count panel instances and align `y` before fit. |
| `predict_proba` missing | Estimator lacks probability capability | Inspect `capability:predict_proba` and choose another classifier if needed. |
| Negative regression score | R-squared can be negative for poor baselines | Use it as a diagnostic, not necessarily an execution failure. |
| Optional estimator imports but fails at fit | Soft dependency, GPU/model, or capability mismatch | Check `python_dependencies`, tags, and small baseline fallback. |
| Clustering slow or unstable | Large `n_init`, `max_iter`, or DTW metric | Reduce settings for smoke and verify metric dependencies. |

Run `scripts/panel_learning_smoke.py --json` for a compact base-path check.

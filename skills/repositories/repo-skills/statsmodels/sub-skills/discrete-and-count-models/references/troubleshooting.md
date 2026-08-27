# Discrete/count troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `PerfectSeparationError` or perfect prediction warning | A predictor or category separates outcomes | Collapse sparse categories, remove separating predictor, regularize if appropriate, or collect more data; do not interpret extreme coefficients as stable. |
| Optimizer does not converge | Poor scaling, separation, bad starting values, inappropriate model family | Scale predictors, simplify model, inspect `mle_retvals`, change optimizer/settings carefully, or use a different model. |
| Huge standard errors or singular Hessian | Weak identification, collinearity, boundary parameter | Check rank, categories, event counts per predictor, and whether inflation/overdispersion terms are supported by data. |
| Poisson underestimates variance | Overdispersion | Compare variance and mean, inspect residuals, and consider robust covariance or NegativeBinomial models. |
| Zero-inflated model unstable | No true structural zero process or inflation at boundary | Compare with simpler Poisson/NegativeBinomial and report instability. |
| Marginal effects unavailable | Result class does not implement `get_margeff` or inputs invalid | Use supported model/result classes or compute scenario predictions manually. |
| Prediction shape/category mismatch | New data lacks constant, formula variables, or category levels | Recreate design with same formula variables or add constant/columns in training order. |

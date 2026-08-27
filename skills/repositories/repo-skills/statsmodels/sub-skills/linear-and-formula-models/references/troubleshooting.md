# Linear/formula troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Coefficients all `NaN` | Missing data with default `missing='none'` | Refit with `missing='raise'` to locate the problem or clean/drop rows explicitly. |
| Singular matrix, huge standard errors, unstable signs | Rank-deficient `exog`, multicollinearity, duplicate intercept, sparse category | Check `np.linalg.matrix_rank`, condition number, `res.model.exog_names`, and remove redundant columns/categories. |
| Prediction errors about shape or columns | New data does not match the training design matrix | For formulas pass a DataFrame with original variable names; for matrix API add the constant and order columns identically. |
| Formula `NameError` or unexpected column names | Patsy/formula expression mismatch | Quote unusual column names or rename columns; use `C(var)` for categoricals; inspect design names. |
| GLM convergence or boundary warnings | Inappropriate family/link, perfect prediction, extreme weights, bad scaling | Scale predictors, inspect response domain, choose a better family/link, and compare with discrete/count models when appropriate. |
| MixedLM singular covariance warning | Random effect variance near zero or overfit grouping structure | Simplify random effects, check group sizes, or fit a fixed-effects alternative. |
| Robust covariance request fails | Missing groups/lags or unsupported covariance for the result type | Use model-supported `cov_type` and required `cov_kwds`; document the estimator assumptions. |

Do not refit the same model instance repeatedly and keep old result objects for comparison; result objects can depend on their model instance. Build separate model instances when comparing fit options.

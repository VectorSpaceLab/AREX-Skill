# Tests and diagnostics troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| User asks for a p-value without a design | Test cannot be selected from variable names alone | Ask/derive sample structure, paired vs independent, one/two-sided alternative, and model context. |
| Diagnostic function shape error | Residuals and design matrix lengths differ | Use residuals from the same fitted result and `res.model.exog`. |
| ANOVA fails or gives unexpected terms | Model not formula-fitted or categorical coding differs | Fit with formula metadata or specify contrast matrices manually; inspect design names. |
| Many significant raw p-values vanish after correction | Multiple testing correction applied | Explain adjusted p-values and false discovery/family-wise error control. |
| Influence measures flag points | High leverage or residual outliers | Report diagnostic evidence; do not delete observations automatically. |
| Heteroskedasticity/autocorrelation detected | OLS standard errors may be invalid | Consider robust/HAC covariance or a model that represents the data-generating process. |

# Datasets/results/graphics troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `get_rdataset` fails | Network unavailable, remote dataset changed, cache missing | Use built-in datasets or local fixtures for reproducible workflows. |
| Plotting raises backend/display errors | GUI backend selected in headless environment | Set `matplotlib.use("Agg")` before importing pyplot and save figures to files. |
| Prediction frame shape error | New data does not match formula variables or design matrix | For formula models pass a DataFrame with original variables; for matrix models recreate the constant and column order. |
| User wants CSV from `summary()` | Summary is presentation text, not structured data | Build a DataFrame from `params`, `bse`, `pvalues`, and `conf_int()` instead. |
| Pickled result will not load | Package/Python version mismatch or unsafe untrusted pickle | Refit if possible; never load untrusted pickle; use structured exports for long-term storage. |
| Too many open figures warning | Figures not closed in loops | Save/close figures with `plt.close(fig)` after each plot. |

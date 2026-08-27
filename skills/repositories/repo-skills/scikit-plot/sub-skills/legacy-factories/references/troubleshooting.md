# Legacy factories troubleshooting

Read root troubleshooting first if `import scikitplot` fails. The factory layer still needs the same compatible SciPy and Matplotlib versions as the direct APIs.

## Failure surfaces

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `"fit" is not in clf`, `"score" is not in clf`, or `"predict" is not in clf` | Object passed to `classifier_factory` is not a sklearn-style classifier. | Use an estimator with `fit`, `score`, and `predict`, or call direct plotting functions with precomputed labels/probabilities. |
| Warning: `predict_proba not in clf. Some plots may not be possible to generate.` | The classifier can be wrapped, but ROC/PR/KS probability plots will fail. | Use a classifier with `predict_proba`, calibrate/wrap the model, or route to plots that do not need probabilities. |
| `"fit"` or `"fit_predict"` missing for `clustering_factory` | Object is not a clusterer with the expected methods. | Use a sklearn-style clusterer or direct `metrics.plot_silhouette` with labels. |
| Warning about an injected method already in `clf` | The factory is overwriting a method name that already exists. | Prefer direct functions, or accept the override only if you control the object. |
| Deprecation warnings from factories or `scikitplot.plotters` | The compatibility layer is deprecated in this snapshot. | Migrate imports and calls to current module functions. |
| Bound-method call fails with an estimator-specific error | The injected method has the same requirements as the direct plot it wraps. | Route to the owning sub-skill for the underlying plot and debug the actual inputs. |
| `BrokenProcessPool` or unpickle errors from `clf.plot_learning_curve(..., n_jobs=-1)` | Factory-injected bound methods can make the estimator object difficult for joblib worker processes to serialize. | Use `n_jobs=1` on the injected method, or migrate to `scikitplot.estimators.plot_learning_curve` with an ordinary cloneable estimator. |

## Debug sequence

1. Verify the object has the methods required by the factory.
2. Check whether the failing injected method needs `predict_proba`, `feature_importances_`, `n_clusters`, or a fitted state.
3. Reproduce with the direct function from the owning sub-skill.
4. If direct usage succeeds, keep the direct function and remove the deprecated factory wrapper from new code.
5. If old code must remain unchanged, suppress only known deprecation warnings after confirming behavior with the smoke script.

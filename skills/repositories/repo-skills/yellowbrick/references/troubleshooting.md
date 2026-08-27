# Yellowbrick Troubleshooting

## When to read

Read this for failures that affect more than one Yellowbrick visualizer family:
install/import errors, scikit-learn compatibility, estimator type detection,
Matplotlib display/font problems, optional dependencies, dataset cache behavior,
and saved-output validation.

## Install and compatibility

| Symptom | Likely cause | Recovery |
|---|---|---|
| `This estimator is not a classifier` for `LogisticRegression`, or similar wrong estimator-type errors for normal scikit-learn models | Yellowbrick 1.5 checks `_estimator_type`; very new scikit-learn releases can change estimator internals. | Use a compatibility stack such as `scikit-learn==1.3.2` with `numpy<2` for this snapshot, then rerun a tiny smoke script. If using a newer Yellowbrick release, verify its declared compatibility first. |
| Import errors for `yellowbrick` after install | Package not installed in the active Python, broken dependencies, or source checkout shadowing another install. | Run `python -m pip show yellowbrick`, `python -m pip check`, and `python -c "import yellowbrick; print(yellowbrick.__version__)"` from the same Python used for the task. |
| `ImportError`, `AttributeError`, or API mismatch in scikit-learn/numpy/scipy | Dependency resolver selected versions newer than this source snapshot expected. | Pin the scientific stack conservatively, recreate the environment when necessary, and prefer smoke scripts before full reports. |
| `YellowbrickTypeError` for an estimator | The selected visualizer does not match the model family, or a third-party estimator lacks scikit-learn metadata. | Use a classifier visualizer only with classifiers, a regression visualizer only with regressors, and a cluster visualizer only with clusterers. For third-party estimators, read the contrib wrapper guidance. |

## Matplotlib display and rendering

| Symptom | Likely cause | Recovery |
|---|---|---|
| Plot hangs, no display, or GUI backend error in CI/agent/server | Interactive backend selected in a headless process. | Before importing `pyplot`, set `matplotlib.use("Agg", force=True)`, then call `show(outpath="file.png")`. |
| Many `findfont` warnings | Yellowbrick default style requests fonts not installed on the host. | If output files are non-empty, treat as appearance warnings. Install fonts or set a different Matplotlib font only for publication-quality rendering. |
| Empty or missing output file | `show()` not called, exception before saving, wrong output directory, or figure cleared too early. | Use a bundled smoke script, check file size, and call `show(outpath=..., clear_figure=True)` after `fit`/`score`. |
| Several figures overlap or leak state | Matplotlib global figure state reused. | Pass explicit `ax=`, call `clear_figure=True`, or `plt.close(fig)` after saving. |

## Estimator and data issues

- `ROCAUC`, `PrecisionRecallCurve`, and `DiscriminationThreshold` need a score
  source such as `predict_proba` or `decision_function`. Choose an estimator
  that exposes one, calibrate the model, or use a visualizer that only needs
  `predict`.
- Class labels and encoded targets must match. Use `classes=` for display names
  and `encoder=` only when the visualizer needs to map encoded values.
- `X` and `y` must remain aligned after train/test splits, sampling, or dropping
  missing values.
- Feature visualizers need feature-name arrays the same length as the columns
  they display.
- Cross-validation visualizers can fail when a class has too few samples for
  the requested folds; reduce `cv`, use stratified splits, or collect more data.

## Optional dependencies

Yellowbrick's base install does not require every optional workflow dependency.

| Optional surface | Missing symptom | Recovery |
|---|---|---|
| pandas dataset/DataFrame support | Dataset object cannot return DataFrames, or pandas-specific tests skip/fail | Install pandas or use numpy arrays plus explicit feature names. |
| `UMAPVisualizer` | `umap package doesn't seem to be installed` | Install `umap-learn`, or use `TSNEVisualizer`/other projections when UMAP is optional. |
| POS parser workflows | NLTK/SpaCy import or model-data errors | Use pre-tagged corpora with `PosTagVisualizer`, or install the parser package and required language/tagger data. |
| statsmodels contrib adapter | `statsmodels` import errors | Install statsmodels only when using `StatsModelsWrapper`; otherwise route to stable sklearn estimators. |

## Datasets and network behavior

Yellowbrick dataset loaders may download archives into a data cache when data is
missing. For offline or deterministic tasks:

1. Set `YELLOWBRICK_DATA` or pass `data_home=` to a cache directory.
2. Run `sub-skills/text-and-datasets/scripts/check_dataset_cache.py` to inspect
   what is present without downloading or deleting anything.
3. Use `python -m yellowbrick.download --help` to inspect downloader flags.
4. Run real downloads only when network access and cache writes are acceptable.

Do not run `--cleanup` or `--overwrite` against a user cache without explicit
approval.

## When to stop

Stop and report the limitation instead of forcing a run when a workflow needs
network downloads, optional parser/model data, an unavailable optional package,
large cross-validation, or publication-grade fonts and the user has not approved
that cost or environment change.

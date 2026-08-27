# Cross-cutting troubleshooting

Read this before a sub-skill-specific troubleshooting page when the package does not import or the first plot fails before workflow-specific inputs matter.

## Compatibility window for this snapshot

The repository snapshot reports `scikit-plot` version `0.3.7`. Live inspection found that the current source imports and plotting paths expect older SciPy and Matplotlib APIs:

- `scipy.interp` must exist, so use `scipy<1.11`.
- `matplotlib.cm.get_cmap` must exist, so use `matplotlib<3.9`.

A compatible install line for this snapshot is:

```bash
python -m pip install "scikit-plot==0.3.7" "scipy<1.11" "matplotlib<3.9" scikit-learn joblib
```

For a local checkout, install the same dependency window and then, from the root of this skill directory, run:

```bash
python scripts/check_environment.py
```

## Failure map

| Symptom | Likely cause | Recovery | Then read |
| --- | --- | --- | --- |
| `ImportError: cannot import name 'interp' from 'scipy'` | SciPy is too new for this source snapshot. | Install `scipy<1.11` and rerun the import check. | the relevant sub-skill after import succeeds |
| `AttributeError: module 'matplotlib.cm' has no attribute 'get_cmap'` | Matplotlib is too new for this source snapshot. | Install `matplotlib<3.9` and rerun the root smoke script. | `metrics` or the plot family that failed |
| A plot opens on the wrong figure | `ax` was omitted or a `Figure` was passed instead of an `Axes`. | Create `fig, ax = plt.subplots()` and pass `ax=ax`; keep the returned axes. | the sub-skill API reference for that function |
| The task mentions `plotters`, `classifier_factory`, or `clustering_factory` | Old compatibility layer or deprecated API path. | Route to `legacy-factories`; migrate to current modules when possible. | `sub-skills/legacy-factories/SKILL.md` |
| The user asks for command-line flags | scikit-plot exposes Python APIs and examples, not a package CLI. | Use Python snippets or bundled smoke scripts instead of inventing CLI flags. | `workflow-map.md` |

## Minimal package check

Use this small check if the bundled script is not available in the current context:

```python
import matplotlib
matplotlib.use("Agg", force=True)
import scikitplot
from scikitplot.metrics import plot_confusion_matrix
ax = plot_confusion_matrix([0, 1], [1, 0])
print(scikitplot.__version__, type(ax).__name__)
```

If this fails, fix the import/runtime stack before debugging model data or estimator inputs.

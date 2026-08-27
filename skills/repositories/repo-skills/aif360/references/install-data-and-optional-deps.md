# Install, Data, and Optional Dependency Reference

## When to read

Read this before installing AIF360 for a workflow, loading built-in datasets,
or using optional algorithms/detectors that may warn about missing packages.

## Base install

```bash
pip install aif360
python -c "import aif360; print(aif360.__version__)"
```

AIF360 0.6.1 metadata requires Python `>=3.8` and base dependencies including
NumPy, SciPy, pandas, scikit-learn `<1.6`, and matplotlib. Use an isolated
virtual environment because optional ML/optimization dependencies can conflict
with other projects.

## Construction verification status

This generated skill verified:

- `aif360==0.6.1` base package import.
- Legacy in-memory `BinaryLabelDataset`, `BinaryLabelDatasetMetric`, and
  `ClassificationMetric` workflows.
- `aif360.sklearn.metrics` metric functions on synthetic pandas data.
- Base MDSS and metric explainer imports through safe synthetic scripts.

This generated skill did **not** install broad extras or run full notebooks,
raw-dataset downloads, R wrapper verification, MLOps platform samples, or
optional ML backends. Treat optional workflows as unverified until the target
environment installs the matching extra and passes a small smoke.

## Optional extras and capabilities

| Extra | Primary capability | Install hint | Notes |
| --- | --- | --- | --- |
| `OptimPreproc` | Optimized preprocessing with `cvxpy` | `pip install 'aif360[OptimPreproc]'` | Solver availability matters. |
| `AdversarialDebiasing` | TensorFlow adversarial debiasing | `pip install 'aif360[AdversarialDebiasing]'` | Uses TensorFlow compatibility APIs; verify Python/TF compatibility. |
| `DisparateImpactRemover` | Feature repair via BlackBoxAuditing | `pip install 'aif360[DisparateImpactRemover]'` | Constructor imports the repairer. |
| `LFR` | Learned fair representations | `pip install 'aif360[LFR]'` | Torch CPU can be enough for tiny smokes. |
| `LIME` | LIME explanations in notebooks | `pip install 'aif360[LIME]'` | Distinct from AIF360 metric explainers. |
| `ART` | ART classifier wrapper | `pip install 'aif360[ART]'` | External classifier backend must also work. |
| `Reductions` | Fairlearn reductions | `pip install 'aif360[Reductions]'` | Used by exponentiated-gradient and grid-search reductions. |
| `FairAdapt` | FairAdapt sklearn preprocessing | `pip install 'aif360[FairAdapt]'` | Requires R/rpy2 compatibility. |
| `inFairness` | SenSeI/SenSR wrappers | `pip install 'aif360[inFairness]'` | Requires torch/skorch/inFairness. |
| `notebooks` | Notebook demo stack | `pip install 'aif360[notebooks]'` | May install plotting/Jupyter extras and still require data files. |
| `OptimalTransport` | `ot_distance` metric | `pip install 'aif360[OptimalTransport]'` | Provides POT imported as `ot`. |
| `FACTS` | FACTS detector/recourse workflows | `pip install 'aif360[FACTS]'` | Provides mlxtend/colorama/tqdm surfaces. |
| `tests`, `docs`, `all` | Development-style broad dependency sets | Use only when required | Avoid these for ordinary user workflows. |

The repository README mentions `LawSchoolGPA` among extras, but the inspected
package metadata at this commit does not define a `LawSchoolGPA` extra. If a
future package version changes that, refresh this skill.

## Standard dataset data constraints

AIF360 wraps common fairness datasets, but raw benchmark data usually are not
bundled in the Python package. Before loading real standard datasets:

- Confirm whether network access is allowed.
- Confirm whether the user accepts any data-source terms.
- Confirm where raw files or caches should live.
- Record data provenance and preprocessing changes.

Use synthetic data for API demonstrations, smoke checks, or skill verification
when the task does not require real benchmark results.

## Install strategy by task

- Metrics, dataset construction, base Reweighing, core postprocessing, MDSS, and
  metric explainers: start with base `aif360` and run a bundled smoke.
- One optional algorithm: install the one named extra and run a tiny workflow.
- Multiple notebook demos: install only the extras that each selected notebook
  imports; do not assume all notebooks are safe or data-local.
- R wrapper: read [r-and-mlops-notes.md](r-and-mlops-notes.md) and verify R,
  reticulate, and Python separately.
- Platform samples: treat Kubeflow/NiFi assets as integration examples requiring
  platform-specific validation.

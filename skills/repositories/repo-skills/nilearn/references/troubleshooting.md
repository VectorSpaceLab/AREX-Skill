# Nilearn Root Troubleshooting

Use this root reference for cross-cutting failures. Workflow-specific failures
belong in the nearest sub-skill troubleshooting file.

## Install And Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'nilearn'` | Package is not installed in the active Python environment | Install with `python -m pip install nilearn` or use the environment selected for the task. |
| Plotting imports fail or report generation cannot find Matplotlib/Plotly/Kaleido | Optional plotting extra is missing | Install `python -m pip install "nilearn[plotting]"` or avoid plotting/reporting features. |
| `pip check` reports dependency conflicts | Environment has incompatible NumPy/SciPy/scikit-learn/nibabel/pandas versions | Use a fresh environment, then install Nilearn and only required extras. |
| Import works in one shell but not another | Different Python executable or environment is active | Run `python -c "import sys, nilearn; print(sys.executable, nilearn.__version__)"` in the same shell that will run the workflow. |

## Data And Cache

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Dataset fetcher unexpectedly downloads large data | Most `fetch_*` functions are network/cache helpers | Use `datasets-interfaces` to choose local loaders or set a bounded `data_dir`, subject count, and filters before fetching. |
| Fetcher resumes corrupt or partial data | Interrupted archive extraction or stale cache | Remove only the affected dataset cache subdirectory or use a new `data_dir`; do not delete unrelated caches blindly. |
| Template or atlas output shape surprises downstream code | Resolution, atlas family, or probabilistic-vs-label atlas mismatch | Inspect the returned Bunch keys, image shape, and labels/LUT before building maskers or models. |

## API And Workflow Mismatch

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Function accepts paths in docs but code passes arrays | Niimg APIs expect path-like, nibabel image, or compatible Niimg objects, not raw arrays | Use `nilearn.image.new_img_like` or nibabel constructors before calling image APIs. |
| Estimator fails before `fit` or has no fitted attributes | A scikit-learn-style estimator was used out of order | Construct with parameters, call `fit`, then inspect trailing-underscore attributes or call `transform`/`predict`. |
| Cross-validation score looks too good | Leakage from preprocessing, masking, feature selection, or confounds outside CV | Route to `ml-decoding-connectivity` and put feature extraction inside a pipeline or use Nilearn decoders intentionally. |

## Plotting And Reports

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Plot command hangs or fails on a server | GUI backend or browser display is unavailable | Use a headless Matplotlib backend and save with `output_file`; see `plotting-reporting`. |
| Interactive view does not export static image | HTML/Plotly views are different from Matplotlib static figures | Choose `plot_*` for files, `view_*` for HTML embedding, or install required static export dependencies. |
| GLM or masker report is empty or missing figures | Model/masker was configured without reports, not fitted, or plotting deps are missing | Enable reports where supported, fit first, and verify plotting extras. |

## Repository Development

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Import-linter fails | A module imported from an equal or higher architecture layer | Use `development-maintenance` to find the allowed lower-layer home for shared code. |
| Tests require real data or network | Nilearn tests usually use synthetic fixtures and mocks | Prefer `nilearn._utils.data_gen`, nearby fixtures, and no-network unit tests. |
| Reviewer asks for generated-test marker | Modified or generated test lacks `@pytest.mark.ai_generated` | Add the marker to any test generated or modified by an AI agent. |
| Changelog entry missing | PR-worthy change requires `doc/changes/latest.rst` entry | Add a one-line badge/PR/author entry following repo policy when preparing a PR. |

---
name: nilearn
description: "Use and maintain Nilearn, the Python neuroimaging package for
  Niimg/surface data, maskers, GLM, decoding, connectivity, plotting, datasets,
  and repository development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Nilearn Repo Skill

Use this skill when a task involves the `nilearn` Python package or this
Nilearn source checkout. Nilearn supports statistical learning for
neuroimaging data: Niimg and surface manipulation, signal extraction, GLM,
decoding, connectomes, decomposition, datasets, plotting, reports, and
scikit-learn-style estimators.

## Quick Start

- Install the package with `python -m pip install nilearn` for core APIs.
- Install plotting/reporting extras with `python -m pip install "nilearn[plotting]"` when a task needs Matplotlib, Plotly, or Kaleido-backed outputs.
- Check imports with:
  `python -c "import nilearn; import nilearn.image; import nilearn.maskers; print(nilearn.__version__)"`.
- Nilearn does not expose package console scripts; use Python APIs and bundled
  smoke helpers in the relevant sub-skill.
- Read [repo provenance](references/repo-provenance.md) before deciding whether
  this generated skill is stale for a changed checkout.
- Use [root troubleshooting](references/troubleshooting.md) for install/import,
  optional dependency, data/cache, plotting, and development failure triage.

## Route By Task

- **Images, masks, and signals:** Use
  [data-io-signal](sub-skills/data-io-signal/SKILL.md) for `nilearn.image`,
  `nilearn.masking`, `nilearn.signal`, Niimg validation, resampling,
  smoothing, thresholding, direct `apply_mask`/`unmask`, and no-network image
  smoke checks.
- **Maskers and regions:** Use
  [maskers-regions](sub-skills/maskers-regions/SKILL.md) for `NiftiMasker`,
  label/map/sphere maskers, multi-subject maskers, `RegionExtractor`,
  `Parcellations`, `ReNA`, inverse transforms, and masker reports.
- **Surface data:** Use
  [surface-workflows](sub-skills/surface-workflows/SKILL.md) for `SurfaceImage`,
  `PolyMesh`, `PolyData`, `vol_to_surf`, fsaverage helpers, and surface masker
  data contracts.
- **GLM analysis:** Use [glm-analysis](sub-skills/glm-analysis/SKILL.md) for
  first-level and second-level models, events, design matrices, HRFs, BIDS GLM
  helpers, contrasts, thresholding, cluster inference, and GLM reports.
- **Decoding and connectomes:** Use
  [ml-decoding-connectivity](sub-skills/ml-decoding-connectivity/SKILL.md) for
  `Decoder`, `SearchLight`, SpaceNet/FREM, `ConnectivityMeasure`, group sparse
  covariance, CanICA/DictLearning, and mass-univariate permutation workflows.
- **Datasets and interfaces:** Use
  [datasets-interfaces](sub-skills/datasets-interfaces/SKILL.md) for dataset
  fetchers/loaders, local templates, atlases, cache/data_dir choices,
  OpenNeuro/NeuroVault, BIDS helpers, fMRIPrep confounds, and FSL design files.
- **Plotting and reports:** Use
  [plotting-reporting](sub-skills/plotting-reporting/SKILL.md) for static
  brain plots, surface plots, interactive HTML views, connectome/matrix/event
  visualizations, cluster tables, HTML reports, and headless rendering issues.
- **Repository changes:** Use
  [development-maintenance](sub-skills/development-maintenance/SKILL.md) when
  editing this checkout, adding tests/docs/changelog entries, or debugging
  import-linter, pre-commit, estimator checks, or CI-style validation.

## Common Workflow Chains

- **Preprocess then model:** Start with `data-io-signal` for Niimg/mask/signal
  validation, use `maskers-regions` for estimator-style extraction when needed,
  then use `glm-analysis` or `ml-decoding-connectivity`.
- **Dataset-backed analysis:** Start with `datasets-interfaces` to choose safe
  loaders or bounded fetchers, then route to maskers, GLM, decoding,
  connectivity, or plotting based on the analysis goal.
- **Surface visualization:** Use `surface-workflows` to validate mesh/data
  shapes and `plotting-reporting` to choose static or interactive rendering.
- **GLM reporting:** Use `glm-analysis` for model, contrast, and threshold
  decisions; use `plotting-reporting` for cluster tables, HTML report output,
  and headless/optional dependency failures.
- **Coding-agent maintenance:** Use `development-maintenance` first, then route
  to the user-facing sub-skill that owns the affected behavior for examples and
  API expectations.

## Data And Safety Notes

- Treat most `fetch_*` dataset functions as network/cache operations unless the
  datasets sub-skill marks them as no-network local loaders.
- Prefer tiny synthetic NIfTI/surface fixtures for smoke checks and tests.
- Do not assume plotting extras are installed unless the environment was
  installed with `nilearn[plotting]` or the task confirms Matplotlib/Plotly.
- Use scikit-learn-style expectations for estimators: `fit` returns `self`,
  fitted attributes end in `_`, and `transform` or `predict` consumes data with
  shapes described by the owning sub-skill.
- When editing Nilearn itself, obey the repository’s import-layer architecture,
  test-marker requirements, changelog policy, and formatting conventions in
  `development-maintenance`.

## Bundled Root Helper

- Run `python scripts/inspect_nilearn_environment.py --help` from this skill
  directory to inspect an environment for Nilearn imports, version, optional
  plotting packages, and public module availability without downloading data.

---
name: pyts
description: "Routes pyts time-series loading, preprocessing, symbolic encoding,
  feature extraction, metrics, classification, and multivariate workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# pyts

Use this skill when a user wants to work with the `pyts` package for time
series classification, transformation, metrics, or multivariate wrappers.

## Quick install

For a fresh environment, install the runtime package and the verification tools:

```bash
python -m pip install -e .
python -m pip install 'scikit-learn<1.6' pytest
```

The verified snapshot for this repo needed `scikit-learn<1.6` so the DTW and
classifier workflows remain compatible. If you already have a working install,
keep the compatible scikit-learn version and run the smoke script below.

## Quick check

Run the bundled smoke helper from this skill tree:

```bash
python scripts/pyts_smoke.py --mode core
python scripts/pyts_smoke.py --mode all
```

Use `--mode datasets`, `--mode symbolic`, `--mode features`, `--mode metrics`,
or `--mode multivariate` when you want a focused installed-package check for a
single workflow family. Each sub-skill also ships a local wrapper at
`sub-skills/<id>/scripts/smoke.py` that runs the matching mode from inside that
sub-skill directory.

## Route map

### `datasets-and-loaders`
Use when the task is to load bundled toy data, inspect UCR/UEA metadata, make
synthetic data, or discuss cached versus network-backed dataset helpers.

### `preprocessing-and-symbols`
Use when the task is to scale, impute, discretize, approximate, or build
symbolic/bag-of-words representations from univariate series.

### `feature-extraction-and-images`
Use when the task is to extract feature vectors, build time-series images, or
decompose series with SSA before a downstream model.

### `metrics-and-classifiers`
Use when the task is to compare series with DTW/BOSS, choose a region or lower
bound, or fit a pyts classifier such as `KNeighborsClassifier(metric='dtw')`.

### `multivariate-workflows`
Use when the input is 3D and the task is to wrap a univariate pyts estimator,
work with `WEASELMUSE`, or build multivariate recurrence images.

## How to navigate

1. Start from the user's data shape and desired output.
2. Go to the most specific sub-skill above.
3. Read the sub-skill's workflow and troubleshooting reference before choosing
   parameters.
4. If the task crosses sub-skill boundaries, keep the data-shape or model choice
   in the upstream sub-skill and hand off to the downstream one only when the
   intermediate representation is clear.

## Shared references

- Read `references/repo-provenance.md` when checking whether this skill still
  matches the current checkout or before refreshing it.
- Read `references/package-and-build.md` or
  `references/package-build-metadata.json` when you need the verified
  distribution metadata, build backend, optional extras, or compatibility pin.
- Read `references/troubleshooting.md` for cross-cutting install/import/version
  issues, especially the scikit-learn compatibility note for DTW.
- Read `scripts/pyts_smoke.py` when you need a quick reproducible installed-
  package check for one workflow family or all of them.
- Read the route-specific `sub-skills/*/scripts/smoke.py` wrappers when you
  want a single workflow-family smoke check from the owning sub-skill.

## Examples of natural requests

- "Load GunPoint and tell me the shapes"
- "Impute missing values and discretize a time series"
- "Build a ROCKET or shapelet feature matrix"
- "Compute DTW with a Sakoe-Chiba band"
- "Wrap a classifier for BasicMotions"

## Notes for future agents

- The repo exposes no public CLI of its own.
- This skill is for the installed package, not the original checkout's docs or
  examples.
- If `dtw` starts failing with a `force_all_finite` validation error, use the
  troubleshooting reference; the verified snapshot required a compatible
  scikit-learn pin.

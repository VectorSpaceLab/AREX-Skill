---
name: glm-analysis
description: "Build Nilearn first-level and second-level GLM workflows,
  including design matrices, contrasts, BIDS helpers, thresholding, and GLM
  reports."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# GLM Analysis

Use this sub-skill when a task asks for Nilearn statistical modeling of fMRI
activation with first-level or second-level general linear models.

## Read First

- For signatures, fitted attributes, methods, and contrast outputs, read
  [API Reference](references/api-reference.md).
- For practical recipes and checklists, read
  [Workflows](references/workflows.md).
- For common errors and debugging paths, read
  [Troubleshooting](references/troubleshooting.md).
- For a local no-network design-matrix sanity check, run
  `python scripts/make_design_matrix_smoke.py --help`.

## Route Here

- Create or validate first-level design matrices from frame times, events,
  HRFs, drifts, FIR delays, or extra regressors.
- Fit `FirstLevelModel`, inspect `design_matrices_`, and compute t/F contrasts
  from expressions or vectors, including fixed effects over multiple runs.
- Use `first_level_from_bids` after BIDS derivatives are already present and
  a task needs model objects plus fit inputs for each subject.
- Fit `SecondLevelModel`, create second-level design matrices, compute group
  contrasts, or run `non_parametric_inference`.
- Apply GLM thresholding with `threshold_stats_img` or
  `cluster_level_inference`, then produce cluster tables or GLM reports.

## Route Elsewhere

- Use `../data-io-signal/SKILL.md` for image loading, masking, resampling,
  confound cleaning, signal extraction, and preprocessing before GLM fitting.
- Use `../datasets-interfaces/SKILL.md` for dataset fetchers, BIDS queries,
  fMRIPrep confound strategy selection, and derivative discovery details.
- Use `../plotting-reporting/SKILL.md` for figure styling, interactive views,
  report rendering details, and optional plotting dependency setup.
- Do not use this sub-skill for decoding, searchlight, classification,
  regression prediction, connectivity, or connectome workflows.

## Fast Operating Rules

- Prefer explicit `t_r`, `slice_time_ref`, `mask_img`, and per-run events or
  design matrices; route upstream data preparation to the sibling skills.
- Inspect `model.design_matrices_` before contrasts; expression contrasts are
  safer than numeric vectors when runs have different column orders or names.
- Set `minimize_memory=False` only when voxelwise residuals, predictions,
  R-squared, or MSE are needed after fitting.
- Keep BIDS workflows local: `first_level_from_bids` reads an existing dataset
  and derivatives tree; it does not download datasets.
- Treat thresholding choices as statistical decisions: document whether the
  workflow uses FPR, FDR, Bonferroni, explicit thresholds, cluster extent,
  permutation inference, TFCE, one-sided, or two-sided tests.

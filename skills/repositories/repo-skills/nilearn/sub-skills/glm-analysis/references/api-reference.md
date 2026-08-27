# GLM API Reference

This reference summarizes the Nilearn GLM APIs most useful to coding agents.
It assumes data are already prepared as Niimg-like objects, surface images, or
file paths; route preprocessing and confound selection to sibling skills.

## Imports

```python
from nilearn.glm import cluster_level_inference, threshold_stats_img
from nilearn.glm.first_level import (
    FirstLevelModel,
    first_level_from_bids,
    make_first_level_design_matrix,
)
from nilearn.glm.second_level import (
    SecondLevelModel,
    make_second_level_design_matrix,
    non_parametric_inference,
)
```

For reporting, prefer fitted model methods:

```python
report = model.generate_report(contrasts={"A-B": "A - B"})
report.save_as_html("glm_report.html")
```

`nilearn.reporting.make_glm_report` remains available in this checkout but is
scheduled to be replaced by `generate_report` on the fitted model.

## Design Matrix Functions

| API | Use | Key defaults and notes |
| --- | --- | --- |
| `make_first_level_design_matrix(frame_times, events=None, hrf_model="glover", drift_model="cosine", high_pass=0.01, drift_order=1, fir_delays=None, add_regs=None, add_reg_names=None, min_onset=-24, oversampling=50)` | Build one run's first-level design matrix as a pandas `DataFrame`. | `events` require `onset` and `duration`; `trial_type` and `modulation` are optional. DataFrame `add_regs` columns become regressor names. Column names must be unique. |
| `make_second_level_design_matrix(subjects_label, confounds=None)` | Build a group design matrix with subject-aligned confounds and `intercept`. | `confounds` must include `subject_label`; every subject must have exactly one confound row; NaN values are rejected. |

HRF model strings include `"glover"`, `"spm"`, derivative variants, dispersion
variants, and `"fir"` with `fir_delays`. Drift models include `"cosine"`,
`"polynomial"`, and `None`.

## FirstLevelModel

Constructor:

```python
FirstLevelModel(
    t_r=None,
    slice_time_ref=0.0,
    hrf_model="glover",
    drift_model="cosine",
    high_pass=0.01,
    drift_order=1,
    fir_delays=None,
    min_onset=-24,
    mask_img=None,
    target_affine=None,
    target_shape=None,
    smoothing_fwhm=None,
    memory=None,
    memory_level=1,
    standardize=False,
    signal_scaling=0,
    noise_model="ar1",
    verbose=0,
    n_jobs=1,
    minimize_memory=True,
    subject_label=None,
    random_state=None,
    reports=True,
)
```

Primary methods:

| Method | Purpose | Notes |
| --- | --- | --- |
| `fit(run_imgs, events=None, confounds=None, sample_masks=None, design_matrices=None, bins=100)` | Fit one or more runs. | If `design_matrices` are supplied, `events`, `confounds`, and design-generation parameters such as `t_r`, `hrf_model`, and `drift_model` are ignored for design construction. |
| `compute_contrast(contrast_def, stat_type=None, output_type="z_score")` | Compute first-level contrast images. | `contrast_def` can be an expression string, vector, or one item per run. `output_type` accepts `"z_score"`, `"stat"`, `"p_value"`, `"effect_size"`, `"effect_variance"`, or `"all"`. |
| `generate_report(contrasts=None, title=None, bg_img="MNI152TEMPLATE", threshold=None, alpha=0.001, cluster_threshold=0, height_control="fpr", two_sided=False, ...)` | Build an HTML GLM report. | Requires a fitted model for design-matrix and mask sections. Plotting/report optional dependencies affect rendered content. |

Important fitted attributes:

| Attribute | Meaning |
| --- | --- |
| `design_matrices_` | List of per-run first-level design matrices. Always inspect before contrast expressions or vectors. |
| `masker_` | Fitted masker used to transform data and inverse-transform maps. |
| `labels_`, `results_` | Per-run GLM result containers. With `minimize_memory=True`, result objects are simplified. |
| `fir_delays_` | Actual FIR delays used during fit. |
| `n_elements_` | Number of voxels or vertices in the fitted mask. |
| `standardize_` | Effective standardization after reconciling `standardize` and `signal_scaling`. |

Voxelwise diagnostic accessors such as residuals, normalized residuals,
predicted signal, SSE, R-squared, and MSE require `minimize_memory=False` at
model initialization.

## first_level_from_bids

Signature shape:

```python
models, run_imgs, events, confounds = first_level_from_bids(
    dataset_path,
    task_label,
    space_label=None,
    sub_labels=None,
    exclude_subjects=None,
    img_filters=None,
    t_r=None,
    slice_time_ref=None,
    hrf_model="glover",
    drift_model="cosine",
    high_pass=0.01,
    drift_order=1,
    fir_delays=None,
    min_onset=-24,
    mask_img=None,
    target_affine=None,
    target_shape=None,
    smoothing_fwhm=None,
    memory=None,
    memory_level=1,
    standardize=False,
    signal_scaling=0,
    noise_model="ar1",
    verbose=0,
    n_jobs=1,
    minimize_memory=True,
    derivatives_folder="derivatives",
    **kwargs,
)
```

`kwargs` prefixed with `confounds_` are forwarded to fMRIPrep confound loading.
When `t_r` or `slice_time_ref` is `None`, Nilearn attempts to infer values from
BIDS metadata; if inference fails, warnings may be emitted or defaults used.
`mask_img="derivatives"` intersects per-run derivative masks for a subject.
The returned model objects are not fitted; call `model.fit(run_imgs[i],
events=events[i], confounds=confounds[i])` for each subject.

## SecondLevelModel

Constructor:

```python
SecondLevelModel(
    mask_img=None,
    target_affine=None,
    target_shape=None,
    smoothing_fwhm=None,
    memory=None,
    memory_level=1,
    verbose=0,
    n_jobs=1,
    minimize_memory=True,
    reports=True,
)
```

Primary methods:

| Method | Purpose | Notes |
| --- | --- | --- |
| `fit(second_level_input, confounds=None, design_matrix=None)` | Fit a group model. | Inputs can be a DataFrame with `subject_label`, `map_name`, `effects_map_path`; a list/series of Niimg-like maps; a 4D Niimg; a list of surface images; or fitted `FirstLevelModel` objects. |
| `compute_contrast(second_level_contrast=None, first_level_contrast=None, second_level_stat_type=None, output_type="z_score")` | Compute group contrast images. | `first_level_contrast` selects effect maps from first-level model inputs. Output types match first-level contrasts. |
| `generate_report(contrasts=None, first_level_contrast=None, title=None, ...)` | Build a second-level HTML report. | `first_level_contrast` is needed when the input is fitted first-level models and the report must derive subject maps. |

Important fitted attributes:

| Attribute | Meaning |
| --- | --- |
| `second_level_input_` | Stored input maps, DataFrame, or first-level models. |
| `design_matrix_` | Group-level design matrix used for contrasts. |
| `masker_`, `n_elements_` | Fitted masker and number of modeled voxels or vertices. |
| `labels_`, `results_` | Filled after `compute_contrast`; not available immediately after `fit` for model diagnostics. |

## Non-Parametric Group Inference

```python
non_parametric_inference(
    second_level_input,
    confounds=None,
    design_matrix=None,
    second_level_contrast=None,
    first_level_contrast=None,
    mask=None,
    smoothing_fwhm=None,
    model_intercept=True,
    n_perm=10000,
    two_sided_test=False,
    random_state=None,
    n_jobs=1,
    verbose=0,
    threshold=None,
    tfce=False,
)
```

With default `threshold=None` and `tfce=False`, it returns a negative-log10
voxel-level FWER p-value image. If `threshold` or `tfce=True` is requested, it
returns a dictionary including `t`, `logp_max_t`, and relevant cluster or TFCE
maps. Cluster-level inference and TFCE are not implemented for surface data in
this API path; Nilearn warns and disables those options for surface inputs.

## Thresholding and Cluster Output

| API | Purpose | Notes |
| --- | --- | --- |
| `threshold_stats_img(stat_img=None, mask_img=None, alpha=0.001, threshold=None, height_control="fpr", cluster_threshold=0, two_sided=True)` | Convert statistical criteria into a thresholded map and used threshold. | `height_control` can be `"fpr"`, `"fdr"`, `"bonferroni"`, or `None`. When `height_control=None`, `threshold` is interpreted directly on the statistic scale. |
| `cluster_level_inference(stat_img, mask_img=None, threshold=3.0, alpha=0.05, verbose=0)` | Estimate true discovery proportion within clusters over one or more z thresholds. | Accepts volume or surface statistical maps. Default threshold behavior has a future-change warning in this checkout. |
| `nilearn.reporting.get_clusters_table(stat_img, stat_threshold, cluster_threshold=None, two_sided=False, min_distance=8.0, return_label_maps=False)` | Produce a pandas table of cluster peaks. | Use after computing or thresholding a stat map. Route table presentation and plotting details to plotting/reporting guidance. |

## Contrast Conventions

- Expression contrasts are evaluated against design matrix column names, for
  example `"face - scrambled"` or `"condition_a + condition_b"`.
- Numeric vectors must match the current design matrix column count and order.
- Multi-run first-level models accept one expression/vector per run; a single
  contrast is reused over runs with a warning when multiple runs are fitted.
- For second-level one-sample tests, the default intercept-only design usually
  pairs with `second_level_contrast="intercept"` or `None` when the design has
  only one column.
- `output_type="all"` returns a dictionary containing z-score, statistic,
  p-value, effect-size, and effect-variance images.

# GLM Troubleshooting

Use this matrix to debug Nilearn GLM workflow failures without reading the
source checkout. Start by printing design matrix columns, row counts, input
image counts, and contrast definitions.

## Events and Design Matrices

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Error mentions missing event keys. | Events lack required `onset` or `duration` columns. | Add numeric onset and duration columns in seconds. `trial_type` and `modulation` are optional. |
| All events are modeled as one condition named `dummy`. | Events table omits `trial_type`. | Add a `trial_type` column with stable condition names before building the design. |
| Early events disappear or regressors are unexpectedly empty. | Event onset is earlier than `frame_times[0] + min_onset`; default `min_onset` is `-24`. | Check onset origin and either align event timing to scans or intentionally adjust `min_onset`. |
| Extra regressor shape error. | `add_regs` row count differs from `len(frame_times)`. | Resample or trim confounds to the retained scan count before calling `make_first_level_design_matrix`. |
| Extra regressor names error. | `add_reg_names` length differs from number of extra regressors. | Pass one name per regressor or use a DataFrame so column names are used automatically. |
| Duplicate design column error. | Event names, derivative names, drift names, or confound names collide. | Rename conditions or confounds so every design matrix column is unique. |
| Singular second-level design warning. | Confounds and intercept are collinear or too many covariates are included for the subject count. | Remove redundant covariates, center continuous covariates, or simplify the design. |

## Timing, HRF, and Drift

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `t_r not given` during first-level fit. | The model is asked to generate design matrices but `t_r` is `None`. | Supply `t_r` in seconds or pass explicit `design_matrices`. |
| Error says repetition time must be positive. | `t_r` is not numeric or is non-positive. | Use a positive float, for example `t_r=2.0`. |
| Error says `slice_time_ref` must be between 0 and 1. | Slice timing reference is expressed outside the fraction-of-TR range. | Use a fraction such as `0.0`, `0.5`, or `StartTime / RepetitionTime`. |
| Design appears overspecified with high-pass confounds. | fMRIPrep high-pass confounds are combined with GLM cosine or polynomial drifts. | Inspect the design matrix and avoid duplicate high-pass modeling when possible. |
| FIR contrast names are surprising. | `hrf_model="fir"` expands each condition by delays. | Inspect `design.columns`; contrast FIR regressors by the generated names or build vectors explicitly. |

## First-Level Fitting and Contrasts

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Events or confounds seem ignored. | `fit(..., design_matrices=...)` was supplied. | Either pass explicit design matrices only, or omit `design_matrices` and let events/confounds generate them. |
| Multi-run contrast fails or warns about different columns. | One contrast vector/expression is reused across runs with different columns or order. | Inspect every `model.design_matrices_` item and pass a list of per-run expressions or vectors. |
| Contrast expression fails with an unknown name. | Expression uses condition labels that are not design matrix column names. | Use exact `design.columns` names; account for derivative/FIR suffixes and renamed conditions. |
| Numeric contrast shape mismatch. | Vector length does not match the design matrix column count. | Prefer expression contrasts or rebuild one vector per run using each design's columns. |
| Need residuals, predictions, R-squared, SSE, or MSE but an attribute error is raised. | Model was initialized with `minimize_memory=True`. | Refit with `minimize_memory=False`; do this only when diagnostic maps are required. |
| Surface and volume inputs fail compatibility checks. | Mask/image types or surface meshes are mixed. | Keep volume data with Nifti masks and surface data with surface masks/images; route conversion decisions to data preprocessing guidance. |

## BIDS Helper

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No matching BIDS files are found. | `task_label`, `space_label`, `img_filters`, or `derivatives_folder` do not match derivative names. | Verify labels such as `_task-..._`, `_space-..._`, and filters like `("desc", "preproc")`. |
| Unknown keyword argument error. | Extra keyword does not start with `confounds_`. | Rename confound-loading options with the `confounds_` prefix or pass regular model parameters directly. |
| TR warning or wrong TR. | BIDS metadata are missing or disagree with supplied `t_r`. | Supply an explicit `t_r` only when it is correct; otherwise repair metadata upstream. |
| `slice_time_ref` warning defaults to 0.0. | Metadata cannot infer slice timing start time. | Provide `slice_time_ref` explicitly as a fraction of TR. |
| Confounds contain NaNs after loading. | Some fMRIPrep confound columns have initial NaNs or missing values. | `first_level_from_bids` replaces first-row NaNs in returned confounds, but inspect remaining NaNs before fitting. |
| Derivative mask behavior is unexpected. | `mask_img="derivatives"` intersects relevant derivative masks for each subject. | Use an explicit mask when group comparability or a different mask policy is required. |

## Second-Level and Non-Parametric Inference

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Second-level list input error says at least two inputs are needed. | A list with fewer than two maps or first-level models was supplied. | Provide at least two subject maps/models or use a different single-image analysis strategy. |
| DataFrame second-level input error mentions missing columns. | Input DataFrame lacks `subject_label`, `map_name`, or `effects_map_path`. | Add all three columns and ensure paths point to subject effect maps. |
| Confounds cannot be matched to subjects. | `subject_label` missing, duplicated, or absent for at least one subject. | Ensure exactly one confound row per modeled subject. |
| Design rows and effect maps mismatch. | Number of rows in `design_matrix` differs from number of subject maps. | Rebuild design from the exact subject list used for maps. |
| First-level model input with confounds fails. | Fitted first-level models lack `subject_label`. | Set `first_level.subject_label = "01"` or construct models with `subject_label`. |
| Non-parametric surface cluster/TFCE options are disabled. | Current `non_parametric_inference` does not implement cluster-level or TFCE analysis for surface data. | Use voxel-level permutation output for surfaces or switch to volume data for cluster/TFCE workflow. |

## Thresholding and Reports

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Threshold value is ignored. | `threshold_stats_img` only uses `threshold` when `height_control=None`. | Set `height_control=None` for explicit statistic thresholds or remove `threshold` when using FPR/FDR/Bonferroni. |
| Error says `stat_img` cannot be `None`. | FDR or Bonferroni thresholding needs map data. | Pass `stat_img`; only FPR and explicit threshold calculations can return a threshold without an image. |
| Cluster threshold error. | `cluster_threshold` is negative. | Use `0` for no cluster extent threshold or a positive voxel-count threshold. |
| Report has no contrast/statistical-map section. | Report generated without contrasts or before fitting. | Fit the model, then pass a contrast string/list/dict to `generate_report`. |
| Report rendering or plots are missing. | Optional plotting/report dependencies are unavailable. | Keep core GLM code independent; route optional dependency setup and rendering details to plotting/reporting guidance. |
| `make_glm_report` emits a future warning. | The module-level report helper is planned to give way to `model.generate_report`. | Prefer `model.generate_report(...)` on fitted first- or second-level models. |

## Minimal Debug Print Block

```python
print("n designs", len(model.design_matrices_))
for index, design in enumerate(model.design_matrices_):
    print(index, design.shape)
    print(design.columns.tolist())
print("contrast", contrast_definition)
```

For second-level models:

```python
print(model.design_matrix_)
print("n subjects/maps", len(second_level_input))
print("contrast", second_level_contrast)
```

# GLM Workflows

These recipes are designed for local, no-download use. They show the shape of
correct Nilearn GLM code while leaving image preparation, BIDS discovery, and
plot styling to sibling skills.

## No-Download Design Matrix Smoke Recipe

Use this to validate timing, event columns, HRF choice, drifts, and contrast
names before fitting images.

```python
import numpy as np
import pandas as pd
from nilearn.glm.first_level import make_first_level_design_matrix

n_scans = 120
t_r = 2.0
frame_times = np.arange(n_scans) * t_r

events = pd.DataFrame(
    {
        "trial_type": ["faces", "houses", "faces", "houses"],
        "onset": [10.0, 30.0, 70.0, 90.0],
        "duration": [2.0, 2.0, 2.0, 2.0],
    }
)
confounds = pd.DataFrame(
    {
        "motion_x": np.zeros(n_scans),
        "motion_y": np.linspace(-1.0, 1.0, n_scans),
    }
)

design = make_first_level_design_matrix(
    frame_times,
    events=events,
    hrf_model="glover + derivative",
    drift_model="cosine",
    high_pass=0.01,
    add_regs=confounds,
)
print(design.columns.tolist())
```

Alternatively run the bundled smoke script:

```bash
python scripts/make_design_matrix_smoke.py --n-scans 120 --tr 2.0
```

Expected design checks:

- Number of rows equals number of scans.
- Event-related columns use the expected `trial_type` names plus any derivative
  suffixes introduced by the HRF model.
- Added regressors have stable, unique names.
- Drift columns and `constant` are present unless `drift_model` is changed.
- No NaNs are present and all column names are unique.

## First-Level Fit and Contrast Checklist

1. Prepare one Niimg-like or surface image per run, with matching field of view
   or compatible surface mesh. Route image loading, masking, resampling, and
   signal preparation to sibling skills.
2. Prepare one events table per run with `onset` and `duration`, optional
   `trial_type`, and optional `modulation`.
3. Prepare one confounds table per run only after matching its row count to the
   run's number of retained volumes.
4. Decide whether to let `FirstLevelModel` create design matrices from events
   and confounds or to pass explicit `design_matrices`. Do not mix the two
   expecting both to contribute; explicit design matrices take precedence.
5. Fit the model and inspect `model.design_matrices_` before contrasts.
6. Use expression contrasts when possible, especially across multiple runs.
7. Use `output_type="all"` if downstream code needs effect-size or variance
   maps, not only z maps.
8. Use `minimize_memory=False` only when post-fit residuals, predictions,
   R-squared, SSE, or MSE are required.

Example shape:

```python
from nilearn.glm.first_level import FirstLevelModel

model = FirstLevelModel(
    t_r=2.0,
    slice_time_ref=0.5,
    hrf_model="glover",
    drift_model="cosine",
    high_pass=0.01,
    noise_model="ar1",
    mask_img=mask_img,
    smoothing_fwhm=5.0,
    reports=True,
)
model = model.fit(run_imgs, events=events, confounds=confounds)

for run_index, design in enumerate(model.design_matrices_):
    print(run_index, design.columns.tolist())

z_map = model.compute_contrast("faces - houses", output_type="z_score")
all_maps = model.compute_contrast("faces - houses", output_type="all")
```

For a two-run model where column names differ, pass one expression per run:

```python
contrast = ["faces - houses", "face_condition - house_condition"]
z_map = model.compute_contrast(contrast, output_type="z_score")
```

## First-Level BIDS Helper Workflow

Use `first_level_from_bids` when a local BIDS dataset with derivatives already
exists and the task needs a model plus per-subject fit inputs.

Prerequisites:

- `dataset_path` points to a BIDS root containing subject folders and a
  derivatives folder.
- `task_label` matches `_task-<label>_` file names.
- `space_label` and `img_filters` identify the derivative BOLD files, commonly
  including filters such as `("desc", "preproc")`.
- BIDS metadata contain `RepetitionTime` or the workflow supplies `t_r`.
- `slice_time_ref` is supplied or inferable from metadata; if inference fails,
  Nilearn may set it to `0.0` with a warning.
- Confound loading choices are expressed with `confounds_` keyword prefixes.

Example shape:

```python
from nilearn.glm.first_level import first_level_from_bids

models, imgs, events, confounds = first_level_from_bids(
    dataset_path=bids_root,
    task_label="main",
    space_label="MNI152NLin2009cAsym",
    img_filters=[("desc", "preproc")],
    derivatives_folder="derivatives",
    confounds_strategy=("motion", "wm_csf"),
    confounds_motion="derivatives",
    confounds_wm_csf="basic",
)

for model, subject_imgs, subject_events, subject_confounds in zip(
    models, imgs, events, confounds, strict=True
):
    model.fit(subject_imgs, events=subject_events, confounds=subject_confounds)
```

If `confounds_strategy` includes high-pass terms while the GLM also uses a
cosine drift, inspect the design matrix carefully because the filters can be
duplicate or conflicting.

## Second-Level One-Sample Workflow

Use this when each subject contributes one first-level contrast map and the
question is whether the group mean differs from zero.

```python
import pandas as pd
from nilearn.glm.second_level import SecondLevelModel

second_level_input = [subject_01_effect_map, subject_02_effect_map]
design_matrix = pd.DataFrame(
    [1.0] * len(second_level_input), columns=["intercept"]
)

model = SecondLevelModel(mask_img=group_mask, smoothing_fwhm=None)
model = model.fit(second_level_input, design_matrix=design_matrix)
z_map = model.compute_contrast(
    second_level_contrast="intercept",
    output_type="z_score",
)
```

For fitted first-level model inputs:

```python
model = SecondLevelModel(mask_img=group_mask)
model = model.fit(first_level_models, design_matrix=design_matrix)
z_map = model.compute_contrast(
    second_level_contrast="intercept",
    first_level_contrast="faces - houses",
)
```

When confounds are needed, build a `confounds` DataFrame with one row per
subject and a `subject_label` column, then call
`make_second_level_design_matrix(subjects_label, confounds=confounds)`.

## Non-Parametric Second-Level Workflow

Use permutation inference when parametric assumptions are not desired or when a
family-wise error corrected p-value map is requested.

```python
from nilearn.glm.second_level import non_parametric_inference

neg_log10_p_map = non_parametric_inference(
    second_level_input,
    design_matrix=design_matrix,
    second_level_contrast="intercept",
    mask=group_mask,
    n_perm=1000,
    two_sided_test=True,
    random_state=0,
    n_jobs=1,
)
```

For cluster-level or TFCE outputs, pass `threshold=<p_scale_threshold>` or
`tfce=True`; expect a dictionary of maps. Avoid these options for surface data
because the current API warns and disables cluster/TFCE inference there.

## Threshold and Cluster Table Workflow

A typical z-map thresholding sequence is:

```python
from nilearn.glm import threshold_stats_img
from nilearn.reporting import get_clusters_table

thresholded_map, threshold = threshold_stats_img(
    z_map,
    alpha=0.05,
    height_control="fdr",
    cluster_threshold=10,
    two_sided=True,
)
clusters = get_clusters_table(
    z_map,
    stat_threshold=threshold,
    cluster_threshold=10,
    two_sided=True,
)
```

Selection guidance:

- Use `height_control="fpr"` for uncorrected voxelwise p-value thresholds.
- Use `height_control="fdr"` for Benjamini-Hochberg FDR control.
- Use `height_control="bonferroni"` for stricter voxelwise family-wise control.
- Use `height_control=None` with an explicit statistic-scale `threshold` only
  when the task gives a cluster-forming threshold directly.
- Set `two_sided=True` when both positive and negative effects matter; the
  thresholding function adjusts alpha accordingly.

## GLM Report Workflow

Fit the model first, compute or name contrasts, then generate a report:

```python
report = model.generate_report(
    contrasts={"faces-houses": "faces - houses"},
    title="Faces versus houses",
    threshold=3.09,
    alpha=0.001,
    height_control="fpr",
    cluster_threshold=0,
    two_sided=False,
)
report.save_as_html("faces_houses_report.html")
```

For second-level models backed by first-level model inputs, include
`first_level_contrast` when generating the report if the model must derive the
subject effect maps from each first-level model. Route visual style choices,
HTML rendering details, and optional plotting dependency troubleshooting to the
plotting/reporting sibling skill.

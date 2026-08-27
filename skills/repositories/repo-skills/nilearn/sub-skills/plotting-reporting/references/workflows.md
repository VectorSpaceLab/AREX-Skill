# Plotting and Reporting Workflows

These workflows assume the user already has valid Nilearn-compatible inputs, or
that a tiny synthetic image is acceptable for a no-network smoke check. Do not
fetch datasets unless the user explicitly asks for a real dataset example.

## Static Volume Plot in Headless CI

Use this when the deliverable is a PNG/PDF/SVG from a stat map, anatomical
image, ROI, atlas, EPI image, or glass brain.

1. Set a non-interactive backend before importing plotting:
   `import matplotlib; matplotlib.use("Agg")`.
2. Choose the function by semantics: `plot_stat_map` for t/z maps, `plot_roi`
   for masks/labels, `plot_prob_atlas` for 4D maps, `plot_anat`/`plot_epi` for
   backgrounds, `plot_glass_brain` for projections, or `plot_img` for generic
   slices.
3. Specify `output_file=...` to let Nilearn save and close the figure.
4. Make display choices explicit: `threshold`, `display_mode`, `cut_coords`,
   `black_bg`, `cmap`, `vmin`, `vmax`, `symmetric_cbar`, and `radiological`.
5. Avoid `plotting.show()` in CI. If no `output_file` is used, close the
   returned display with `.close()`.

Minimal pattern:

```python
import matplotlib
matplotlib.use("Agg")

from nilearn import plotting

plotting.plot_stat_map(
    stat_img,
    threshold=3.1,
    display_mode="ortho",
    cut_coords=(0, 0, 0),
    symmetric_cbar=True,
    output_file="stat_map.png",
)
```

## Interactive Volume View

Use this when the user wants an embeddable HTML artifact rather than a static
image.

1. Prefer `view_img` for a 3D statistical map and optional background.
2. Set `threshold`, `symmetric_cmap`, `opacity`, `radiological`, and
   `show_lr` deliberately.
3. Save with `.save_as_html(path)` for reproducibility.
4. Do not call `.open_in_browser()` from automated jobs unless the user asked
   for a local browser launch.

Pattern:

```python
from nilearn import plotting

view = plotting.view_img(
    stat_img,
    threshold=3.1,
    title="Thresholded statistic",
    radiological=False,
)
view.save_as_html("stat_map_view.html")
```

## Surface Plot or Surface HTML

Use this after surface data and meshes are already validated by the surface
workflows sub-skill.

1. Confirm whether data is mesh-native (`surf_map`, `stat_map`, `roi_map`) or a
   volume that needs projection (`plot_img_on_surf` or `view_img_on_surf`).
2. For reliable static files in CI, start with `engine="matplotlib"` and
   `output_file=...`.
3. Use `engine="plotly"` only when interactivity is needed and Plotly is
   installed. For PNG export with Plotly, also require Kaleido and Chrome.
4. Use `view_surf(..., engine="niivue")` when a Niivue HTML surface view is
   desired; save the view as HTML and expect browser/WebGL rendering.
5. Choose `hemi`, `view`, `threshold`, `bg_map`, `bg_on_data`, colorbar limits,
   and `symmetric_cbar`/`symmetric_cmap` explicitly.
6. Save HTML view objects with `.save_as_html(...)`.

Static pattern:

```python
from nilearn import plotting

plotting.plot_surf_stat_map(
    surf_mesh,
    stat_map=surface_stat,
    bg_map=background,
    hemi="left",
    view="lateral",
    engine="matplotlib",
    threshold=2.0,
    output_file="surface_stat_left.png",
)
```

Interactive pattern:

```python
from nilearn import plotting

view = plotting.view_surf(
    surf_mesh,
    surf_map=surface_stat,
    hemi="left",
    view="left",
    threshold=2.0,
    engine="plotly",  # or "niivue" for a Niivue HTML view
)
view.save_as_html("surface_stat_left.html")
```

## Connectome, Marker, Matrix, and Event Plots

Use these after adjacency matrices, node coordinates, design matrices, or event
tables have been produced by the appropriate analysis workflow.

- For static connectomes, use `plot_connectome(adjacency, coords,
  edge_threshold=..., output_file=...)`.
- For marker maps, use `plot_markers(values, coords, node_threshold=...,
  output_file=...)`.
- For interactive connectomes/markers, use `view_connectome` or `view_markers`
  and save HTML.
- For design matrices, contrasts, events, or correlations, use
  `plot_design_matrix`, `plot_contrast_matrix`, `plot_event`, and
  `plot_design_matrix_correlation` with `output_file` where available.
- For a generic connectivity matrix heatmap, use `plot_matrix`; if a file is
  required, save the active Matplotlib figure yourself because `plot_matrix`
  does not take `output_file`.

Matrix save pattern:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from nilearn import plotting

plotting.plot_matrix(correlation, labels=labels, tri="lower")
plt.savefig("correlation_matrix.png", bbox_inches="tight")
plt.close()
```

## GLM Cluster Table and HTML Report

Use this after a fitted GLM and contrast/stat map exist. Fit models and compute
contrasts in `../glm-analysis/SKILL.md`; return here for reporting.

1. Decide thresholding in statistical terms before plotting: explicit numeric
   threshold, FPR/FDR/Bonferroni, permutation threshold, cluster extent,
   `two_sided`, and `min_distance`.
2. Use `get_clusters_table(stat_img, stat_threshold=..., cluster_threshold=...,
   two_sided=...)` to produce a pandas table of peaks and clusters.
3. Use `model.generate_report(...)` for fitted first- or second-level GLM
   objects. `make_glm_report(...)` is a compatibility wrapper that delegates to
   the model and may warn about future deprecation.
4. Save `HTMLReport` objects with `.save_as_html(path)`. Avoid opening a
   browser in scripts.

Pattern:

```python
from nilearn.reporting import get_clusters_table

clusters = get_clusters_table(
    stat_img,
    stat_threshold=3.1,
    cluster_threshold=10,
    two_sided=True,
)
clusters.to_csv("clusters.csv", index=False)

report = model.generate_report(
    contrasts="condition_a - condition_b",
    threshold=3.1,
    cluster_threshold=10,
    two_sided=True,
    plot_type="slice",
)
report.save_as_html("glm_report.html")
```

## Masker Report Handoff

Many fitted Nilearn maskers expose HTML reports through `generate_report()` or
rich HTML display once fitted. Route creation, fitting, labels/maps, and signal
extraction to `../maskers-regions/SKILL.md`, then use this sub-skill only for
report handling:

1. Confirm the masker is fitted; unfitted estimators report that `.fit()` is
   required.
2. Call `report = masker.generate_report()` when the estimator supports it.
3. Save with `report.save_as_html("masker_report.html")`.
4. If plotting backends are unavailable, expect reports to be generated with
   missing figures or backend warnings rather than full visual content.

## Image Comparison Workflow

Use `plot_img_comparison` or `plot_bland_altman` when the request is to compare
outputs, not to visualize one final map.

1. Confirm input images are aligned and comparable; route resampling/alignment
   to `../data-io-signal/SKILL.md`.
2. For many images, use `plot_img_comparison(ref_imgs, src_imgs, output_dir=...)`.
3. For one pair and distributional agreement, use `plot_bland_altman(ref_img,
   src_img, ...)` and close/save the Matplotlib figure.
4. Document mask choice if a masker is used to define comparison voxels.

## No-Network Synthetic Smoke Pattern

For quick checks, build tiny synthetic images with NumPy and Nibabel instead of
fetching datasets. Use values above and below threshold so `plot_stat_map` and
`get_clusters_table` exercise meaningful paths.

```python
import numpy as np
import nibabel as nib

shape = (9, 9, 9)
data = np.zeros(shape, dtype=float)
data[4, 4, 4] = 5.0
data[2, 2, 2] = -4.5
stat_img = nib.Nifti1Image(data, np.eye(4))
```

Then save a static figure with `output_file` and run a cluster table with an
explicit threshold.

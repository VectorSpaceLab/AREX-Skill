# Plotting and Reporting API Reference

This reference summarizes Nilearn plotting/reporting entry points that agents
most often need. Route image, surface, GLM, masker, and connectivity data
creation to sibling Nilearn sub-skills; this sub-skill starts once valid inputs
exist or synthetic no-network inputs are being made for a check.

## Static Volume Plotters

Import from `nilearn.plotting`.

| Task | Function | Core inputs | Notes |
| --- | --- | --- | --- |
| General image slices | `plot_img(img, ...)` | 3D niimg-like image | Neutral defaults; supports `bg_img`, `threshold`, `display_mode`, `cut_coords`, `cmap`, `colorbar`, `radiological`. |
| Anatomical background | `plot_anat(anat_img=..., ...)` | anatomical image or default template | Uses anatomical-style grayscale defaults; `black_bg="auto"` and `dim="auto"` are common. |
| EPI/T2* image | `plot_epi(epi_img=None, ...)` | EPI image | Dark background by default. |
| ROI or mask overlay | `plot_roi(roi_img, bg_img=..., ...)` | label/mask image plus optional background | Default `resampling_interpolation="nearest"`; supports `view_type`, `linewidths`, `alpha`. |
| Probabilistic atlas | `plot_prob_atlas(maps_img, ...)` | 4D maps image | Choose `view_type="filled_contours"`, `"contours"`, or automatic behavior. |
| Statistical map | `plot_stat_map(stat_map_img, ...)` | 3D stat image | Common for t/z/F maps; supports `threshold`, `symmetric_cbar`, `vmin`, `vmax`, transparency, and background. |
| Glass brain projection | `plot_glass_brain(stat_map_img, ...)` | 3D stat image | Maximum-intensity projection; set `plot_abs=False` for signed positive/negative maps. |
| Carpet plot | `plot_carpet(img, mask_img=None, ...)` | 4D image plus optional mask | Visualizes time by voxel; optional `t_r`, `detrend`, `standardize`, `mask_labels`. |
| Bland-Altman/image comparison | `plot_bland_altman`, `plot_img_comparison` | image pairs or lists | Use when comparing image sets, not for routine map display. |

Common static parameters include `output_file`, `display_mode`, `cut_coords`,
`figure`, `axes`, `title`, `annotate`, `draw_cross`, `black_bg`, `colorbar`,
`cbar_tick_format`, `vmin`, `vmax`, and `radiological`. Valid volume display
modes include `"ortho"`, single axes such as `"x"`, `"y"`, `"z"`, paired axes
such as `"xz"`, `"yx"`, `"yz"`, and layout modes such as `"tiled"` or
`"mosaic"`. Glass-brain/connectome displays also support projection modes such
as `"l"`, `"r"`, `"lr"`, `"lzr"`, `"lyr"`, `"lzry"`, and `"lyrz"`.

## Connectome and Marker Plotters

| Task | Function | Core inputs | Notes |
| --- | --- | --- | --- |
| Static connectome | `plot_connectome(adjacency_matrix, node_coords, ...)` | square adjacency and `(n_nodes, 3)` coordinates | Supports `edge_threshold`, `edge_cmap`, `node_color`, `node_size`, `edge_kwargs`, `node_kwargs`, `radiological`. |
| Static markers | `plot_markers(node_values, node_coords, ...)` | per-node values and coordinates | Supports value thresholds, marker colormap limits, and `radiological`. |
| Interactive connectome | `view_connectome(adjacency_matrix, node_coords, ...)` | square adjacency and coordinates | Returns an HTML view object; save with `.save_as_html(...)`. |
| Interactive markers | `view_markers(marker_coords, ...)` | marker coordinates | Returns an HTML view object; supports marker colors, sizes, labels, and title. |

Connectivity estimation, coordinates from atlases, and region extraction belong
in the connectivity or masker/regions sub-skills before using these functions.

## Matrix, Event, and Design Plotters

| Task | Function | Core inputs | Return style |
| --- | --- | --- | --- |
| Generic matrix | `plot_matrix(mat, title=None, labels=None, ..., tri="full", reorder=False, **kwargs)` | 2D array-like matrix | Matplotlib display/axes object. |
| Contrast vector/matrix | `plot_contrast_matrix(contrast_def, design_matrix, colorbar=True, axes=None, output_file=None)` | contrast plus design matrix | Saves when `output_file` is set. |
| Design matrix | `plot_design_matrix(design_matrix, rescale=True, axes=None, output_file=None)` | pandas design matrix | Saves when `output_file` is set. |
| Event table | `plot_event(model_event, cmap=None, output_file=None, **fig_kwargs)` | BIDS-like events table | Saves when `output_file` is set. |
| Design correlation | `plot_design_matrix_correlation(design_matrix, tri="full", ..., output_file=None, **kwargs)` | pandas design matrix | Useful for collinearity inspection. |

Route event construction, design matrix construction, and contrast validity to
`../glm-analysis/SKILL.md`; this sub-skill covers how to display and save them.

## Surface Plotters and Views

| Task | Function | Core inputs | Engine and return notes |
| --- | --- | --- | --- |
| Surface mesh/map | `plot_surf(surf_mesh=None, surf_map=None, bg_map=None, hemi="left", view=None, engine="matplotlib", ...)` | mesh plus optional data | `engine="matplotlib"` returns a Matplotlib figure-like object; `engine="plotly"` returns a `PlotlySurfaceFigure`. |
| Surface stat map | `plot_surf_stat_map(surf_mesh=None, stat_map=None, bg_map=None, ..., symmetric_cbar="auto", output_file=None, **kwargs)` | mesh plus stat data | Use for scalar statistical maps; supports threshold, colorbar, cbar limits, and background-on-data. |
| Surface ROI/atlas | `plot_surf_roi(surf_mesh=None, roi_map=None, bg_map=None, ..., cmap="gist_ncar", output_file=None, **kwargs)` | mesh plus integer/categorical ROI data | Use nearest/categorical reasoning for ROI data. |
| Volume projected to surface | `plot_img_on_surf(stat_map, surf_mesh="fsaverage5", ..., symmetric_cbar="auto", output_file=None, **kwargs)` | volume image | Projects before plotting; projection details belong to surface/image sub-skills. |
| Interactive surface map | `view_surf(surf_mesh=None, surf_map=None, bg_map=None, ..., engine="plotly", view="left")` | mesh plus optional data | Returns an HTML view object, commonly saved with `.save_as_html(...)`; `engine` may be `"plotly"` or `"niivue"`. |
| Interactive volume-on-surface | `view_img_on_surf(stat_map_img, surf_mesh="fsaverage5", ..., view="left", vol_to_surf_kwargs=None)` | volume image | Returns an HTML view object after projection. |

Surface plotting accepts `hemi` values such as `"left"`, `"right"`, or
`"both"` where supported, and view names such as `"lateral"`, `"medial"`,
`"dorsal"`, `"ventral"`, `"anterior"`, `"posterior"`, or engine-specific
camera choices. Validate mesh/data dimensions in `../surface-workflows/SKILL.md`
before diagnosing plotting.

## Interactive Volume Views

`view_img(stat_map_img, bg_img="MNI152", cut_coords=None, colorbar=True,
title=None, threshold=1e-6, annotate=True, draw_cross=True, black_bg="auto",
cmap=..., symmetric_cmap=True, dim="auto", vmax=None, vmin=None,
resampling_interpolation="continuous", width_view=600, opacity=1,
radiological=False, show_lr=True)` returns a `StatMapView` HTML object.

Use `view_img` when the user wants a portable browser/notebook artifact. It is
not the same as saving a Matplotlib PNG. Save it with `.save_as_html(path)` and
avoid opening a browser in automated jobs.

## Reporting APIs

Import from `nilearn.reporting`.

| Task | Function or class | Core behavior |
| --- | --- | --- |
| Cluster peak table | `get_clusters_table(stat_img, stat_threshold, cluster_threshold=0, two_sided=False, min_distance=8.0, return_label_maps=False)` | Returns a pandas `DataFrame`; with `return_label_maps=True`, returns `(table, label_maps)`. Supports volume and surface stat images. |
| GLM report wrapper | `make_glm_report(model, contrasts=None, first_level_contrast=None, title=None, bg_img="MNI152TEMPLATE", threshold=3.09, alpha=0.001, cluster_threshold=0, height_control="fpr", two_sided=False, min_distance=8.0, plot_type="slice", cut_coords=None, display_mode=None, report_dims=(width, height))` | Calls the fitted model's `generate_report`; newer code can call `model.generate_report(...)` directly. |
| HTML report | `HTMLReport(head_tpl, body, head_values=None)` | Returned by Nilearn report generators; inherits HTML document methods such as `.save_as_html(...)` and `.open_in_browser()`. |

Cluster tables require a statistical image and explicit threshold. `two_sided`
controls whether positive and negative clusters are reported. `cluster_threshold`
is an extent threshold. `min_distance` controls subpeak separation for volume
images; surface images do not use the same spatial subpeak logic.

## `output_file` and Return Objects

- Most static plotters create a display, axes, or figure when `output_file` is
  omitted. The caller owns closing that object.
- Static plotters that use Nilearn's save helper create parent directories,
  save the figure, close it, and return `None` when `output_file` is provided.
- `plot_matrix` has no `output_file`; save the returned Matplotlib object or
  active figure explicitly if a file is needed.
- `plot_img_comparison` uses `output_dir` rather than `output_file`.
- `view_*` functions return HTML view objects; use `.save_as_html(...)` for
  reproducible files and `.open_in_browser()` only for interactive local use.
- `PlotlySurfaceFigure.savefig(path)` writes static images only when Plotly,
  Kaleido, and a compatible Chrome are available. Prefer HTML outputs or the
  Matplotlib engine in constrained CI.

## Dependency and Engine Choices

- `nilearn.plotting` requires Matplotlib for its public plotting imports. The
  plotting extra installs Matplotlib, Plotly, and Kaleido.
- Nilearn sets a non-interactive Matplotlib backend when no display is detected,
  but CI scripts should still set `MPLBACKEND=Agg` or call
  `matplotlib.use("Agg")` before importing `nilearn.plotting`.
- Surface static functions default to the Matplotlib engine unless configured
  otherwise. Use `engine="plotly"` for interactive surface figures only when
  Plotly is installed and browser/renderer behavior is acceptable.
- HTML view functions are best for notebook/browser artifacts and should be
  saved as HTML in headless jobs instead of shown. `view_surf` can render with
  Plotly or Niivue HTML backends; Niivue avoids the Python Plotly dependency but
  still needs a browser/WebGL-capable frontend for interactive use.

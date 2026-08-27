# Plotting and Reporting Troubleshooting

Start by separating input validity from rendering problems. Image shape,
affine, mesh/data alignment, GLM fitting, and masker setup belong to sibling
sub-skills. This page focuses on rendering, output, and report behavior.

## Missing Plotting Dependencies

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Importing `nilearn.plotting` warns that dependencies are missing | Matplotlib is not installed | Install the plotting extra or Matplotlib according to project policy; in public examples phrase this as `nilearn[plotting]`. |
| `engine="plotly"` raises that Plotly is required | Plotly is not installed | Use `engine="matplotlib"` for static surface plots, or install Plotly through the plotting extra. |
| Plotly figure displays but PNG export fails | Kaleido or Chrome is missing | Save HTML instead, switch to Matplotlib, or install Kaleido and a compatible Chrome when static Plotly export is truly required. |
| Browser does not open for a view/report | Headless machine, no browser, blocked display, or notebook mismatch | Save with `.save_as_html(...)`; do not rely on `.open_in_browser()` in CI. |
| Report says no plotting backend detected or figures are missing | Matplotlib/plotting backend unavailable during report generation | Install plotting dependencies or accept a text/table-only report; rerun report generation after backend repair. |

Do not bury broad package installation steps in task code. If environment
mutation is required, route policy decisions to the root Nilearn skill or ask
the user.

## Headless Matplotlib and Figure Lifecycle

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Job hangs or errors with display/backend messages | GUI backend selected on a headless runner | Set `MPLBACKEND=Agg` or call `matplotlib.use("Agg")` before importing `nilearn.plotting`. |
| Many plots make the process slow or memory-heavy | Displays are created but not closed | Prefer `output_file=...`, which saves and closes many static Nilearn plots; otherwise call `.close()` or `plt.close()`. |
| Expected return object is `None` | `output_file` was supplied | This is normal for static plotters using Nilearn's save helper; the artifact is on disk. |
| Output directory did not exist | Static save helper creates parent directories for many plotters | Check the exact path; if using raw Matplotlib or `plot_matrix`, create directories yourself. |
| `plot_matrix` cannot accept `output_file` | It returns a Matplotlib object without that parameter | Use `plt.savefig(path, bbox_inches="tight")` and `plt.close()`. |

## Threshold, Colorbar, and Colormap Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No activation appears | Threshold too high, data below threshold, wrong sign, NaNs, or wrong image | Inspect data range, lower `threshold`, set `two_sided=True` for cluster tables, or verify contrast direction. |
| Colorbar range looks misleading | `vmin`, `vmax`, or `symmetric_cbar`/`symmetric_cmap` conflicts with data sign | For signed t/z maps, use symmetric settings deliberately; for positive-only maps, disable symmetry or set explicit limits. |
| Error about incompatible colorbar limits | Symmetric colorbar requested with incompatible `vmin`/`vmax` | Either remove manual limits or set symmetric limits around zero. |
| Glass brain loses sign information | `plot_abs=True` projects absolute values | Set `plot_abs=False` for positive/negative glass-brain maps. |
| ROI colors look interpolated | Continuous interpolation or continuous colormap used for labels | Use ROI-specific functions and nearest/categorical reasoning; route label image creation to masker/regions. |
| Cluster table is empty | Threshold or cluster extent removes all clusters | Confirm `stat_threshold`, `cluster_threshold`, `two_sided`, and image values; empty tables may be expected. |

For statistical threshold choices, route interpretation to `../glm-analysis/SKILL.md`.

## Orientation and Coordinate Confusion

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Left/right appears flipped relative to expected radiology view | Default neurological display differs from radiological convention | Set `radiological=True` only when the requested convention is radiological; keep `show_lr=True` for interactive views when labels help. |
| Cut coordinates show empty slices | Coordinates are outside image field of view or not in the expected world space | Inspect image affine and shape through image/data sub-skill; choose automatic `cut_coords` or coordinates in world millimeters. |
| Connectome nodes appear misplaced | Node coordinates do not match image/world convention | Verify `node_coords` are `(n_nodes, 3)` world coordinates in the intended space before plotting. |

## Surface Engine and Mesh/Data Mismatch

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Surface plot errors on data length | `surf_map`, `stat_map`, or `roi_map` length does not match mesh vertices | Route to `../surface-workflows/SKILL.md` to validate mesh/data contracts. |
| `hemi` or `view` error | Invalid hemisphere/view for the chosen function or engine | Use supported values such as `left`, `right`, or `both`; for views use lateral/medial/dorsal/ventral/anterior/posterior where supported. |
| Plotly-specific warning says a parameter is not implemented | Some Matplotlib options are unavailable with `engine="plotly"` | Remove that parameter, use a Plotly-supported alternative, or switch to `engine="matplotlib"`. |
| Static surface PNG fails only with Plotly | Plotly image export needs Kaleido and Chrome | Use `engine="matplotlib"` for CI PNGs or save interactive HTML instead. |
| `view_surf` works but `plot_surf(..., engine="plotly")` does not save | Interactive HTML rendering and Plotly static export have different dependencies | Save `.html` for views; use Matplotlib or fully provision Plotly/Kaleido/Chrome for image export. |
| Niivue surface HTML saves but appears blank when opened | Browser/WebGL support, blocked scripts, or frontend rendering issue | Try another browser, confirm WebGL is enabled, or switch `view_surf` back to `engine="plotly"`/static Matplotlib depending on the deliverable. |

## Interactive HTML Views

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| HTML view does not appear in a script | The object is returned but not displayed by a notebook frontend | Call `.save_as_html(path)` and open the file manually if needed. |
| `view_img` warns about threshold or empty data | Threshold removes all visible voxels | Adjust `threshold`, inspect values, or document that no suprathreshold data exists. |
| HTML file is large | Data and JavaScript are embedded for portability | Save only needed views and avoid embedding many high-resolution artifacts in one report. |
| Browser renderer fails for Plotly | Renderer unavailable in the environment | Save HTML or configure a renderer outside the Nilearn code path. |

## GLM and Masker Reports

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Report says estimator is not fitted | `.fit()` was not called or fitted attributes are absent | Route fitting to GLM or masker sub-skill, then regenerate the report. |
| `make_glm_report` emits a future/deprecation warning | The wrapper delegates to model `generate_report` and is slated for deprecation | Prefer `model.generate_report(...)` in new code while understanding old examples may use `make_glm_report`. |
| Report generation warns or omits figures | Plotting backend/dependencies unavailable | Install plotting dependencies or save a limited report; do not claim full visual report verification. |
| GLM report threshold differs from cluster table | Different `threshold`, `height_control`, `alpha`, `cluster_threshold`, or `two_sided` values | Keep report and cluster-table parameters synchronized and document them. |
| Masker report is empty or missing images | Masker did not retain report content or was configured without reporting support | Refit with report-capable settings if supported; route masker configuration to `../maskers-regions/SKILL.md`. |

## Safe Debug Checklist

1. Can `python -c "import nilearn, nilearn.plotting, nilearn.reporting"` import
   with the current environment?
2. Was the Matplotlib backend set before importing `nilearn.plotting` in a
   headless script?
3. Is the input object valid and in the expected space? If not, route upstream.
4. Is the task asking for a static file, a Matplotlib object, or an HTML view?
5. Are optional Plotly/Kaleido/Chrome dependencies actually needed, or can the
   workflow use Matplotlib/HTML instead?
6. Are threshold, colorbar symmetry, and orientation choices explicit enough for
   a future reader to reproduce the visual result?

# Visualization Troubleshooting

Use this checklist when Squidpy plotting code fails or produces unexpected figures.

## Spatial Metadata and Library Routing

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError` or `ValueError` around `adata.uns['spatial']` | Image-backed plotting was requested but Visium-style spatial metadata is absent or incomplete. | For no-image plots, call `sq.pl.spatial_scatter(..., shape=None, img=False, size=...)`. For image overlays, route metadata repair to datasets-and-io and verify `.uns['spatial'][library_id]['images']` and `scalefactors`. |
| `Could not fetch library_id` | `shape` or image metadata needs a valid `library_id`, but the selected `spatial_key` or `.uns['spatial']` layout does not contain it. | Pass `library_id` explicitly, check `spatial_key`, or disable image-backed shape behavior with `shape=None, img=False`. |
| `Found library_id ... but no library_key was specified` | Multiple libraries are selected but Squidpy cannot subset observations by library. | Add a categorical `adata.obs[library_key]` column and pass both `library_key` and the selected `library_id` values. |
| `library_key` missing from `.obs` | The requested library routing column is absent or not propagated after concatenation/subsetting. | Restore the column, make it categorical, and ensure values match the library ids in `.uns['spatial']`. |
| Crops show blank panels | `crop_coord` is outside image-coordinate space or the coordinate origin/orientation was misunderstood. | Confirm coordinates are pixel-space with origin in the top-left. Use a broad crop first, then tighten `(x0, y0, x1, y1)`. |

## Images, Segmentation, and Shapes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Image key ... does not exist` | `img_res_key` does not match stored image keys. | Inspect the available keys under the selected library's `images` mapping and pass the matching `img_res_key`, or pass an image array directly. |
| `No scale_factor found that could match img_res_key` | The scalefactor names do not include the requested image resolution. | Pass `scale_factor` explicitly or repair the scalefactors metadata before image-backed plotting. |
| `Specified size_key ... does not exist and size is None` | Automatic spot sizing cannot find `spot_diameter_fullres` or the requested size key. | Pass `size=<number>` explicitly or provide the expected scalefactor metadata. |
| Segmentation plot says `Cell id ... not found` | `seg_cell_id` is missing from `adata.obs`. | Add an integer cell-id column that maps observations to segmentation labels. |
| Segmentation plot says invalid dtype for `seg_cell_id` | Cell ids are strings/floats rather than integer labels. | Convert ids to integer labels that match the segmentation mask values. |
| Segmentation or image appears shifted/scaled | Segmentation array, image array, coordinates, and scale factors are in different pixel spaces. | Plot with `img=False, seg=True` or `img=True, seg=False` separately, verify dimensions, then re-enable overlays after coordinate/scale alignment. |

## Missing Computed Keys

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Plotter says to run `squidpy.gr.<function>(..., cluster_key=...)` first | The matching graph/statistic result is absent from `adata.uns`. | Route computation to graph-analysis, run the corresponding `sq.gr.*` function, and preserve the same `cluster_key`. |
| Spatial edges do not render or `connectivity_key` is missing | `adata.obsp[connectivity_key]` is absent or empty. | Compute a spatial graph first, usually storing to `spatial_connectivities`, and pass that exact key. |
| `sq.pl.var_by_distance` fails on `design_matrix_key` | `adata.obsm[design_matrix_key]` was not created or was overwritten. | Route design-matrix creation to tools-workflows, rerun `sq.tl.var_by_distance`, and pass the matching key. |
| `Variable ... not found in adata.var or adata.obs` | `var` is neither a gene name nor observation column. | Use a valid `adata.var_names` entry, add the requested observation column, or verify casing. |
| `Can't stack variables and plot covariate at the same time` | `stack_vars=True` and `covariate` are mutually exclusive. | Use faceted variables with a covariate, or stack variables without a covariate. |

## Palettes and Categories

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Categorical plot errors or invalid group selection | `color`/`cluster_key` is not categorical or `groups` contains absent categories. | Convert columns with `adata.obs[key] = adata.obs[key].astype('category')` and verify requested groups are in `.cat.categories`. |
| Colors do not match expectations after subsetting | Stored `adata.uns[f"{key}_colors"]` length/order no longer matches categories. | Delete the stale colors entry or provide `palette=` explicitly. |
| `ligrec` says invalid clusters | `source_groups` or `target_groups` are not present in the ligand-receptor result columns. | Inspect the result's source/target cluster levels and select exact values. |
| `ligrec` says no rows or columns remain after filtering | `means_range`, `pvalue_threshold`, `alpha`, or removal flags filtered out everything. | Relax filters, set `remove_empty_interactions=False` for diagnosis, or verify the underlying `means`/`pvalues` result. |

## Headless Rendering and Saving

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Backend errors such as display connection failures | Matplotlib selected an interactive backend in a headless environment. | Set `MPLBACKEND=Agg` or call `matplotlib.use("Agg")` before importing `matplotlib.pyplot`. |
| A script saves to an unexpected directory | Squidpy `save=` delegates to Scanpy figure settings for relative paths. | For exact paths, request axes where available and call `ax.figure.savefig(path, ...)`, or set Scanpy's figure directory deliberately. |
| `return_ax=True` works for spatial plots but not graph plotters | Not every Squidpy plotter exposes `return_ax`. | For graph heatmaps pass `ax=` where supported; for other graph plotters save through `save=` or use the current Matplotlib figure. |
| Batch plotting consumes memory | Figures remain open in a loop. | Call `matplotlib.pyplot.close("all")` or close each returned figure after saving. |

## Visual Baselines and Version Sensitivity

Squidpy's native plotting tests include image baselines. They are useful evidence for expected coverage, but exact pixels can change across Matplotlib, Seaborn, font, backend, or operating-system versions.

When validating a plotting workflow:

1. Start with smoke checks that assert a figure or axes object is created.
2. Confirm required keys and categories before comparing pixels.
3. If comparing images, record Matplotlib and Seaborn versions and use a tolerance appropriate for antialiasing and font differences.
4. Prefer semantic assertions for generated scripts: output file exists, axes title/labels are set when expected, and no missing-key exception is raised.

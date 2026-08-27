# Cross-cutting troubleshooting

This page covers failures that can show up across multiple OSMnx workflows.
Workflow-specific detail lives in the owning sub-skill.

## Install and import failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ImportError: No module named osmnx` | The package is not installed in the current interpreter. | Install the package itself, then rerun the minimal import check. |
| `pip check` reports broken requirements | A dependency mismatch or partial install is present. | Reinstall the package into a clean environment or repair the missing packages. |
| Errors mentioning geospatial wheels, GEOS, PROJ, GDAL, or compiled extensions | A compiled dependency is missing or incompatible with the Python environment. | Use the supported package manager for a clean install; conda often handles geospatial stacks more reliably than ad hoc source builds. |
| Import errors for `scipy`, `scikit-learn`, `rasterio`, `rio-vrt`, or `matplotlib` | An optional workflow extra was not installed. | Install the relevant extra or narrow the task to a workflow that does not need it. |

## Optional dependency mismatches

- `neighbors` is required for the nearest-node/edge workflow on projected or unprojected graphs when the optional search path is exercised.
- `entropy` is required for orientation entropy.
- `raster` is required for local raster elevation and VRT-backed multi-raster sampling.
- `visualization` is required for static plots and color helpers.

If the task only needs the base package, do not install extras just because they exist.
If the task needs one of the optional workflows above, install the matching extra and rerun the bundled environment check.

## Network and API limits

- OSMnx uses public Nominatim and Overpass services for many acquisition workflows.
- Failures such as empty geocoder responses, `429`/`504`-style service issues, or slow requests are usually data-service problems, not package bugs.
- Keep cache usage, rate limits, and endpoint settings under `data-acquisition` rather than trying to solve them here.

## Headless plotting and image output

- In a headless environment, set `matplotlib.use("Agg")` before importing plotting helpers.
- If a plot saves to the wrong place, set `settings.imgs_folder` or pass an explicit `filepath`.
- If an image helper fails because the graph is missing coordinates, route the problem to `graph-modeling-io` first.

## When to stop and switch sub-skills

- If the problem is a bad graph schema, projection, or file-format mismatch, use `graph-modeling-io`.
- If the problem is query construction, OSM service limits, or XML fallback, use `data-acquisition`.
- If the problem is nearest matching, weights, stats, or bearings, use `routing-analysis`.
- If the problem is elevation, grades, or plots, use `elevation-visualization`.

# Interactive Map Troubleshooting

Use this guide before guessing. Keep backend, credentials, widgets, palettes, and optional network layers separate because the same symptom can have different causes.

## Earth Engine auth, project, and network

Symptoms:

- `ee.Initialize()` fails.
- `Map.addLayer()` fails for a real EE image or feature collection.
- `centerObject()` or Inspector clicks hang or fail when they call `getInfo()`.
- Errors mention missing credentials, unregistered project, permission denied, quota, proxy, SSL, or unreachable Google services.

Actions:

1. If the user only needs map structure, use `geemap.Map(ee_initialize=False)` and postpone real EE calls.
2. If the user needs EE data, ensure they have authenticated and initialized Earth Engine with the intended project.
3. Ask for or document the project id when the environment requires one.
4. Check network/proxy restrictions separately from credentials; retries will not fix a missing account or project.
5. Keep slow remote calls bounded: small regions, explicit scale, and a clear reason before calling `getInfo()`.

Do not blame EE auth for failures from `add_raster`, `add_cog_layer`, or `add_stac_layer` unless the failing object is actually an EE object. Those methods often use local tile serving or third-party tile services.

## Colab or Jupyter kernel restart after install

Symptoms:

- `import geemap` fails immediately after installation.
- Widget classes or JavaScript front-end assets appear missing.
- The notebook shows stale versions after upgrading.

Actions:

1. Restart the Colab runtime or Jupyter kernel after install or upgrade.
2. Re-import geemap after restart.
3. Re-run the smoke script with `--skip-ee-init` to separate import/backend issues from Earth Engine auth.
4. If only widgets fail, continue with the widget display section below.

## `USE_FOLIUM` backend selection

Symptoms:

- Top-level `import geemap` returns a folium map when the user expected ipyleaflet widgets.
- `add_draw_control`, `add_layer_manager`, or `add_inspector` is missing.
- Code behaves differently across terminals, notebooks, or deployment platforms.

Actions:

1. Prefer explicit imports in generated code:
   - `import geemap.geemap as geemap` for ipyleaflet.
   - `import geemap.foliumap as geemap` for folium.
2. Treat any set `USE_FOLIUM` environment variable as a request for folium behavior at top level.
3. If changing `USE_FOLIUM` inside a running process, restart the process or kernel before relying on top-level imports.
4. Run both smoke checks if the user is unsure:
   - `scripts/map_smoke.py --backend ipyleaflet --skip-ee-init`
   - `scripts/map_smoke.py --backend folium --skip-ee-init`

## Basemap catalog and shadowing

Symptoms:

- `geemap.basemaps.get_xyz_dict()` fails because `geemap.basemaps` is not the helper module the user expected.
- A backend map has a `basemaps` object but helper functions such as `xyz_to_leaflet()` are not found.
- A basemap name works in one backend but not another.

Cause:

- Backend modules expose a variable named `basemaps` that contains provider entries. That variable can shadow the helper submodule name in casual imports.

Actions:

```python
import geemap.basemaps as basemap_helpers

xyz = basemap_helpers.get_xyz_dict(free_only=True)
leaflet_layers = basemap_helpers.xyz_to_leaflet()
folium_layers = basemap_helpers.xyz_to_folium()
```

Then choose names that exist in the target backend registry. For compatibility aliases, try `ROADMAP`, `SATELLITE`, `TERRAIN`, or `HYBRID`, but expect provider-backed replacements when Google map environment variables are not set.

## Widget display issues

Symptoms:

- A map object exists but the notebook output is blank.
- Draw tools, Inspector, Layer Manager, toolbar, or layer editor does not render.
- Traitlet or widget front-end errors appear in the browser console.

Actions:

1. Verify the backend is ipyleaflet, not folium, if the user needs geemap widget controls.
2. Restart the notebook kernel after install or upgrade.
3. Confirm ipywidgets and ipyleaflet are installed in the same kernel used by the notebook.
4. In JupyterLab or hosted notebook environments, ensure widget extensions are enabled by the platform.
5. For non-notebook contexts, switch to folium HTML output or `to_html()` instead of expecting bidirectional widgets.
6. If an Inspector result is empty, confirm the target EE layer is visible and Earth Engine calls are authorized.

## Invalid palette, legend, or colorbar values

Symptoms:

- Errors mention `palette must be`, invalid `Box` palette, invalid orientation, min/max scalar type, opacity or alpha scalar type, legend positions, built-in legends, or keys/colors length.

Actions:

- For EE layer visualization, pass `vis_params` as a dictionary. Valid examples:

```python
{"min": 0, "max": 4000, "palette": ["006633", "E5FFCC", "662A00"]}
{"min": 0, "palette": "00FF00"}
```

- For legends, use either `legend_dict={label: color}` or matching `keys=[...]` and `colors=[...]` lists.
- Valid legend positions are `topleft`, `topright`, `bottomleft`, and `bottomright`.
- For ipyleaflet colorbars, use `orientation="horizontal"` or `orientation="vertical"`.
- Keep `min`, `max`, `opacity`, and `alpha` scalar values.
- Route deeper colormap, chart, static cartography, Plotly, or pydeck styling questions to [visualization-and-charts](../../visualization-and-charts/SKILL.md).

## Optional localtileserver, titiler, and network layers

Symptoms:

- `add_raster()` fails for a local GeoTIFF, NumPy array, or xarray object.
- `add_cog_layer()` or `add_stac_layer()` fails while building tile URLs or bounds.
- A raster layer is added but tiles do not load in a remote notebook.

Likely causes:

- Missing optional local tile dependencies.
- The raster path is wrong or inaccessible from the Python process.
- A remote COG, STAC item, or titiler endpoint is unavailable.
- The hosted notebook needs a proxy prefix for local tile services.
- Network, token, or catalog access is blocked.

Actions:

1. Confirm the user actually needs local/COG/STAC display rather than EE export or data conversion. If they need conversion/export, route to [conversion-and-io](../../conversion-and-io/SKILL.md).
2. For local files, verify file existence and permissions in the user's runtime.
3. For COG/STAC, test the service endpoint and token requirements outside the map call if the environment allows network checks.
4. In hosted Jupyter environments, configure the local tile server proxy expected by that platform.
5. If optional dependencies are absent, either install the requested extra in the active environment or fall back to folium/HTML with already available tile URLs.

## HTML and Streamlit output failures

Symptoms:

- `to_html()` rejects the filename.
- ipyleaflet output dimensions are wrong.
- Streamlit embedding shows a blank frame or misses layer controls.

Actions:

- Use filenames ending in `.html`.
- For ipyleaflet `to_html()`, pass width as a string ending in `px` or `%`, and height as a string ending in `px`.
- Add a layer control before export when the user needs toggles in the output.
- For folium Streamlit bidirectional behavior, install the optional Streamlit-folium bridge; otherwise use static embedding.
- Route broader app layout, deployment, ports, secrets, and packaging to [timelapse-and-apps](../../timelapse-and-apps/SKILL.md).

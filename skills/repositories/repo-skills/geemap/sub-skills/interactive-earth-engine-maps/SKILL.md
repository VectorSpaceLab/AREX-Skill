---
name: interactive-earth-engine-maps
description: "Route geemap interactive Earth Engine maps, backend choice,
  layers, basemaps, widgets, and HTML or Streamlit map output."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Interactive Earth Engine Maps

Use this operating sub-skill when the user asks for geemap map construction or debugging: creating a map, choosing the ipyleaflet or folium backend, adding Earth Engine layers, adding basemaps or tile services, adding map widgets, comparing layers, and saving or embedding an interactive map.

## Route here for

- `geemap.Map`, `geemap.geemap.Map`, and `geemap.core.Map` when the desired map is the default ipyleaflet-backed geemap map.
- `geemap.foliumap.Map` or `USE_FOLIUM=1` when the desired map is the folium-backed HTML-oriented map.
- Earth Engine layer methods: `add_layer`, `addLayer`, and `add_ee_layer`.
- Map positioning methods: `set_center`, `setCenter`, `center_object`, and `centerObject`.
- Basemap and external layer methods: `add_basemap`, `add_tile_layer`, `add_wms_layer`, `split_map`, `add_raster`, `add_cog_layer`, and `add_stac_layer`.
- Presentation and widget controls: `add_legend`, `add_colorbar`, `add_draw_control`, `add_layer_manager`, and `add_inspector`.
- Map output methods: `to_html` and `to_streamlit`.
- Module surfaces that support interactive maps: `geemap.ee_tile_layers`, `geemap.basemaps`, `geemap.map_widgets`, and `geemap.toolbar`.

## Route elsewhere

- Data conversion, local/remote data movement, Earth Engine exports, `shp_to_ee`, `ee_export_*`, `ee_to_numpy`, COG/STAC URL helpers, and format troubleshooting: [conversion-and-io](../conversion-and-io/SKILL.md).
- Charts, static cartography, cartoee, legends/colormaps beyond map attachment, Plotly, pydeck, kepler, and maplibre style depth: [visualization-and-charts](../visualization-and-charts/SKILL.md).
- Timelapse generation, GIF/MP4 processing, app packaging, and deployment workflows: [timelapse-and-apps](../timelapse-and-apps/SKILL.md).
- Earth Engine classifier conversion and ML/AI helper workflows: [machine-learning-and-ai](../machine-learning-and-ai/SKILL.md).

## First actions for future agents

1. For map recipes, backend choice, and Earth Engine layer patterns, read [references/workflows.md](references/workflows.md).
2. For signatures, aliases, backend differences, and method ownership, read [references/api-reference.md](references/api-reference.md).
3. For failures, credentials, optional services, widget display, basemaps, palettes, legends, or colorbars, read [references/troubleshooting.md](references/troubleshooting.md).
4. If the active Python environment is uncertain, run [scripts/map_smoke.py](scripts/map_smoke.py) with `--backend ipyleaflet --skip-ee-init` or `--backend folium --skip-ee-init`.
5. For package-wide installation and Earth Engine account setup, use the root skill's installation/auth guidance if integration provides it.

## Backend policy

- Prefer **ipyleaflet** for notebooks, drawing, layer manager, inspector, split-map UI, bidirectional widget interaction, and the richest geemap toolset.
- Prefer **folium** for simple map rendering, saved HTML, static Leaflet output, or lightweight Streamlit embedding.
- Use explicit imports when backend behavior matters:
  - `import geemap.geemap as geemap` for ipyleaflet.
  - `import geemap.foliumap as geemap` for folium.
- Treat top-level `import geemap` as environment-dependent: if `USE_FOLIUM` is set, it loads folium behavior; otherwise it attempts the ipyleaflet implementation.
- Use `ee_initialize=False` for offline or pre-auth smoke checks. Remove that flag only after the user has an Earth Engine account, project, credentials, and network access.

## Safety boundaries

- This sub-skill can create offline map objects and inspect method availability without Earth Engine authentication.
- Adding real Earth Engine imagery, sampling data, centering on remote EE objects, or using Inspector values requires Earth Engine initialization and network access.
- `add_raster` usually requires optional local tile serving support; `add_cog_layer` and `add_stac_layer` usually require reachable titiler or catalog services.
- Keep generated answers self-contained: do not ask future agents to open the original repository checkout. Use only this subtree and sibling generated skill references.

## Workflow checklist

- For a **map-only offline check**, import the chosen backend, create `Map(..., ee_initialize=False)`, add a basemap or tile URL, and run the smoke script if imports are uncertain.
- For an **authenticated EE layer**, initialize Earth Engine first, then call `add_layer`, `addLayer`, or `add_ee_layer` with a supported EE object and a validated `vis_params` dictionary.
- For **external web layers**, use `add_tile_layer` for XYZ URLs and `add_wms_layer` for WMS services; match argument names to the active backend.
- For **COG/STAC/local raster layers**, confirm optional raster dependencies, local file paths, remote URLs, and titiler or local tile serving requirements before blaming EE auth.
- For **interactive controls**, stay on ipyleaflet and use `add_draw_control`, `add_layer_manager`, `add_inspector`, `add_toolbar`, or `add_gui` as appropriate.
- For **portable output**, call `to_html`; use `to_streamlit` only when Streamlit is installed and route larger app deployment to the app sub-skill.

## Troubleshooting start points

- Auth, project, proxy, or EE service failures: use `references/troubleshooting.md`, section "Earth Engine auth, project, and network".
- Import, kernel, Colab, Jupyter, or widget display failures: use the troubleshooting sections on kernel restart and widget display.
- Backend mismatch or `USE_FOLIUM` surprises: use the backend policy above plus `scripts/map_smoke.py` and the troubleshooting backend section.
- Basemap registry versus module-helper confusion: use the troubleshooting section "Basemap catalog and shadowing".
- Palette, legend, and colorbar validation errors: use the troubleshooting section "Invalid palette, legend, or colorbar values".
- Raster, COG, STAC, WMS, or XYZ layer failures: use the troubleshooting section "Optional localtileserver, titiler, and network layers".

## Bundled-source policy

- `scripts/map_smoke.py` is the only bundled executable helper for this sub-skill.
- The credentialed Earth Engine map example from the repository is intentionally reference-only and distilled into `references/workflows.md`; do not ask future agents to run or open it.
- `references/api-reference.md` owns the verified method and module surface; keep new API detail there rather than expanding this router.
- `references/troubleshooting.md` owns the operational failure matrix; keep new failure notes there rather than scattering them through workflows.
- Verification cases and reports belong outside this runtime subtree; this sub-skill only contains operating instructions and helpers.

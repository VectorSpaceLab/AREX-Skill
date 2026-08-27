---
name: interactive-maps
description: "It routes a researcher through safe Leafmap and Folium Streamlit
  workflows for tiled, raster, vector, and comparison maps."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Interactive maps

Use this leaf when a task needs a Leafmap-backed Streamlit map: basemaps and
XYZ/QMS search, split views, heatmaps, marker clusters, WMS, COG/raster
visualization, vector uploads, or NLS/Ordnance Survey tile overlays. Keep Earth
Engine and housing-specific joins on their sibling routes.

## Route the request

1. Select the rendering backend before reading data:
   - `leafmap.foliumap` for Folium controls, WMS/COG layers, XYZ tiles, and
     `Map.to_streamlit`.
   - `leafmap.kepler` for Kepler layer/config output and its
     `Map.to_streamlit`.
   - `leafmap.deck` for PyDeck-compatible maps rendered with
     `st.pydeck_chart`.
2. Classify the input as a local vector, point table, trusted WMS/COG service,
   XYZ/QMS provider, or prepared tile layer. Do not fetch a user-supplied URL
   to decide whether it is trusted. Use an exact allowlist for services that
   the application is willing to contact.
3. For a local GeoJSON, KML, or ZIP upload, run
   [the bundled validator](scripts/validate_vector_input.py) first. A zero exit
   status and its JSON report are the pre-render gate; a nonzero status is a
   user-correctable input error.
4. Follow the inspected signatures and concrete recipes in the references.
   Initialize empty selections before conditional UI branches, catch service
   and backend errors at the boundary, and show a readable Streamlit error
   rather than a traceback.
5. Render only after the relevant URL, bands/visualization parameters, vector
   geometry/CRS, and backend checks pass. Keep remote tile selection bounded and
   preserve provider attribution.

## Operating links

- [Inspected API reference](references/api-reference.md) — exact signatures,
  module locations, and backend render calls.
- [Workflows](references/workflows.md) — concrete map construction recipes,
  validation gates, split views, and NLS overlays.
- [Data formats](references/data-formats.md) — local vector, point, WMS, COG,
  and XYZ input contracts.
- [Troubleshooting](references/troubleshooting.md) — URL, CRS/driver, service,
  backend, visualization, and tile failure recovery.
- [Offline vector validator](scripts/validate_vector_input.py) — deterministic
  geometry count, CRS, bounds, and column report without network access.

## Completion signals

A successful invocation has a selected backend, a validated input contract, and
one of these observable render signals:

- Folium: a `leafmap.foliumap.Map` reaches `to_streamlit(...)`.
- Kepler: a `leafmap.kepler.Map` reaches `to_streamlit(...)`.
- PyDeck: a `leafmap.deck.Map` reaches `st.pydeck_chart(...)`.

Rejected URLs, malformed vectors, missing optional backends, invalid COG
visualization JSON, and failed WMS capabilities must become user-visible
errors. Record remote-service limits and any unverified split-layer ordering;
do not silently change backend or layer semantics.

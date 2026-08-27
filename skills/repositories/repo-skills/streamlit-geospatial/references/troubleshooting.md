# Cross-cutting troubleshooting

## Import or startup errors

- **`ModuleNotFoundError` for Streamlit, Leafmap, GeoPandas, or a backend**:
  install the documented requirements in the active private environment, then
  run `scripts/check_environment.py`. Do not repair a user-owned environment
  blindly.
- **`geemap.foliumap` fails while building basemaps**: set `USE_FOLIUM=1` in
  the process environment before importing `geemap.foliumap`; do not set it
  after the module has been imported.
- **Kepler.gl reports missing `pkg_resources`**: use a compatible setuptools
  release such as `<81` in the selected environment, then rerun `pip check`.
  Keep this pin scoped to the app environment.
- **GDAL/Fiona/Pyogrio import or driver errors**: check the Python wheel and
  host GDAL/PROJ/GEOS libraries, inspect supported drivers, and retry with a
  small GeoJSON fixture. Do not assume `osgeo` is installed merely because the
  requirements file mentions GDAL.

## Streamlit and deployment errors

- **Blank page or repeated reruns**: confirm `Home.py` is the command target,
  page code calls `st.set_page_config` once near the top, and expensive
  network calls are behind a submit/button boundary and cache where safe.
- **Port/config problems**: use the deployment platform's port and headless
  settings. The original setup recipe writes a home-directory config, so avoid
  running it unchanged on a shared host.
- **Page not listed**: verify the file is directly under `pages/`, has a
  `.py` suffix, and uses a deployment-safe filename.

## External data and credentials

- **WMS/XYZ/COG or housing source fails**: validate URL policy and local input
  schema first, then check network, service status, attribution, rate limits,
  and response schema. A 200 response is not proof of geospatial content.
- **Earth Engine authentication or asset failure**: use the remote-data
  preflight, confirm the token variable name without printing its value, and
  check project/asset type/access. Never substitute a fabricated asset or
  claim a remote result from local imports.
- **No imagery/data or request too large**: reduce ROI, date span, collection,
  bands, dimensions, or frame rate; use a known small sample and verify output
  existence before displaying it.

## Input and rendering failures

- **Invalid JSON visualization parameters**: require a JSON object; verify
  bands are a non-empty string list, numeric min/max are finite and ordered,
  opacity is in `[0, 1]`, and palette values are non-empty strings.
- **Vector upload cannot render**: run the bundled vector validator, inspect
  geometry count/CRS/bounds, enable KML support only when needed, reproject to
  WGS84 for Earth Engine, and reject empty or non-finite geometry.
- **Dashboard joins are empty**: preserve FIPS/CBSA/postal identifiers as
  strings, zero-fill five-character numeric keys, uppercase state keys, and
  report unmatched geometry/data rows rather than imputing zero.

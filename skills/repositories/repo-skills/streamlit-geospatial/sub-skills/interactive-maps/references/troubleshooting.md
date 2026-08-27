# Troubleshooting and recovery

Treat every item below as a bounded, user-correctable failure. Show the
selected backend and input category in the UI, keep the original exception
available for review, and do not silently switch semantics.

## URL and remote-service failures

| Symptom | Likely cause | Recovery and expected signal |
|---|---|---|
| `WMS URL is not trusted` | The submitted URL is not an exact approved entry. | Reject before `get_wms_layers`; show the allowlist policy. Do not make a probe request or accept a merely similar host/path. |
| WMS capabilities timeout, parse error, or empty list | Service is down, blocked, malformed, or does not expose usable capabilities. | Catch the capability exception, set available layers to `[]`, and show `WMS capabilities could not be read` or `no selectable layers`. Do not render with an uninitialized options variable. |
| WMS layer is rejected after selection | UI state contains a name not returned by the latest capability response. | Re-check membership in the capability result before `add_wms_layer`; clear stale selections and retry discovery. |
| COG URL rejected | URL is outside the approved prefix, is not HTTPS, or does not end in `.tif`. | Stop before `cog_bands`; show `COG URL is not trusted`. Do not broaden the prefix based on a redirect or file name. |
| XYZ/QMS search is slow or empty | Discovery is remote and provider catalogs can change. | Run only after an explicit submit, cap results, report an empty state, and allow a retry. Do not treat an empty catalog as a valid tile layer. |
| Tiles load partially or overwhelm the browser | Too many layers, an excessive viewport/zoom, rate limiting, or a provider usage limit. | Limit selected layers and zoom, retain attribution, avoid auto-refresh, and show the provider's limit. Do not fetch tiles in the validator. |

The service URL and data URL policies are independent. A trusted WMS URL does
not trust arbitrary legend JSON, and a trusted COG prefix does not authorize
arbitrary visualization keys.

## Visualization and split-map failures

- **Invalid visualization JSON:** parse text with `json.loads(text or "{}")`,
  require a dictionary, and report the `JSONDecodeError` without calling
  `add_cog_layer`.
- **Invalid COG bands:** use `leafmap.cog_bands` output as the only source of
  selectable labels. Require one or three selected labels. If discovery fails,
  do not use a guessed band list.
- **Raster endpoint rejection:** a dictionary can still contain an unsupported
  key or value. Remove endpoint-specific keys, retry with `{}`, and retain the
  original error as a diagnostic rather than claiming the COG is invalid.
- **COG/WMS split ordering:** validate both inputs independently. The inspected
  `split_map` call supports the application's ordinary provider/tile-object
  pattern, but WMS and COG split ordering is not a contract to assume. Smoke
  test the rendered order; if unsupported, use a clearly labelled ordinary
  layered map or stop for an explicit fallback decision.

## Local vector, geometry, and CRS failures

| Symptom | Recovery |
|---|---|
| Validator exits 2 with malformed GeoJSON | Keep the file local, fix the JSON/geometry, and rerun `python scripts/validate_vector_input.py --input ./file.geojson`. Do not bypass the helper by passing the upload directly to GeoPandas. |
| Validator reports an unsafe ZIP member | Rebuild the archive with a regular root or nested file using a safe relative member name. The helper never extracts or follows archive paths. |
| Empty geometry or non-finite coordinate error | Reject the upload, identify the feature in the user's local copy, and repair/remove it. No map object should be created. |
| CRS is missing or unclear | Ask for the source CRS. Do not assign EPSG:4326 merely because coordinates look geographic; only reproject after the CRS is known. |
| KML driver error | Check whether the installed Fiona exposes `fiona.drvsupport.supported_drivers`; enable `"KML": "rw"` only there, then call `gpd.read_file(..., driver="KML")`. If the driver is absent, report a dependency/driver error rather than treating KML as GeoJSON. |
| Web map is in the wrong place | Inspect `gdf.crs`, transform to EPSG:4326, and recompute the center. Never use a centroid computed in a projected CRS as latitude/longitude. |
| Geometry is valid but the backend rejects it | Reduce the layer to a small local fixture, preserve the validated CRS, and test the selected backend's `add_gdf` signature. Keep the backend choice visible; do not silently fall back. |

The validator is intentionally independent of GeoPandas/Fiona and cannot prove
renderer compatibility. That second-stage check is required for uploads.

## Backend and dependency failures

- **Folium import failure:** report the missing Leafmap/Folium dependency and
  stop the Folium route. Do not substitute Kepler or PyDeck without a new user
  choice.
- **Kepler `pkg_resources` failure:** some Kepler dependency combinations
  import code that expects `pkg_resources`. Confirm the selected environment's
  `setuptools`/`pkg_resources` availability and the installed `keplergl` and
  Streamlit adapter versions. Repair the environment with its approved package
  policy, then re-run a minimal `import leafmap.kepler` smoke test. Do not
  patch runtime source files or silently change to another backend.
- **PyDeck render failure:** the inspected `leafmap.deck.Map` has no
  `to_streamlit`; use `st.pydeck_chart(m)`. If the optional chart package is
  absent, report it as a dependency error.
- **Wrong helper module:** `get_wms_layers` is on the package-level `leafmap`
  module in the inspected environment, not the `leafmap.foliumap` alias. Keep
  those imports separate. `gdf_centroid` is also package-level.

## Difficult synthetic cases to review

1. Supply a local vector with one malformed geometry and select Kepler first.
   Expected: validator rejects the input before any backend import or map
   construction; the UI names both the malformed vector and the selected
   backend, with no silent Folium fallback.
2. Supply a trusted COG URL, an invalid visualization object, and a trusted WMS
   layer for a split comparison. Expected: COG JSON/band validation fails
   before either layer is added; the WMS capability result is not used to mask
   the raster error. With corrected parameters, the reviewer must still verify
   the split ordering or observe the documented ordinary-layer fallback.

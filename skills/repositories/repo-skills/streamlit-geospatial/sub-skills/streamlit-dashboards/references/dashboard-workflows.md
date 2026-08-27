# Dashboard workflows

This reference distills the checked-in dashboard behavior into procedures a
Researcher can apply without depending on the source checkout. Names below are
logical data groups and filenames, not links to a particular hosting account.

## 1. Compose the multipage app

`Home.py` is the landing page, not a data-processing module. It sets a wide
page layout, presents sidebar About/Contact/Support sections, introduces the
mapping libraries, shows a navigation hint, and lays out four remote timelapse
images in two columns. A page placed in the app's `pages/` directory is
presented by Streamlit's multipage navigation; the source convention uses an
integer, an emoji, and a descriptive title in the filename. Preserve that
convention when adding a page, but keep page-specific imports and expensive
work inside the page.

A safe composition sequence is:

1. Configure the page once at the top of the entry point or page.
2. Keep sidebar copy and app-wide navigation separate from data loading.
3. Give each page one clear input-to-view flow and cache only pure, repeatable
   reads.
4. Resolve bundled resources from the application root in new code instead of
   relying on the process current directory. The historical page currently
   reads its TSV by a relative path and the housing page currently resolves its
   data dictionary from the current directory; those are deployment risks to
   make explicit during a repair.
5. Keep network-backed images, data, and map tiles optional and give the user a
   useful local-schema error when they are unavailable.

The low-level map construction API is intentionally routed to
`interactive-maps`; this sub-skill covers the dashboard orchestration and data
contract around it.

## 2. U.S. housing dashboard lifecycle

The housing page declares logical data-link groups:

| Frequency/type | Geography files represented by the group | Period/key family |
|---|---|---|
| `weekly` | `national`, `metro` | `week_end_date`; national `geo_country`, metro `cbsa_code` |
| `monthly_current` | `national`, `state`, `metro`, `county`, `zip` | `month_date_yyyymm` |
| `monthly_historical` | `national`, `state`, `metro`, `county`, `zip` | `month_date_yyyymm` |
| `hotness` | `metro`, `county`, `zip` | history-oriented metrics; not consumed by the current `app()` path |

The current controls expose monthly national/state/metro/county and weekly
national/metro. The link map contains ZIP and hotness entries, but a caller
should not claim those views are implemented merely because an entry exists.
Current versus historical monthly selection is unavailable for weekly data; the
page removes the current-month choice when weekly is selected.

For every selected branch:

1. Select frequency, monthly current/history (when applicable), and scale.
2. Load the matching boundary collection and tabular source.
3. Normalize the source identifiers before joining; see
   [data-contracts.md](data-contracts.md).
4. Derive and validate the available period set. Never fabricate a missing
   month or week.
5. Derive the metric list from the data columns, excluding the period and
   geography metadata columns. Check the selected metric against the optional
   data dictionary.
6. Join attributes to geometry, split mapped and no-data rows, and report
   unmatched records before rendering.
7. Construct the PyDeck layers, tooltip, view state, and optional raw-data
   table only after the selected metric is numeric enough to rank and color.

### Period behavior

The source helpers have intentionally specific behavior:

- Monthly periods come from `month_date_yyyymm`. The current-month branch uses
  the first value returned from a set-derived list, so its choice is not a
  stable ordering guarantee. Historical controls calculate the minimum and
  maximum year, build `YYYYMM` from year/month sliders, and fall back to the
  first available period when the requested value is absent. A repaired or new
  workflow should sort unique periods and choose a deterministic available
  default while retaining the explicit missing-period warning.
- Weekly values are strings such as `M/D/YYYY` or `MM/DD/YYYY` in
  `week_end_date`. Nulls are removed, values are parsed as month/day/year, and
  the resulting dates are sorted. A selected date is advanced to the Saturday
  of its week; if that Saturday is absent, the page reports the allowed range
  and falls back to the latest available week. Validate the exact source format
  before converting it.
- A period with no rows is different from a period with rows whose metric is
  null. The first is an availability error; the second is a no-data geography
  that should be visible and explained.

## 3. Join and map the selected attribute

The page reads the four bundled boundary families as GeoJSON and uses the
following logical joins:

| Scale | Geometry key | Data key after source normalization |
|---|---|---|
| National | `NAME` | monthly `country`; weekly special-case `United States` |
| State | `STUSPS` | uppercase `state_id` copied to `STUSPS` |
| County | `GEOID` | `county_fips`, string zero-filled to five characters |
| Metro | `CBSAFP` | `cbsa_code` as a string; weekly code is truncated to five characters |
| ZIP (prepared, not exposed by current controls) | `GEOID10` | `postal_code`, string zero-filled to five characters |

The source uses `how="outer"` for all five merges. That preserves both
geometry-only rows and data-only rows, but it can create records with null
geometry. A production repair should classify the result into:

- matched geometry plus non-null metric: renderable data layer;
- matched geometry plus null metric: optional gray no-data layer;
- data-only or invalid-geometry row: exclude from GeoJSON rendering and report
  as an unmatched data record;
- geometry-only row: no observation for this source/period, usually a no-data
  geography.

Do not pass a null-geometry row blindly to a `GeoJsonLayer`. For the difficult
case of a historical county period that has a valid county boundary but no
record in the selected period, retain the boundary in the gray no-data set and
state that the metric is unavailable; do not fill it with zero. If the data
record has no matching county FIPS at all, report an unmatched key separately.

The source then sorts non-null mapped rows by the selected metric, assigns a
palette-derived `R`, `G`, `B` triplet by rank, and uses a fixed gray color for
no-data rows. Preserve numeric types for metrics: percentage strings with a
trailing `%` are converted to fractions for the two weekly aggregate sources,
except `median_days_on_market_by_day_yy`, which remains a day-like value.
Confirm the source header before applying this rule because a remote schema
change can make a string operation unsafe.

## 4. PyDeck view contract

The inspected runtime exposes these constructors:

- `pydeck.Layer(type, data=None, id=None, use_binary_transport=None, **kwargs)`
- `pydeck.ViewState(longitude=None, latitude=None, zoom=None, min_zoom=None,
  max_zoom=None, pitch=None, bearing=None, **kwargs)`
- `pydeck.Deck(layers=None, views=..., map_style='__MAP_STYLE__',
  api_keys=None, initial_view_state=..., width='100%', height=500,
  tooltip=True, description=None, effects=None, map_provider='carto',
  parameters=None, widgets=None, show_error=False, map_projection=None)`

The housing page uses a `GeoJsonLayer` with the GeoDataFrame as data,
`pickable=True`, filled/stroked polygons, optional extrusion, an RGB expression
`[R, G, B]`, black outlines, and a minimum line width. It makes a second gray
`GeoJsonLayer` for no-data rows when requested. Its `Deck` uses a centered U.S.
view (`latitude=40`, `longitude=-100`, `zoom=3`, `max_zoom=16`, `pitch=0`,
`bearing=0`) and a tooltip whose HTML substitutes `NAME`, the selected metric,
and the selected period. Treat metric names as data, not HTML: escape or
restrict tooltip fields if accepting arbitrary user input.

A stable rendering order is:

1. validate geometry and the selected metric;
2. build the mapped layer;
3. optionally build the gray no-data layer;
4. create the tooltip with a human label and period;
5. pass layers and view state to `pdk.Deck`, then call Streamlit's PyDeck chart;
6. show the color scale and raw-data table only for columns that exist.

Empty mapped layers must not be presented as a successful map. Show counts for
matched, no-data, unmatched, and invalid-geometry rows instead.

## 5. Historical NLS/Ordnance Survey comparison

The historical page reads a small tab-separated catalog with `Name` and `URL`
columns. It combines catalog names/URLs with Leafmap basemap names/objects,
lets the user choose left and right layers, parses latitude/longitude/zoom from
text inputs, optionally adds every catalog name containing `OS 25 inch`, and
renders a split map. The default historical layer is the Great Britain
Bartholomew Half Inch map and the default right layer is `HYBRID` when those
names are present.

The inspected Leafmap/Folium signatures are:

- `leafmap.foliumap.Map(**kwargs)`
- `Map.split_map(self, left_layer='TERRAIN', right_layer='OpenTopoMap',
  left_args={}, right_args={}, left_array_args={}, right_array_args={},
  left_label=None, right_label=None, left_position='bottomleft',
  right_position='bottomright', **kwargs)`
- `Map.add_tile_layer(self, url, name, attribution, overlay=True,
  control=True, shown=True, opacity=1.0, API_key=None, **kwargs)`
- `Map.to_streamlit(self, width=None, height=600, scrolling=False,
  add_layer_control=True, bidirectional=False, **kwargs)`
- `folium.plugins.MeasureControl(position='topright',
  primary_length_unit='meters', secondary_length_unit='miles',
  primary_area_unit='sqmeters', secondary_area_unit='acres', **kwargs)`
- `folium.TileLayer(tiles='OpenStreetMap', min_zoom=None, max_zoom=None,
  max_native_zoom=None, attr=None, detect_retina=False, name=None,
  overlay=False, control=True, show=True, no_wrap=False, subdomains='abc',
  tms=False, opacity=1, **kwargs)`

The page's tile URLs use `{z}/{x}/{y}` placeholders and an attribution for the
National Library of Scotland. Preserve attribution and check the provider's
reuse terms. Validate numeric text inputs before constructing a map; reject
empty, non-numeric, out-of-range coordinates and unreasonable zoom values.
Route low-level `Map` API troubleshooting to `interactive-maps` rather than
expanding this dashboard skill.

## 6. Safe deployment

The repository declares Python dependencies in `requirements.txt`, including
Streamlit, GeoPandas, PyDeck's surrounding geospatial stack, and GDAL from a
wheel index. `packages.txt` declares OS packages including GDAL/PROJ/GEOS
libraries, compilers, and media tools. The Procfile currently runs
`sh setup.sh` before `streamlit run Home.py`.

`setup.sh` does not install the commented apt packages. It creates a
user-level Streamlit configuration directory and writes a config using
`$PORT`. That is a host mutation and can leave a literal or empty port when
`PORT` is unset. For a clean Streamlit Cloud or Procfile deployment:

- let the platform install `packages.txt` and `requirements.txt` through its
  supported build mechanism;
- do not run the host-mutating setup script on a shared workstation or in a
  persistent build image;
- prefer platform configuration or explicit Streamlit command-line flags for
  headless mode, CORS, and the runtime port, with a platform-provided port;
- keep the application code and bundled catalog fixtures read-only at runtime;
- if a ZIP boundary must be inspected, extract into an owned temporary
  directory after validating member names and size, not into an installed
  package's static directory;
- smoke-test import, page discovery, local fixture parsing, and one small
  in-memory join without fetching all remote data or tiles.

The source creates `Path(st.__path__[0]) / "static" / "downloads"` and writes a
ZIP and extracted shapefile there for the ZIP branch. Treat that as an
implementation detail to audit, not a general output directory: installed
package directories may be read-only and the extraction is not safe for an
untrusted archive without traversal/size checks. A repair should use an
explicit writable temporary or application-owned output location and clean it
up.

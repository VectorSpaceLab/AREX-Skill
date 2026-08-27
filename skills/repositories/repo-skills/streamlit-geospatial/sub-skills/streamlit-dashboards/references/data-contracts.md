# Dashboard data contracts

Use this document before a remote fetch or map join. It is an operating
contract inferred from the checked-in housing page, boundary fixtures, and data
dictionary. The validator bundled with this skill checks local stand-ins for the
same assumptions.

## Tabular source contract

Read CSVs as tabular data with string-preserved identifiers. The source helper
uses `pandas.read_csv(url)` and then derives normalized key columns. Required
columns by branch are:

| Frequency | Scale | Required source columns | Derived/used data key |
|---|---|---|---|
| monthly | national | `month_date_yyyymm`, `country` | `country` |
| monthly | state | `month_date_yyyymm`, `state`, `state_id` | uppercase `state_id` as `STUSPS` |
| monthly | metro | `month_date_yyyymm`, `cbsa_code`, `cbsa_title`, `HouseholdRank` | string `cbsa_code` |
| monthly | county | `month_date_yyyymm`, `county_fips`, `county_name` | string `county_fips`, zero-filled to five characters |
| monthly | zip | `month_date_yyyymm`, `postal_code`, `zip_name`, `flag` | string `postal_code`, zero-filled to five characters |
| weekly | national | `week_end_date`, `geo_country` | source special-cases first row as `country = United States` |
| weekly | metro | `week_end_date`, `cbsa_code`, `cbsa_title`, `hh_rank` | string `cbsa_code`, first five characters |

The page's current controls do not expose monthly ZIP, weekly ZIP, or hotness
views even though the logical link map names those groups. Treat them as
unsupported until their own metric and rendering contract is proven.

The source's exact normalization behavior is important:

- County FIPS: `map(str)` followed by `str.zfill(5)`.
- State: `STUSPS = state_id.str.upper()`; the source expects a string-like
  `state_id`.
- Metro: `map(str)`; weekly metro then applies `str[:5]`.
- Postal code: `map(str)` followed by `str.zfill(5)`.
- Weekly national: when `geo_country` is present, the source creates a
  `country` column filled with null and writes `United States` only at row zero.

For robust new code, strip whitespace before normalization, reject non-digit
values for FIPS/CBSA/postal identifiers, preserve nulls as nulls, and record
how many keys changed or became unmatched. Do not turn a missing key into a
zero or a string such as `nan`.

## Period and metric contract

Monthly period values are `month_date_yyyymm` and should be validated as a
six-digit `YYYYMM` value (a separator form such as `YYYY-MM` can be normalized
only at a validation boundary). Weekly values are `week_end_date` strings in
month/day/year form. Remove null period values before offering choices, sort
the unique values, and show the available range.

A requested monthly value must exist exactly after normalization. A requested
weekly date must match a source week; the UI may map an arbitrary selected date
to the Saturday ending its week, but it must warn and choose a known fallback
when that Saturday is absent. Do not use a missing month or week as an implicit
zero.

Metric columns are the columns left after excluding the period and geography
metadata for the selected branch. The local data dictionary has exactly these
columns:

- `Name`: machine column name;
- `Label`: user-facing metric label;
- `Description`: metric explanation.

A selected metric should exist in the CSV, contain at least one non-null value
for the selected period, and have a dictionary row when a dictionary is
provided. The checked-in dictionary describes, among others:

- median listing price and its month/year changes;
- active, new, pending, price-increased, price-reduced, and total listing
  counts and changes;
- days on market and its changes;
- median list price per square foot, median listing square feet, and average
  listing price;
- pending ratio and its changes.

The dictionary says that count measures are snapshots or typical-week measures
where stated; it does not authorize deriving a monthly total from a weekly
count without an explicit product decision. Show the dictionary label and
description next to an attribute when available, and warn rather than crash
when a new remote metric lacks a description.

The weekly aggregate branch converts percent-suffixed strings to a fraction
for all selected data columns except `median_days_on_market_by_day_yy`. This
is a source-specific rule: inspect headers and sample values before applying it
when a remote schema changes.

## Boundary GeoJSON contract

A boundary input must be a `FeatureCollection` with a non-empty `features` list.
The checked-in fixture families use the NAD83 geographic CRS identified as
EPSG:4269. The required property keys are:

| Scale | Required property key |
|---|---|
| national | `NAME` |
| state | `STUSPS` |
| county | `GEOID` |
| metro | `CBSAFP` |
| zip | `GEOID10` |

The observed small fixtures have one national feature, 52 state features,
3,220 county features, and 945 metro features. Counts can legitimately change
when a boundary vintage changes, so use them as diagnostics rather than hard
requirements. Check that the key has usable values and count null geometries.
A null geometry is a reportable condition, not a geometry to send to PyDeck.

## Join contract

Use these normalized pairs:

```text
national: NAME  <-> country
state:    STUSPS <-> uppercase(state_id)
county:   GEOID <-> zero-filled county_fips
metro:    CBSAFP <-> five-character cbsa_code
zip:      GEOID10 <-> zero-filled postal_code
```

The source uses an outer merge. For a safer dashboard, calculate and expose:

- unique normalized keys in each side;
- overlap count;
- data rows with no geometry match;
- geometry rows with no data for the selected period;
- matched rows whose metric is null;
- rows with null or invalid geometry.

Render only valid geometries. Use a separate no-data layer for valid boundary
features without an observation. Never impute a missing historical county value
as zero. If a data-only row has null geometry, preserve it in diagnostics or a
raw table, not the map layer.

## PyDeck input contract

The installed inspection environment reports pandas 3.0.5, GeoPandas 1.1.4,
and PyDeck 0.9.3. The relevant signatures are:

```text
pandas.read_csv(filepath_or_buffer, *, sep=..., delimiter=..., header=...,
                names=..., index_col=..., usecols=..., dtype=..., ...)
geopandas.read_file(filename, bbox=None, mask=None, columns=None, rows=None,
                    engine=None, **kwargs)
pydeck.Layer(type, data=None, id=None, use_binary_transport=None, **kwargs)
pydeck.ViewState(longitude=None, latitude=None, zoom=None, min_zoom=None,
                 max_zoom=None, pitch=None, bearing=None, **kwargs)
pydeck.Deck(layers=None, views=..., map_style='__MAP_STYLE__', api_keys=None,
            initial_view_state=..., width='100%', height=500, tooltip=True,
            description=None, effects=None, map_provider='carto', parameters=None,
            widgets=None, show_error=False, map_projection=None)
```

Use a `GeoJsonLayer` with a validated GeoDataFrame or GeoJSON-like input,
`pickable=True`, a numeric fill expression or RGB values, and an HTML tooltip
whose fields are fixed or escaped. Keep no-data rows in a separate gray layer.
Do not let an arbitrary metric name become an unescaped HTML fragment.

## Validator usage

The bundled helper is intentionally dependency-light and local-only:

```text
python scripts/validate_dashboard_inputs.py \
  --csv /absolute/path/metrics.csv \
  --category county --frequency monthly \
  --period 202401 --metric median_listing_price \
  --geojson /absolute/path/boundaries.geojson \
  --dictionary /absolute/path/realtor_data_dict.csv \
  --output /absolute/path/validation.json
```

It checks file readability, headers, required branch keys, selected period and
metric availability, dictionary columns/rows, GeoJSON structure/property keys,
normalized key overlap, and null geometry counts. It exits nonzero with a
readable error summary when a strict check fails. It never downloads remote
files, extracts archives, modifies a Streamlit config, or writes unless
`--output` is explicitly supplied.

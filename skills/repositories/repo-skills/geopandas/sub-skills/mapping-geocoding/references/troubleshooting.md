# Mapping and Geocoding Troubleshooting

## `ImportError` for matplotlib, folium, or mapclassify

Symptoms: `.plot()` or `.explore()` fails when called, even though GeoPandas imports.

Fix:

1. Run `python scripts/check_mapping_optional_deps.py --json`.
2. Install only the needed optional package: matplotlib for static plots, folium/branca for interactive maps, mapclassify for classification schemes.
3. If installation is not allowed, return a vector data file or tabular summary instead of a rendered map.

## Map Is Blank or Mislocated

Likely causes:

- Wrong or missing CRS.
- Coordinates are lat/lon swapped.
- Layer bounds are far outside the expected area.
- Interactive tiles expect web-map-friendly coordinates and data is not transformed as expected.

Fix:

1. Inspect `gdf.crs`, `gdf.total_bounds`, and a few geometry coordinates.
2. Use `core-data-model` guidance to assign or transform CRS correctly.
3. Plot a tiny subset or bounding boxes before styling.
4. Confirm x=longitude and y=latitude for geographic points.

## Interactive Map Is Too Slow

Fix:

1. Simplify geometries on a copy before `explore()`.
2. Filter rows/columns and remove unused attributes.
3. Dissolve or aggregate categories when detailed geometry is unnecessary.
4. Prefer a static plot for large analysis previews.

## Geocoding Provider Fails

Symptoms: `GeocoderNotFound`, timeout, HTTP errors, quota/rate-limit errors, or missing API key.

Fix:

1. Confirm `geopy` is installed.
2. Specify provider explicitly instead of relying on defaults when reproducibility matters.
3. Pass provider-required kwargs such as API key, `user_agent`, domain, timeout, or locale.
4. Respect provider rate limits and terms of service.
5. Cache results when repeated calls are expected.
6. Do not store API keys in generated scripts or reusable references.

## Tests Accidentally Call Network

Fix:

1. Use `scripts/mock_geocode_smoke.py` or monkeypatch geopy geocoder methods.
2. Assert output columns, CRS, and coordinate ordering on mocked results.
3. Keep real provider tests behind explicit network authorization and provider credentials.

## Choropleth Classification Errors

Symptoms: errors mentioning classification scheme, bins, or mapclassify.

Fix:

1. Install `mapclassify` for scheme-based classification.
2. Check that the styled column is numeric unless using categorical plotting.
3. Handle missing values deliberately with `missing_kwds` or by filtering.
4. Use a simpler `column` + `legend=True` plot when classification is not essential.

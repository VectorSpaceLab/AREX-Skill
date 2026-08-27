# Mapping and Geocoding Workflows

## Static Choropleth Plot

```python
ax = gdf.plot(
    column="population",
    cmap="viridis",
    legend=True,
    edgecolor="white",
    linewidth=0.2,
    figsize=(8, 6),
)
ax.set_axis_off()
```

Checklist:

- Install and import matplotlib.
- Ensure the active geometry column is correct.
- Decide whether classification (`scheme=...`) is needed; install mapclassify if so.
- Save through matplotlib when the deliverable is an image.

## Interactive Map with `explore()`

```python
m = gdf.explore(
    column="category",
    tooltip=["name", "category"],
    legend=True,
)
# m.save("map.html")  # when a file deliverable is needed
```

Checklist:

- Check `folium`, `branca`, and any classification/tile dependencies.
- Reduce geometry complexity for large layers.
- Avoid embedding private data in an HTML map unless the user explicitly authorizes it.

## Add Context after Spatial Analysis

Typical sequence:

1. Use `spatial-operations` to clip/filter/dissolve/simplify data.
2. Use `core-data-model` to confirm CRS and active geometry.
3. Use static `.plot()` for quick inspection or `.explore()` for interactive output.
4. Persist final vector data via `io-formats` if the map is not the only deliverable.

## Safe Geocoding with Explicit Provider

```python
from geopandas.tools import geocode

addresses = ["260 Broadway, New York, NY", "77 Massachusetts Ave, Cambridge, MA"]
points = geocode(addresses, provider="photon", timeout=5)
```

Before real provider calls:

- Confirm `geopy` is installed.
- Read provider terms of service, rate limits, and API-key requirements.
- Set timeouts and user-agent/provider kwargs when required.
- Cache or persist results if repeated calls would violate limits.
- Do not run real provider calls in tests; use mocks.

## Reverse Geocode Points

```python
from shapely.geometry import Point
from geopandas.tools import reverse_geocode

points = [Point(-71.0594869, 42.3584697)]  # x=longitude, y=latitude
addresses = reverse_geocode(points, provider="photon", timeout=5)
```

The output geometry remains points; address text is returned in an `address` column.

## No-network Geocode Smoke

```bash
python scripts/mock_geocode_smoke.py --json
```

If `geopy` is missing, install it only when the actual task needs geocoding. The script intentionally does not contact external services.

## Optional Dependency Probe

```bash
python scripts/check_mapping_optional_deps.py --require matplotlib folium --json
```

Use this before choosing a map route. If optional dependencies are missing and installation is not allowed, produce a non-map vector output or a plain data summary instead of pretending a rendered map can be generated.

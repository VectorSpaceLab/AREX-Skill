# Earth Engine API and data workflows

This reference describes the authenticated remote boundary for this sub-skill.
The inspected installation reports geemap `0.37.2`, imported with
`USE_FOLIUM=1`; the repository dependency declares `geemap[extra]` alongside
Earth Engine-facing geospatial packages. The signatures below are local Python
introspection results; they do not prove that Earth Engine is reachable, that a
public asset still exists, or that imagery is available.

## Import and authentication boundary

Set the backend selector before importing the folium adapter:

```python
import os
os.environ["USE_FOLIUM"] = "1"
import geemap.foliumap as geemap
```

`USE_FOLIUM=1` is required here because the application uses geemap's folium
map implementation in a Streamlit page. Setting it before the import avoids an
implicit backend choice and keeps `geemap.Map` aligned with the map object the
page renders. Do not set or print a token value in code or logs.

The installed signature is:

```python
geemap.ee_initialize(
    token_name: str = "EARTHENGINE_TOKEN",
    auth_mode: str | None = None,
    auth_args: dict[str, typing.Any] | None = None,
    user_agent_prefix: str = "geemap",
    project: str | None = None,
    **kwargs: typing.Any,
) -> None
```

`token_name` is the name of the configured token environment variable, not the
token itself. Call `ee_initialize` only after the caller has explicitly
approved the Earth Engine service call and has supplied the configured
secret through its normal secret mechanism. A preflight may check only
whether the named variable is present. The bundled validator never imports
Earth Engine, authenticates, reads a token value, or makes a remote request.

## Map and ROI contracts

The installed folium map constructor is:

```python
geemap.Map(**kwargs)
```

The app evidence constructs it with options such as `basemap="HYBRID"`,
`plugin_Draw=True`, `Draw_export=True`, `locate_control=True`, and
`plugin_LatLngPopup=False`, then renders the map through the folium-backed
Streamlit integration. Keep generic basemap and layer composition in the
interactive-map sibling; this reference covers `Map` only as the Earth Engine
workflow surface.

The installed GeoDataFrame converter is:

```python
geemap.gdf_to_ee(gdf, geodesic=True, date=None, date_format="YYYY-MM-dd")
```

For an uploaded or sample ROI, inspect the GeoDataFrame before conversion:

1. Accept GeoJSON, KML, or a supported zipped upload only through the caller's
   upload layer. The evidence converts a file to a GeoDataFrame, enables KML
   support when needed, and uses `EPSG:4326` for sample polygons.
2. Reproject uploaded data to WGS84 before conversion when its CRS is not
   WGS84. Confirm that the geometry is non-empty, finite, and suitable for the
   selected collection. A missing CRS is not proof that coordinates are WGS84.
3. Convert with `geemap.gdf_to_ee(gdf, geodesic=False)` for the small polygon
   workflow used by the app. Retain the resulting server-side ROI and do not
   serialize it as if it were local imagery.
4. Use a small rectangle or similarly bounded sample first. A global polygon
   can be syntactically valid yet exceed an operation's practical memory or
   pixel limits.

## Catalog search and asset selection

The inspected catalog helpers are:

```python
geemap.search_ee_data(
    keywords,
    regex=False,
    source="ee",
    types=None,
    keys=["id", "provider", "tags", "title"],
)

geemap.ee_data_html(asset)
```

Search is an external catalog operation. Treat the returned records as
untrusted, versioned metadata: select a record by its returned `id`, inspect
its returned `type`, and show details only after confirming the record is the
one the caller intended. The app evidence handles these types as follows:

- `image_collection` → `ee.ImageCollection(id)`
- `image` → `ee.Image(id)`
- `table` or `table_collection` → `ee.FeatureCollection(id)`

The generic timelapse page additionally expects catalog records with `title`,
`id`, and an Earth Engine snippet marker. Catalog response fields can drift;
inspect the record rather than assuming a field is present. Never construct an
asset ID by concatenating untrusted text, and never treat a search result as a
successful data read until a later authenticated operation confirms it.

For a generic image collection, the evidence loads an entered ID with
`ee.ImageCollection.load(asset_id)`, probes the first image's band names, and
then asks the user for one or three bands. That probe is remote and belongs
only after authentication and preflight validation. If loading fails, recover
by checking the asset type and ID, then select another catalog result.

## Verified source-backed datasets

The following patterns are present in the app evidence. They are public asset
identifiers recorded as examples, not live availability guarantees.

### NLCD

The NLCD branch uses:

```python
dataset = ee.ImageCollection("USGS/NLCD_RELEASES/2019_REL/NLCD")
image = dataset.filter(ee.Filter.eq("system:index", year)).first()
landcover = image.select("landcover")
```

The UI offers the years `2001`, `2004`, `2006`, `2008`, `2011`, `2013`, `2016`,
and `2019`, and optionally adds the built-in `NLCD` legend. Keep the year
selection explicit and handle a missing first image before calling map-layer
methods.

### Dynamic World, ESA WorldCover, and ESRI land cover

The inspected Dynamic World helper is:

```python
geemap.dynamic_world(
    region=None,
    start_date="2020-01-01",
    end_date="2021-01-01",
    clip=False,
    reducer=None,
    projection="EPSG:3857",
    scale=10,
    return_type="hillshade",
)
```

The app calls it with a bounded `region`, date strings, and
`return_type="hillshade"`. The comparison also uses:

```python
esa = ee.ImageCollection("ESA/WorldCover/v100").first()
esa_vis = {"bands": ["Map"]}

esri = ee.ImageCollection(
    "projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m"
).mosaic()
```

The ESRI visualization evidence uses `min=1`, `max=10`, and a ten-color
palette. Validate any user-supplied visualization object before passing it to
a layer helper. The `Dynamic_World`, `ESA_WorldCover`, and `ESRI_LandCover`
legend names are UI choices, not guarantees that a legend exists in every
geemap version.

### Microsoft building footprints

The building branch creates a feature collection from one of these patterns:

```python
ee.FeatureCollection("projects/sat-io/open-datasets/MSBuildings/US/{state}")
ee.FeatureCollection("projects/sat-io/open-datasets/MSBuildings/{country}")
```

Use a validated state or country identifier and do not infer that every place
has an asset. Style only after the collection is successfully constructed;
the evidence uses `{"fillColor": "00000000", "color": color}` and centers on
`fc.first()`. An empty collection, unsupported name, access change, or public
asset migration must be reported as a remote-data failure rather than hidden
by the UI.

## External-service and verification rules

Earth Engine object construction, collection filtering, `getInfo`, map tile
creation, and timelapse generation may cross the remote boundary. Keep those
calls out of unit-level config validation. A successful local signature probe
is only an API-shape check. A successful remote workflow requires all of:

- explicit authentication at the caller-selected point;
- a service response confirming the requested asset/collection and ROI;
- a non-empty, bounded result for the requested date range; and
- a local output existence/format check for media operations.

If any of these cannot be observed safely, stop with an unverified result and
state the missing evidence.

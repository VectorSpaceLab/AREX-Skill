# BlenderGIS Georeferencing and CRS API Reference

This reference distills the BlenderGIS scene georeferencing surface so future agents can work without reopening the repository source.

## Scene georeference state

BlenderGIS stores georeferencing state as custom ID properties on the Blender scene. The `GeoScene` wrapper accepts `GeoScene(scn=None)` and defaults to `bpy.context.scene`.

| Public concept | Exact scene key | Meaning | Validity notes |
| --- | --- | --- | --- |
| geographic origin longitude | `longitude` | origin longitude in WGS84 decimal degrees | setter requires `-180 <= value <= 180` |
| geographic origin latitude | `latitude` | origin latitude in WGS84 decimal degrees | setter requires `-90 <= value <= 90` |
| CRS / SRID | `SRID` | CRS definition string | can be an EPSG code, `AUTH:CODE`, `+init=...`, or a Proj4 string |
| projected origin X | `crs x` | scene origin X/easting in the current CRS | setter accepts numeric `int` or `float` |
| projected origin Y | `crs y` | scene origin Y/northing in the current CRS | setter accepts numeric `int` or `float` |
| map scale denominator | `scale` | map scale denominator `1:x` | defaults to `1` when unset; setter creates `_RNA_UI` metadata |
| basemap zoom | `zoom` | current tile-matrix zoom level | optional; set by basemap/map-viewer workflows |

The scene is considered usable for GIS imports when it has a valid CRS and projected origin:

- `GeoScene.hasCRS`: `SRID` exists.
- `GeoScene.hasValidCRS`: `SRS.validate(GeoScene.crs)` succeeds.
- `GeoScene.hasOriginPrj`: both `crs x` and `crs y` exist.
- `GeoScene.hasOriginGeo`: both `longitude` and `latitude` exist.
- `GeoScene.isGeoref`: valid CRS plus projected origin.
- `GeoScene.isFullyGeoref`: valid CRS plus projected origin plus geographic origin.
- `GeoScene.isPartiallyGeoref`: any CRS, projected origin, or geographic origin exists.
- `GeoScene.isBroken`: one of these invalid partial states exists:
  - `SRID` exists but is not a valid CRS.
  - origin exists but `SRID` is absent.
  - `SRID` and geographic origin exist but projected origin is missing.

## GeoScene methods and coordinate semantics

| Method/property | Inputs | Output/effect | Important behavior |
| --- | --- | --- | --- |
| `GeoScene.crs` | set with CRS string/code | validates via `SRS`; writes `SRID` | if an origin already exists, BlenderGIS attempts to reproject/synchronize it before setting the new CRS; failure raises and does not safely complete the switch |
| `GeoScene.setOriginPrj(x, y, synch=True)` | projected CRS coordinates | writes `crs x`, `crs y`; optionally writes `longitude`, `latitude` | if `synch=True` and CRS-to-WGS84 reprojection fails, existing geographic origin is deleted |
| `GeoScene.setOriginGeo(lon, lat)` | WGS84 lon/lat | writes `longitude`, `latitude` and tries to compute `crs x`, `crs y` | requires the CRS to already be set for projected synchronization; if reprojection fails, projected origin is deleted |
| `GeoScene.updOriginPrj(x, y, updObjLoc=True, synch=True)` | absolute projected origin | updates origin and optionally offsets top-level objects by the inverse delta | raises if projected origin is unset |
| `GeoScene.updOriginGeo(lon, lat, updObjLoc=True)` | absolute WGS84 origin | transforms to current CRS and updates projected origin | requires `isGeoref` |
| `GeoScene.moveOriginPrj(dx, dy, useScale=True, updObjLoc=True, synch=True)` | relative scene-space delta | moves projected origin; optionally moves top-level objects | with `useScale=True`, CRS delta is `dx * scale`, `dy * scale` |
| `GeoScene.moveOriginGeo(dx, dy, updObjLoc=True)` | lon/lat deltas | moves geographic origin and updates projected origin | requires existing geographic origin and valid georef |
| `GeoScene.view3dToProj(dx, dy)` | Blender XY location | `(x, y)` in CRS coordinates | uses `x = crsx + dx * scale`, `y = crsy + dy * scale`; requires projected origin |
| `GeoScene.projToView3d(dx, dy)` | projected CRS coordinates | Blender XY-like coordinates | implements the repository behavior `(dx * scale) - crsx`, `(dy * scale) - crsy`; verify against a scene before using for precision placement |

When possible, prefer projected origins for durable scene state. Geographic origin is a synchronized convenience state and may be missing in valid but not fully synchronized scenes.

## Operators and panels

These are the public Blender operator IDs for scene georeferencing:

| Operator ID | Label/description | Typical use | Success/cancel conditions |
| --- | --- | --- | --- |
| `geoscene.set_crs` | `Switch to` / `Switch scene crs` | choose a CRS from add-on preferences and write scene `SRID` | cancels if setting CRS cannot update the existing origin |
| `geoscene.init_org` | `Init origin` | create scene origin custom props at `x`, `y`; option `lonlat` treats values as WGS84 lon/lat | cancels if any origin already exists |
| `geoscene.edit_org_geo` | `Edit origin geo` | edit origin as longitude/latitude | cancels when `GeoScene.isBroken`; if no geographic origin exists, sets it |
| `geoscene.edit_org_prj` | `Edit origin proj` | edit origin in projected CRS coordinates | cancels when `GeoScene.isBroken`; if no projected origin exists, sets it |
| `geoscene.link_org_geo` | `Link geo` | compute `longitude`/`latitude` from `SRID` + `crs x`/`crs y` | requires projected origin and CRS; cancels if reprojection fails |
| `geoscene.link_org_prj` | `Link prj` | compute `crs x`/`crs y` from `longitude`/`latitude` + CRS | requires geographic origin and CRS; cancels if reprojection fails |
| `geoscene.clear_org` | `Clear origin` | remove `longitude`, `latitude`, `crs x`, `crs y` | does not remove `SRID` |
| `geoscene.clear_georef` | `Clear georef` | remove origin keys and `SRID` | use before rebuilding a broken scene from known coordinates |
| `geoscene.coords_viewer` | `Geo-coordinates` | modal View3D cursor coordinate readout | requires object mode, View3D area, `isGeoref`, and not broken |

The `GEOSCENE_PT_georef` panel appears in View3D sidebar category `View`, context `objectmode`, label `Geoscene`. Other BlenderGIS panels reuse `georefManagerLayout(self, context)` to display CRS/origin controls.

## CRS parsing with `SRS`

`SRS(crs)` accepts:

- A numeric EPSG code: `4326`, `"4326"` -> `EPSG:4326` internally with Proj4 `+init=epsg:4326`.
- An authority/code string: `EPSG:3857`, `epsg:32631`, `+init=epsg:4326`. Authority is normalized to uppercase unless the input is a Proj4 string.
- A Proj4 string where each non-empty token starts with `+`, for example `+proj=utm +zone=31 +datum=WGS84 +units=m +no_defs`.

Key properties and methods:

| API | Meaning |
| --- | --- |
| `SRS.validate(crs)` | returns `True` if `SRS(crs)` can be initialized, else logs and returns `False` |
| `str(SRS(crs))` | returns `AUTH:CODE` for SRID inputs, otherwise the Proj4 string |
| `SRS.SRID` | `AUTH:CODE` when available, else `None` |
| `SRS.isEPSG`, `isWGS84`, `isWM`, `isUTM`, `isGeo` | convenience CRS classifiers |
| `SRS.getOgrSpatialRef()` | GDAL/OSR spatial reference; requires GDAL Python bindings |
| `SRS.getPyProj()` | `pyproj.Proj`; requires pyproj |
| `SRS.loadProj4()` | parses a Proj4 string into a dict-like parameter map |
| `SRS.getWKT()` | uses GDAL when available; otherwise uses MapTiler/EPSG.io only for EPSG inputs |

Validation only checks whether the text matches BlenderGIS accepted forms and can be initialized by available libraries when required. It does not guarantee that a dataset's axis order or units match the task intent.

## Reprojection API

`reprojPt(crs1, crs2, x, y)` and `Reproj(crs1, crs2)` are the user-facing point transform APIs.

| API | Inputs | Output | Notes |
| --- | --- | --- | --- |
| `Reproj(crs1, crs2)` | accepted CRS definitions | object with selected `iproj` engine | initialization is relatively slow; reuse one instance for many points |
| `Reproj.pt(x, y)` | one coordinate pair | `(x, y)` in destination CRS | rejects `None` coordinates |
| `Reproj.pts([(x, y), ...])` | list of 2-tuples | list of transformed 2-tuples | rejects non-2D point tuples |
| `Reproj.bbox(bbox)` | `BBOX` or `(xmin, ymin, xmax, ymax)` | transformed extent bbox | transforms corners then takes min/max |
| `reprojPt(crs1, crs2, x, y)` | convenience wrapper | one transformed point | do not call repeatedly in tight loops because it constructs `Reproj` each time |
| `reprojPts(crs1, crs2, pts)` | convenience wrapper | transformed list | prefer for multiple points |
| `reprojBbox(crs1, crs2, bbox)` | convenience wrapper | transformed bbox | used by OSM/DEM/basemap workflows |

The exact exception class for projection failures is `ReprojError`; its string representation wraps the message with Python `repr`, so messages may appear quoted.

## Projection engine selection

The selected engine is `core.settings.proj_engine` and is controlled from add-on preferences `BGIS_PREFS.projEngine`. Valid values are:

| Engine | Availability | Capabilities | Risk/notes |
| --- | --- | --- | --- |
| `AUTO` | always listed | chooses best available engine at `Reproj` initialization | priority is GDAL, then pyproj, then built-in for limited WGS84/Web Mercator/UTM pairs, then EPSGIO/MapTiler |
| `GDAL` | listed only if `osgeo` imports | OSR coordinate transformations and raster reprojection support | strong general CRS support; optional dependency not installed in the minimum verified environment |
| `PYPROJ` | listed only if `pyproj` imports | local PROJ transforms | typical CPU install path when GDAL is absent; beware axis-order handling described below |
| `BUILTIN` | always listed | only WGS84 <-> Web Mercator and WGS84 <-> UTM EPSG zones | deterministic offline fallback; rejects unrelated CRS pairs |
| `EPSGIO` | always listed in preferences and settings availability | MapTiler Coordinates API for EPSG-to-EPSG transforms | requires network and a MapTiler API key via add-on preferences/settings; slow and unsuitable for many points |

`AUTO` details from source behavior:

1. If GDAL is importable, select `GDAL`.
2. Else if pyproj is importable, select `PYPROJ`.
3. Else if one CRS is WGS84 and the other is Web Mercator or UTM, select `BUILTIN`.
4. Else select `EPSGIO` / MapTiler Coordinates, which requires network and an API key.

If a user forces `GDAL` or `PYPROJ` when the dependency is missing, `Reproj` raises `ReprojError('Missing reproj engine')`. If a user forces `BUILTIN` for an unsupported CRS pair, it raises `ReprojError('Too limited built in reprojection capabilities')` or `ReprojError('Not implemented transformation')`.

## WGS84, Web Mercator, and UTM handling

- WGS84 is recognized as EPSG `4326`.
- Web Mercator is recognized as EPSG `3857`.
- UTM EPSG codes recognized by `SRS.isUTM` are `32601` through `32660` for the northern hemisphere and `32701` through `32760` for the southern hemisphere.
- `lonlat_to_epsg(longitude, latitude)` returns a UTM EPSG string based on longitude zone and hemisphere.
- `UTM.init_from_epsg(epsg)` validates the UTM code and stores `zone_number` and `northern`.
- Built-in UTM transforms validate latitude range `-80.0 <= latitude <= 84.0`, longitude range `-180.0 <= longitude <= 180.0`, easting range `100000 <= easting < 1000000`, and northing range `0 <= northing <= 10000000`.

Built-in Web Mercator uses the GRS80 equatorial perimeter and maps lon/lat as `(longitude, latitude)` to meters `(x, y)`.

## Predefined CRS preferences

Default add-on CRS presets are stored in `BGIS_PREFS.predefCrsJson` as a JSON list of `(value, label, tooltip)` tuples:

| Value | Label | Tooltip summary |
| --- | --- | --- |
| `EPSG:3857` | `Web Mercator` | worldwide projection, high distortion, not suitable for precision modelling |
| `EPSG:4326` | `WGS84 latlon` | longitude/latitude in degrees; source warns not to use as scene CRS for precision modelling |

CRS preference operators:

| Operator ID | Use |
| --- | --- |
| `bgis.add_predef_crs` | add CRS preset; optional MapTiler search requires API key |
| `bgis.edit_predef_crs` | edit current preset; validates with `SRS.validate` |
| `bgis.rmv_predef_crs` | remove current preset |
| `bgis.reset_predef_crs` | reset to the two defaults above |
| `bgis.pref_show` | open the add-on preferences UI |

`PredefCRS.getEnumItems()` returns the current predefined CRS entries for use in operator enum properties. `PredefCRS.getName(key)` maps a CRS value to its display name or returns `None`.

## Axis and order behavior

BlenderGIS' high-level convention is `(x, y)`:

- For WGS84 geographic data, `(x, y)` means `(longitude, latitude)`.
- For projected CRSs, `(x, y)` means easting/northing or projected X/Y.

Engine-specific internal handling:

- GDAL path: if PROJ major version is 6+ and the source CRS is geographic, BlenderGIS swaps each input point from `(lon, lat)` to `(lat, lon)` before `TransformPoints`. If the destination CRS is geographic, it reads returned values as `(lat, lon)` and swaps back to `(lon, lat)`.
- pyproj path: if the source CRS is geographic, BlenderGIS swaps input `pts` into lat-first values for `Transformer.transform`; if the destination CRS is geographic, it swaps the result back.
- Built-in path: uses explicit `(lon, lat)` for WGS84.

Practical rule: give BlenderGIS and the bundled helper `(longitude, latitude)` for EPSG:4326 even if an underlying library advertises lat/long axis metadata.

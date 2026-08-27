# BlenderGIS Georeferencing and CRS Troubleshooting

## Quick triage

1. Check scene state with `GeoScene`:

```python
from BlenderGIS.geoscene import GeoScene, SK

gs = GeoScene(bpy.context.scene)
print("keys", {k: bpy.context.scene.get(k) for k in [SK.CRS, SK.CRSX, SK.CRSY, SK.LON, SK.LAT, SK.SCALE, SK.ZOOM]})
print("valid", gs.hasValidCRS, "georef", gs.isGeoref, "full", gs.isFullyGeoref, "broken", gs.isBroken)
```

2. Check transform capability outside Blender with:

```bash
python sub-skills/georeferencing-and-crs/scripts/transform_point.py --src-crs EPSG:4326 --dst-crs EPSG:3857 --x 2 --y 48 --json
```

3. If a failure belongs to raster/world-file metadata, vector import geometry, or georeferenced camera output, route to that owning sub-skill after the CRS/origin gate is resolved here.

## Invalid CRS

Symptoms:

- Geoscene panel shows CRS with an error state.
- `GeoScene.hasCRS` is true but `GeoScene.hasValidCRS` is false.
- `GeoScene.isBroken` is true.
- `geoscene.set_crs`, `geoscene.link_org_geo`, or `geoscene.link_org_prj` reports a generic reprojection/log error.
- `SRS.validate(crs)` returns false.

Accepted CRS forms:

- `4326` or `"4326"`.
- `EPSG:4326` / other `AUTH:CODE` with an integer code.
- `+init=epsg:4326`.
- Proj4 strings where each non-empty token begins with `+`.

Common mistakes and fixes:

| Mistake | Why it fails | Fix |
| --- | --- | --- |
| `EPSG 4326` | missing colon | use `EPSG:4326` |
| `EPSG:WGS84` | code is not numeric | use `EPSG:4326` or a valid Proj4 string |
| WKT text pasted as CRS | `SRS` does not accept raw WKT input | convert to EPSG/Auth code or Proj4 before setting |
| Empty string or `None` | not a CRS | clear georef or provide a valid CRS |
| Forcing `BUILTIN` with arbitrary projected CRSs | built-in transforms are intentionally limited | use `AUTO`, `PYPROJ`, `GDAL`, or a supported WGS84/WebMercator/UTM pair |

Recovery sequence when an invalid `SRID` exists:

1. Preserve useful origin values externally:

```python
from BlenderGIS.geoscene import SK
scn = bpy.context.scene
saved = {k: scn.get(k) for k in [SK.CRSX, SK.CRSY, SK.LON, SK.LAT, SK.SCALE, SK.ZOOM]}
```

2. If the origin is known trustworthy, remove only the bad CRS or use `geoscene.clear_georef` if the full state is unreliable.
3. Set a valid CRS with `GeoScene.crs = "EPSG:xxxx"` or `geoscene.set_crs`.
4. Reapply projected or geographic origin and link the missing counterpart if needed.
5. Verify `not GeoScene(scene).isBroken`.

## Broken partial georef state

`GeoScene.isBroken` is true in exactly these source-defined cases:

1. `SRID` exists but is invalid.
2. `SRID` is missing while projected or geographic origin exists.
3. `SRID` exists and geographic origin exists, but projected origin is missing.

The scene may also be merely incomplete without being broken: for example, a valid `SRID` with no origin is not georeferenced yet but is not necessarily broken.

Recovery patterns:

| State | Likely cause | Safe recovery |
| --- | --- | --- |
| `crs x`/`crs y` exist, `SRID` missing | origin was initialized before CRS or CRS key was deleted | identify the CRS from project/data evidence, set `GeoScene.crs`, then call `setOriginPrj(existing_x, existing_y, synch=True)` or UI `geoscene.link_org_geo` |
| `longitude`/`latitude` exist, `SRID` missing | origin was created as lon/lat before CRS or CRS key was deleted | identify intended projected scene CRS, set it, then call `setOriginGeo(existing_lon, existing_lat)` or UI `geoscene.link_org_prj` |
| `SRID` and lon/lat exist, projected origin missing | synchronization failed or projected keys were deleted | ensure reprojection engine works, then run `geoscene.link_org_prj` |
| invalid `SRID` plus origin values | mistyped CRS or stale preset | preserve origin values, clear/fix CRS, then reapply origin using the right coordinate domain |
| mixed origin values disagree | old synchronization failure or manual property edit | choose one trusted domain; delete and recompute the other with `link_org_geo` or `link_org_prj` |

Avoid blind fixes:

- Do not infer CRS from numeric magnitude alone unless task evidence supports it.
- Do not assume `EPSG:4326` is the scene CRS just because `longitude`/`latitude` exist.
- Do not clear origin before saving the values if the user may need them.

## Missing reprojection engine

Symptoms:

- `ReprojError('Missing reproj engine')`.
- Preference `Projection engine` is forced to `GDAL` but `osgeo` is not importable.
- Preference is forced to `PYPROJ` but `pyproj` is not importable.
- `SRS.getOgrSpatialRef()` raises `ImportError('GDAL not available')`.
- `SRS.getPyProj()` raises `ImportError('PYPROJ not available')`.

Fixes:

1. Prefer add-on preference `Projection engine = Auto detect`.
2. If GDAL is absent but pyproj exists, `AUTO` should select `PYPROJ`; this is expected and supports general local point transforms.
3. If both GDAL and pyproj are absent:
   - WGS84 <-> Web Mercator and WGS84 <-> UTM can still use `BUILTIN`.
   - Other EPSG-to-EPSG transforms need a local dependency or network/API-key fallback.
4. If a user forced `BUILTIN` and gets `Too limited built in reprojection capabilities`, switch to `AUTO`, `PYPROJ`, or `GDAL`.
5. If installing dependencies is outside the current task, document the limitation and avoid running operators that require the missing transform.

Engine priority in `AUTO` is GDAL first, pyproj second, built-in for limited WGS84/WebMercator/UTM pairs, then EPSGIO/MapTiler.

## EPSG.io / MapTiler network fallback risk

BlenderGIS source keeps the historical `EPSGIO` engine name but implements it with MapTiler Coordinates API. It is not a free offline EPSG.io lookup.

Risks:

- Requires `settings.maptiler_api_key`, normally set from add-on preferences `maptiler_api_key`.
- Requires network access to `https://api.maptiler.com`.
- Constructor pings the service with a short timeout.
- Point transforms use API requests and can be slow; batch transforms are limited by API behavior.
- Only EPSG-to-EPSG transforms are supported by the fallback; Proj4 strings are rejected.
- Logs or debug output may include request URLs; avoid exposing API keys.

Recommended use:

- Use local `GDAL` or `PYPROJ` for normal work.
- Use `BUILTIN` for simple WGS84/Web Mercator/UTM checks when local dependencies are missing.
- Use `EPSGIO` / MapTiler only after confirming network and credential approval.
- Do not use EPSGIO in loops; transform many points locally or batch carefully.

## pyproj and GDAL optional dependency differences

| Topic | GDAL path | pyproj path | Built-in path |
| --- | --- | --- | --- |
| Availability | needs `osgeo.gdal`/`osgeo.osr` | needs `pyproj` | always source-defined |
| `AUTO` priority | chosen before pyproj if importable | chosen when GDAL absent and pyproj importable | chosen only for limited supported pairs when no local full engine exists |
| CRS object | `SRS.getOgrSpatialRef()` | `SRS.getPyProj()` | EPSG code classifiers only |
| Raster reprojection | `reprojImg` requires GDAL | not used for raster reprojection | not applicable |
| Axis handling | source includes PROJ 6 geographic source swap and geographic destination swap | source swaps geographic input/result around `Transformer.transform` | explicit lon/lat functions |
| Failure class | generally wrapped in `ReprojError` for init; GDAL APIs may raise lower-level errors in raster paths | generally wrapped in `ReprojError` for init | `ReprojError` or UTM range errors |

When pyproj exists but GDAL does not:

- `AUTO` selecting `PYPROJ` is correct.
- Do not treat missing GDAL as a blocker for scene CRS or point transform workflows.
- Do treat missing GDAL as relevant for raster reprojection/GeoTIFF workflows; route those details to `raster-dem-and-basemaps`.

## Axis/order gotchas

BlenderGIS expects `(x, y)` order at the public API boundary.

- For WGS84, pass `(longitude, latitude)`, not `(latitude, longitude)`.
- For projected CRSs, pass `(easting, northing)` or projected `(x, y)`.
- Do not copy axis-order examples directly from external PROJ/GDAL docs without adapting to BlenderGIS' wrapper behavior.
- For `EPSG:4326 -> EPSG:3857`, input `(2, 48)` should produce approximately `(222638.98, 6106854.83)`; if you get a result for latitude `2` and longitude `48`, the inputs were swapped.
- GeoScene property names also reflect the convention: `longitude`, `latitude`, `crs x`, `crs y`.

Validation command:

```bash
python sub-skills/georeferencing-and-crs/scripts/transform_point.py --src-crs EPSG:4326 --dst-crs EPSG:3857 --x 2 --y 48 --json
```

If the X output is near `5,343,335` instead of `222,639`, latitude/longitude were likely swapped by the calling code.

## WGS84 as scene CRS warning

BlenderGIS ships `EPSG:4326` as a default predefined CRS but its source tooltip warns: WGS84 longitude/latitude is not suitable as a precision scene CRS because units are degrees. Use it for reprojection inputs/outputs and metadata checks. For modelling or GIS placement, choose a projected CRS such as a UTM zone or Web Mercator depending on task accuracy requirements.

## Coordinate update moved objects unexpectedly

`GeoScene.updOriginPrj`, `updOriginGeo`, `moveOriginPrj`, and `moveOriginGeo` can move top-level objects to retain geolocation. UI setter behavior uses preference `lockObj` as `updObjLoc`. If objects shifted unexpectedly:

1. Check whether object-lock preference was enabled.
2. Confirm whether the operation was an origin move/update rather than first-time initialization.
3. Restore from backup if needed, then repeat with `updObjLoc=False` in Python if you intend to change origin metadata without moving objects.

## CRS switch fails on an existing scene

Changing `GeoScene.crs` attempts to preserve existing origin coordinates:

- If geographic origin exists, BlenderGIS tries `reprojPt(4326, new_crs, lon, lat)`.
- Else if projected origin and a valid old CRS exist, it tries `reprojPt(old_crs, new_crs, crsx, crsy)`.
- If old CRS is invalid, it raises `Scene origin coordinates cannot be updated because current CRS is invalid.`

Fix:

1. Repair invalid old CRS first, or preserve origin values and clear/rebuild georef.
2. Ensure an engine supports the old-to-new transform.
3. Retry with `AUTO` or a local engine.

## Operator reports are generic

Several operators report short messages such as `Cannot update crs. Check logs form more info`, `Cannot compute lat/lon`, `Cannot compute crs coordinates`, or `No enough infos`. Treat these as pointers to inspect state and engine availability:

- `No enough infos`: required CRS or origin counterpart is missing.
- `Cannot compute lat/lon`: projected origin + CRS could not transform to WGS84.
- `Cannot compute crs coordinates`: lon/lat + CRS could not transform to projected coordinates.
- `Scene georef is broken`: repair partial keys before editing origin.

## Helper script errors

The bundled `scripts/transform_point.py` emits safe non-traceback errors by default and JSON errors with `--json`.

Examples:

```bash
python sub-skills/georeferencing-and-crs/scripts/transform_point.py --src-crs EPSG:BAD --dst-crs EPSG:3857 --x 2 --y 48 --json
```

Expected error shape:

```json
{"ok": false, "error": "invalid_crs", "message": "..."}
```

If the helper reports `missing_engine`, install/enable pyproj for general transforms or use a WGS84/WebMercator/UTM pair supported by the built-in fallback. The helper intentionally does not call MapTiler/EPSGIO over the network by default.
